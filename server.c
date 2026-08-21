/*
 * metro_server.c — Metro telemetry & control server
 *
 * Build:  gcc -pthread -Wall -Wextra -o metro_server metro_server.c
 * Run:    ./metro_server <port> <logfile>
 *
 * Platform: POSIX / Linux only (pthreads, BSD sockets, POSIX sleep()).
 *           The old Windows #ifdef block was removed: it could never compile
 *           on MSVC (it included <unistd.h>/<pthread.h> unconditionally and
 *           never called WSAStartup), so it only advertised a portability the
 *           code did not have. See the notes accompanying this file if you
 *           actually need a Windows port.
 *
 * ---------------------------------------------------------------------------
 * Wire protocol (line-based, one message per '\n'-terminated line):
 *
 *   Client -> Server
 *     ROLE|observer                 declare passive observer role
 *     ROLE|admin                    declare admin role (still needs AUTH)
 *     AUTH|user=<u>;pass=<p>         authenticate as admin
 *     COMMAND|<CMD>                  run a control command (admin only)
 *     LISTUSERS                      list connected clients (admin only)
 *
 *   Commands (<CMD>):
 *     SPEEDUP    +5 km/h (max 120), only while moving
 *     SLOWDOWN   -5 km/h (min 0)
 *     STOPNOW    force speed 0 and mark stopped
 *     STARTNOW   resume from a stop at 20 km/h
 *
 *   Server -> Client
 *     RESPONSE|OK
 *     RESPONSE|ROLE_OK
 *     RESPONSE|USERS;<id>,<id>,...
 *     RESPONSE|ERROR;reason=<why>
 *     TELEMETRY|speed=<f>;battery=<d>;station=<d>;direction=<FWD|REV>
 *                                   pushed to every client on connect and on
 *                                   each simulation event
 *
 * NOTE on the simulation: for simplicity the train is modelled as reaching a
 * station on every tick (there is no "travelling between stations" phase).
 * That matches the original demo behaviour; if your assignment needs real
 * travel time, that logic lives in metro_thread() and is the thing to change.
 * ---------------------------------------------------------------------------
 */

#define _POSIX_C_SOURCE 200112L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <stdarg.h>
#include <stdint.h>
#include <signal.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>

#include <pthread.h>

#define MAXLINE      1024   /* size of a single protocol message buffer      */
#define CLIENT_BUFSZ 4096   /* per-connection accumulator for line framing   */
#define MAXCLIENTS   100    /* hard cap on simultaneous connections          */
#define ADMIN_USER   "admin"
#define ADMIN_PASS   "adminpass"

/* -------------------------------------------------------------------------- */
/* Shared state                                                               */
/* -------------------------------------------------------------------------- */

typedef enum { FWD, REV } direction_t;

typedef struct {
    double      speed;                  /* km/h                               */
    int         battery;                /* %                                  */
    int         station;                /* station index                      */
    direction_t dir;
    int         stations_since_reverse;
    int         stopped;                /* 1 if stopped                       */
    pthread_mutex_t lock;
} metro_state_t;

static metro_state_t metro;

typedef struct client {
    int                sockfd;
    struct sockaddr_in addr;
    char               role[16];        /* "observer" or "admin"              */
    int                authenticated;   /* 1 once admin AUTH succeeds          */
    char               id[64];          /* "ip:port"                          */
    struct client     *next;
} client_t;

static client_t       *clients_head = NULL;
static int             client_count = 0;
static pthread_mutex_t clients_lock = PTHREAD_MUTEX_INITIALIZER;

static FILE           *logfile = NULL;
static pthread_mutex_t log_lock = PTHREAD_MUTEX_INITIALIZER;

/*
 * Lock ordering: metro.lock and clients_lock are never held at the same time,
 * and log_lock is a leaf (nothing else is acquired while it is held). This
 * keeps the design deadlock-free.
 */

/* -------------------------------------------------------------------------- */
/* Logging                                                                    */
/* -------------------------------------------------------------------------- */

/* Timestamped log to stdout + logfile. Safe to call from any thread. */
static void log_msg(const char *fmt, ...) {
    va_list ap;
    char    buf[1024];
    char    tbuf[64];
    time_t  now = time(NULL);
    struct tm tm;

    localtime_r(&now, &tm);             /* thread-safe, unlike localtime()    */
    snprintf(tbuf, sizeof(tbuf), "%04d-%02d-%02d %02d:%02d:%02d",
             tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
             tm.tm_hour, tm.tm_min, tm.tm_sec);

    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    pthread_mutex_lock(&log_lock);
    printf("[%s] %s\n", tbuf, buf);
    if (logfile) {
        fprintf(logfile, "[%s] %s\n", tbuf, buf);
        fflush(logfile);
    }
    pthread_mutex_unlock(&log_lock);
}

/* -------------------------------------------------------------------------- */
/* Low-level send helpers                                                     */
/* -------------------------------------------------------------------------- */

/* Send the whole string, retrying on short writes / EINTR. MSG_NOSIGNAL keeps
 * a dead peer from raising SIGPIPE and killing the process. Returns bytes
 * sent, or -1 on error. */
static ssize_t send_all(int fd, const char *s, int extra_flags) {
    size_t len = strlen(s);
    size_t off = 0;
    while (off < len) {
        ssize_t k = send(fd, s + off, len - off, MSG_NOSIGNAL | extra_flags);
        if (k < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        off += (size_t)k;
    }
    return (ssize_t)off;
}

/* Blocking send of one line to a specific client (used for direct replies). */
static ssize_t send_line(client_t *c, const char *s) {
    return send_all(c->sockfd, s, 0);
}

/* -------------------------------------------------------------------------- */
/* Client registry                                                            */
/* -------------------------------------------------------------------------- */

/* Insert client, enforcing MAXCLIENTS. Returns 0 on success, -1 if full. */
static int add_client(client_t *c) {
    pthread_mutex_lock(&clients_lock);
    if (client_count >= MAXCLIENTS) {
        pthread_mutex_unlock(&clients_lock);
        return -1;
    }
    c->next = clients_head;
    clients_head = c;
    client_count++;
    pthread_mutex_unlock(&clients_lock);
    return 0;
}

static void remove_client(client_t *c) {
    pthread_mutex_lock(&clients_lock);
    client_t **p = &clients_head;
    while (*p) {
        if (*p == c) {
            *p = c->next;
            client_count--;
            break;
        }
        p = &((*p)->next);
    }
    pthread_mutex_unlock(&clients_lock);
}

/* -------------------------------------------------------------------------- */
/* Telemetry                                                                  */
/* -------------------------------------------------------------------------- */

/* Format the current telemetry line (takes metro.lock internally). */
static void build_telemetry_msg(char *out, size_t n) {
    pthread_mutex_lock(&metro.lock);
    const char *dirstr = (metro.dir == FWD) ? "FWD" : "REV";
    snprintf(out, n,
             "TELEMETRY|speed=%.1f;battery=%d;station=%d;direction=%s\n",
             metro.speed, metro.battery, metro.station, dirstr);
    pthread_mutex_unlock(&metro.lock);
}

/* Push current telemetry to a single client. */
static void send_telemetry_to(client_t *c) {
    char msg[MAXLINE];
    build_telemetry_msg(msg, sizeof(msg));
    send_line(c, msg);
}

/* Push current telemetry to every connected client. A slow client only loses
 * a frame (non-blocking send); a dead one is shut down so its owning thread
 * wakes up and cleans it up. Broadcast never frees clients itself. */
static void broadcast_telemetry(void) {
    char msg[MAXLINE];
    build_telemetry_msg(msg, sizeof(msg));

    pthread_mutex_lock(&clients_lock);
    for (client_t *it = clients_head; it; it = it->next) {
        ssize_t k = send(it->sockfd, msg, strlen(msg),
                         MSG_NOSIGNAL | MSG_DONTWAIT);
        if (k < 0 && errno != EAGAIN && errno != EWOULDBLOCK) {
            log_msg("Send to %s failed (%s); dropping connection",
                    it->id, strerror(errno));
            shutdown(it->sockfd, SHUT_RDWR);   /* unblocks the owning thread  */
        }
    }
    pthread_mutex_unlock(&clients_lock);

    /* msg has a trailing '\n'; strip it for a tidy log line. */
    msg[strcspn(msg, "\n")] = '\0';
    log_msg("Telemetry broadcast: %s", msg);
}

/* -------------------------------------------------------------------------- */
/* Command handling                                                           */
/* -------------------------------------------------------------------------- */

static int has_prefix(const char *s, const char *p) {
    return strncmp(s, p, strlen(p)) == 0;
}

/* Apply an admin command. All I/O (reply + log) happens outside metro.lock so
 * a disk write can't stall the simulation or other commands. */
static void handle_command_from_admin(const char *cmd, client_t *c) {
    char response[MAXLINE];
    char logline[256];
    logline[0] = '\0';

    pthread_mutex_lock(&metro.lock);

    /* Safety interlock: below 5% battery, only STARTNOW is allowed. */
    if (metro.battery < 5 && strcmp(cmd, "STARTNOW") != 0) {
        int bat = metro.battery;
        pthread_mutex_unlock(&metro.lock);
        send_line(c, "RESPONSE|ERROR;reason=battery_too_low\n");
        log_msg("Command %s denied for %s: battery too low (%d%%)",
                cmd, c->id, bat);
        return;
    }

    if (strcmp(cmd, "SPEEDUP") == 0) {
        if (metro.stopped) {
            snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=stopped\n");
        } else {
            metro.speed += 5.0;
            if (metro.speed > 120.0) metro.speed = 120.0;
            snprintf(response, sizeof(response), "RESPONSE|OK\n");
            snprintf(logline, sizeof(logline), "SPEEDUP -> %.1f km/h", metro.speed);
        }
    } else if (strcmp(cmd, "SLOWDOWN") == 0) {
        metro.speed -= 5.0;
        if (metro.speed < 0.0) metro.speed = 0.0;
        snprintf(response, sizeof(response), "RESPONSE|OK\n");
        snprintf(logline, sizeof(logline), "SLOWDOWN -> %.1f km/h", metro.speed);
    } else if (strcmp(cmd, "STOPNOW") == 0) {
        metro.speed = 0.0;
        metro.stopped = 1;
        snprintf(response, sizeof(response), "RESPONSE|OK\n");
        snprintf(logline, sizeof(logline), "STOPNOW");
    } else if (strcmp(cmd, "STARTNOW") == 0) {
        if (metro.stopped) {
            metro.stopped = 0;
            metro.speed = 20.0;             /* resume at baseline speed        */
            snprintf(response, sizeof(response), "RESPONSE|OK\n");
            snprintf(logline, sizeof(logline), "STARTNOW -> %.1f km/h", metro.speed);
        } else {
            snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=not_stopped\n");
        }
    } else {
        snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=unknown_command\n");
    }

    pthread_mutex_unlock(&metro.lock);

    send_line(c, response);
    if (logline[0]) log_msg("[%s] %s", c->id, logline);
}

/* Send the list of connected client ids to an admin. */
static void send_listusers(client_t *c) {
    char buf[MAXLINE];

    pthread_mutex_lock(&clients_lock);
    snprintf(buf, sizeof(buf), "RESPONSE|USERS;");
    for (client_t *it = clients_head; it; it = it->next) {
        char tmp[128];
        snprintf(tmp, sizeof(tmp), "%s,", it->id);
        strncat(buf, tmp, sizeof(buf) - strlen(buf) - 1);
    }
    pthread_mutex_unlock(&clients_lock);

    strncat(buf, "\n", sizeof(buf) - strlen(buf) - 1);
    send_line(c, buf);
    log_msg("LISTUSERS requested by %s", c->id);
}

/* -------------------------------------------------------------------------- */
/* Per-connection protocol handling                                           */
/* -------------------------------------------------------------------------- */

/* Handle exactly one complete protocol line (no trailing newline). */
static void process_line(client_t *c, char *line) {
    if (line[0] == '\0') return;    /* ignore blank lines                     */

    /* Never write credentials to the log. */
    if (has_prefix(line, "AUTH|"))
        log_msg("Received from %s: AUTH|<redacted>", c->id);
    else
        log_msg("Received from %s: %s", c->id, line);

    if (has_prefix(line, "ROLE|")) {
        const char *role = line + 5;
        if (strcmp(role, "admin") == 0)
            snprintf(c->role, sizeof(c->role), "admin");
        else
            snprintf(c->role, sizeof(c->role), "observer");
        c->authenticated = 0;
        send_line(c, "RESPONSE|ROLE_OK\n");

    } else if (has_prefix(line, "AUTH|")) {
        char  user[64] = {0}, pass[64] = {0};
        char *kv = line + 5;
        char *u  = strstr(kv, "user=");
        char *pw = strstr(kv, "pass=");

        if (u) {
            u += 5;
            char *semi = strchr(u, ';');
            if (semi) {
                *semi = '\0';
                strncpy(user, u, sizeof(user) - 1);
                *semi = ';';
            } else {
                strncpy(user, u, sizeof(user) - 1);
            }
        }
        if (pw) {
            pw += 5;
            strncpy(pass, pw, sizeof(pass) - 1);
        }

        if (strcmp(user, ADMIN_USER) == 0 && strcmp(pass, ADMIN_PASS) == 0) {
            c->authenticated = 1;
            snprintf(c->role, sizeof(c->role), "admin");
            send_line(c, "RESPONSE|OK\n");
            log_msg("Admin authenticated: %s (%s)", user, c->id);
        } else {
            c->authenticated = 0;
            send_line(c, "RESPONSE|ERROR;reason=auth_failed\n");
            log_msg("Authentication failed from %s (user=%s)", c->id, user);
        }

    } else if (has_prefix(line, "COMMAND|")) {
        if (strcmp(c->role, "admin") != 0 || !c->authenticated) {
            send_line(c, "RESPONSE|ERROR;reason=not_authorized\n");
            log_msg("Command rejected (not authorized): %s", c->id);
        } else {
            handle_command_from_admin(line + 8, c);
        }

    } else if (strcmp(line, "LISTUSERS") == 0) {
        if (strcmp(c->role, "admin") != 0 || !c->authenticated)
            send_line(c, "RESPONSE|ERROR;reason=not_authorized\n");
        else
            send_listusers(c);

    } else {
        send_line(c, "RESPONSE|ERROR;reason=invalid_message\n");
    }
}

/* One thread per client: reads bytes, reassembles complete '\n'-delimited
 * lines (handles several messages per recv and messages split across recvs),
 * and dispatches each to process_line. */
static void *client_thread(void *arg) {
    client_t *c = (client_t *)arg;

    if (add_client(c) < 0) {
        log_msg("Rejected %s: server full (%d clients)", c->id, MAXCLIENTS);
        send_line(c, "RESPONSE|ERROR;reason=server_full\n");
        close(c->sockfd);
        free(c);
        return NULL;
    }

    log_msg("New client connected: %s", c->id);
    send_telemetry_to(c);   /* give a fresh client the current state at once  */

    char    acc[CLIENT_BUFSZ];
    size_t  acc_len = 0;
    char    rbuf[MAXLINE];
    ssize_t n;

    while ((n = recv(c->sockfd, rbuf, sizeof(rbuf), 0)) > 0) {
        for (ssize_t i = 0; i < n; i++) {
            char ch = rbuf[i];
            if (ch == '\r') continue;               /* tolerate CRLF          */
            if (ch == '\n') {
                acc[acc_len] = '\0';
                process_line(c, acc);
                acc_len = 0;
            } else if (acc_len < sizeof(acc) - 1) {
                acc[acc_len++] = ch;
            } else {
                /* Line longer than the buffer: drop it and tell the client. */
                acc_len = 0;
                send_line(c, "RESPONSE|ERROR;reason=line_too_long\n");
            }
        }
    }

    if (n == 0)
        log_msg("Client disconnected: %s", c->id);
    else if (n < 0)
        log_msg("Recv error from %s: %s", c->id, strerror(errno));

    close(c->sockfd);
    remove_client(c);
    free(c);
    return NULL;
}

/* -------------------------------------------------------------------------- */
/* Metro simulation                                                           */
/* -------------------------------------------------------------------------- */

static void *metro_thread(void *arg) {
    (void)arg;
    for (;;) {
        sleep(10);                          /* inter-tick delay               */

        /* Advance one tick. (Simplified model: a station is reached every
         * tick — see the note at the top of the file.) */
        pthread_mutex_lock(&metro.lock);
        if (!metro.stopped) {
            metro.station += 1;
            metro.battery -= 1;
            if (metro.battery < 0) metro.battery = 0;
        }
        int station_now = metro.station;
        pthread_mutex_unlock(&metro.lock);

        /* Announce arrival. */
        broadcast_telemetry();

        /* Dwell at the station. */
        pthread_mutex_lock(&metro.lock);
        metro.stopped = 1;
        metro.speed = 0.0;
        pthread_mutex_unlock(&metro.lock);

        log_msg("Arrived at station %d. Dwelling 20s.", station_now);
        sleep(20);

        /* Depart; reverse direction every 5 stations. */
        pthread_mutex_lock(&metro.lock);
        metro.stopped = 0;
        metro.speed = 30.0;                 /* resume baseline                */
        metro.stations_since_reverse += 1;
        int reversed = 0;
        if (metro.stations_since_reverse >= 5) {
            metro.dir = (metro.dir == FWD) ? REV : FWD;
            metro.stations_since_reverse = 0;
            reversed = 1;
        }
        const char *dnow = (metro.dir == FWD) ? "FWD" : "REV";
        pthread_mutex_unlock(&metro.lock);

        if (reversed) log_msg("Direction reversed -> %s", dnow);

        /* Announce departure. */
        broadcast_telemetry();
    }
    return NULL;
}

/* -------------------------------------------------------------------------- */
/* main                                                                       */
/* -------------------------------------------------------------------------- */

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <port> <logfile>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    /* Validate the port instead of trusting atoi(). */
    char *end = NULL;
    long  port = strtol(argv[1], &end, 10);
    if (*end != '\0' || port < 1 || port > 65535) {
        fprintf(stderr, "Invalid port: %s (expected 1-65535)\n", argv[1]);
        exit(EXIT_FAILURE);
    }
    const char *logsfile_path = argv[2];

    logfile = fopen(logsfile_path, "a");
    if (!logfile) {
        perror("fopen logfile");
        exit(EXIT_FAILURE);
    }

    /* A client vanishing mid-send must not kill us with SIGPIPE. */
    signal(SIGPIPE, SIG_IGN);

    /* Initialize metro state before any thread can read it. */
    pthread_mutex_init(&metro.lock, NULL);
    metro.speed                  = 20.0;
    metro.battery                = 100;
    metro.station                = 0;
    metro.dir                    = FWD;
    metro.stations_since_reverse = 0;
    metro.stopped                = 0;

    int listenfd = socket(AF_INET, SOCK_STREAM, 0);
    if (listenfd < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    int opt = 1;
    setsockopt(listenfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in servaddr;
    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family      = AF_INET;
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port        = htons((uint16_t)port);

    if (bind(listenfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("bind");
        exit(EXIT_FAILURE);
    }
    if (listen(listenfd, 10) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    log_msg("Server started on port %ld. Logs: %s", port, logsfile_path);

    pthread_t metro_tid;
    if (pthread_create(&metro_tid, NULL, metro_thread, NULL) != 0) {
        perror("pthread_create metro");
        exit(EXIT_FAILURE);
    }

    for (;;) {
        struct sockaddr_in cliaddr;
        socklen_t          clilen = sizeof(cliaddr);
        int connfd = accept(listenfd, (struct sockaddr *)&cliaddr, &clilen);
        if (connfd < 0) {
            log_msg("Accept error: %s", strerror(errno));
            continue;
        }

        client_t *c = calloc(1, sizeof(client_t));
        if (!c) {
            log_msg("Out of memory; dropping connection");
            close(connfd);
            continue;
        }
        c->sockfd        = connfd;
        c->addr          = cliaddr;
        c->authenticated = 0;
        snprintf(c->role, sizeof(c->role), "observer");

        char ipstr[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &(cliaddr.sin_addr), ipstr, sizeof(ipstr));
        snprintf(c->id, sizeof(c->id), "%s:%d", ipstr, ntohs(cliaddr.sin_port));

        pthread_t tid;
        if (pthread_create(&tid, NULL, client_thread, c) != 0) {
            log_msg("Error creating client thread");
            close(connfd);
            free(c);
        } else {
            pthread_detach(tid);
        }
    }

    /* Not reached (the accept loop runs forever); kept for clarity. */
    fclose(logfile);
    close(listenfd);
    return 0;
}
