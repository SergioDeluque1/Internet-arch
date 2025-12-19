#define _POSIX_C_SOURCE 200112L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <stdarg.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>

#include <pthread.h>

#define MAXLINE 1024
#define MAXCLIENTS 100
#define ADMIN_USER "admin"
#define ADMIN_PASS "adminpass"

typedef enum { FWD, REV } direction_t;

typedef struct {
    double speed;
    int battery;
    int station;
    direction_t dir;
    int stations_since_reverse;
    int stopped;
    pthread_mutex_t lock;
} metro_state_t;

metro_state_t metro;

typedef struct client {
    int sockfd;
    struct sockaddr_in addr;
    char role[16];
    int authenticated;
    char id[64];
    struct client *next;
} client_t;

client_t *clients_head = NULL;
pthread_mutex_t clients_lock = PTHREAD_MUTEX_INITIALIZER;
FILE *logfile = NULL;
pthread_mutex_t log_lock = PTHREAD_MUTEX_INITIALIZER;

void log_msg(const char *fmt, ...) {
    va_list ap;
    char buf[1024];
    time_t now = time(NULL);
    struct tm tm = *localtime(&now);
    char tbuf[64];
    snprintf(tbuf, sizeof(tbuf), "%04d-%02d-%02d %02d:%02d:%02d",
             tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday,
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

void add_client(client_t *c) {
    pthread_mutex_lock(&clients_lock);
    c->next = clients_head;
    clients_head = c;
    pthread_mutex_unlock(&clients_lock);
}

void remove_client(client_t *c) {
    pthread_mutex_lock(&clients_lock);
    client_t **p = &clients_head;
    while (*p) {
        if (*p == c) {
            *p = c->next;
            break;
        }
        p = &((*p)->next);
    }
    pthread_mutex_unlock(&clients_lock);
}

void broadcast_telemetry() {
    char msg[MAXLINE];
    pthread_mutex_lock(&metro.lock);
    const char *dirstr = (metro.dir == FWD) ? "FWD" : "REV";
    snprintf(msg, sizeof(msg),
             "TELEMETRY|speed=%.1f;battery=%d;station=%d;direction=%s\n",
             metro.speed, metro.battery, metro.station, dirstr);
    pthread_mutex_unlock(&metro.lock);

    pthread_mutex_lock(&clients_lock);
    client_t *it = clients_head;
    while (it) {
        ssize_t n = send(it->sockfd, msg, strlen(msg), 0);
        if (n <= 0) {
            log_msg("Error sending telemetry to %s: %s", it->id, strerror(errno));
        }
        it = it->next;
    }
    pthread_mutex_unlock(&clients_lock);
    log_msg("Telemetry broadcast: %s", msg);
}

int has_prefix(const char *s, const char *p) {
    return strncmp(s, p, strlen(p)) == 0;
}

void handle_command_from_admin(const char *cmd, client_t *c) {
    char response[MAXLINE];

    pthread_mutex_lock(&metro.lock);
    if (metro.battery < 5 && strcmp(cmd, "STARTNOW") != 0) {
        snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=battery_too_low\n");
        send(c->sockfd, response, strlen(response), 0);
        pthread_mutex_unlock(&metro.lock);
        log_msg("Command %s denied for %s: battery low (%d%%)", cmd, c->id, metro.battery);
        return;
    }

    if (strcmp(cmd, "SPEEDUP") == 0) {
        if (metro.stopped) {
            snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=stopped\n");
        } else {
            metro.speed += 5.0;
            if (metro.speed > 120.0) metro.speed = 120.0;
            snprintf(response, sizeof(response), "RESPONSE|OK\n");
            log_msg("SPEEDUP executed. New speed: %.1f", metro.speed);
        }
    } else if (strcmp(cmd, "SLOWDOWN") == 0) {
        metro.speed -= 5.0;
        if (metro.speed < 0.0) metro.speed = 0.0;
        snprintf(response, sizeof(response), "RESPONSE|OK\n");
        log_msg("SLOWDOWN executed. New speed: %.1f", metro.speed);
    } else if (strcmp(cmd, "STOPNOW") == 0) {
        metro.speed = 0.0;
        metro.stopped = 1;
        snprintf(response, sizeof(response), "RESPONSE|OK\n");
        log_msg("STOPNOW executed.");
    } else if (strcmp(cmd, "STARTNOW") == 0) {
        if (metro.stopped) {
            metro.stopped = 0;
            metro.speed = 20.0;
            snprintf(response, sizeof(response), "RESPONSE|OK\n");
            log_msg("STARTNOW executed. Speed: %.1f", metro.speed);
        } else {
            snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=not_stopped\n");
        }
    } else {
        snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=unknown_command\n");
    }
    pthread_mutex_unlock(&metro.lock);
    send(c->sockfd, response, strlen(response), 0);
}

void send_listusers(client_t *c) {
    char buf[MAXLINE];
    pthread_mutex_lock(&clients_lock);
    client_t *it = clients_head;
    snprintf(buf, sizeof(buf), "RESPONSE|USERS;");
    while (it) {
        char tmp[128];
        snprintf(tmp, sizeof(tmp), "%s,", it->id);
        strncat(buf, tmp, sizeof(buf)-strlen(buf)-1);
        it = it->next;
    }
    pthread_mutex_unlock(&clients_lock);
    strncat(buf, "\n", sizeof(buf)-strlen(buf)-1);
    send(c->sockfd, buf, strlen(buf), 0);
    log_msg("LISTUSERS requested by %s", c->id);
}

void *client_thread(void *arg) {
    client_t *c = (client_t *)arg;
    char buf[MAXLINE];
    ssize_t n;

    log_msg("New client connected: %s", c->id);
    add_client(c);

    while ((n = recv(c->sockfd, buf, sizeof(buf)-1, 0)) > 0) {
        buf[n] = '\0';
        char *p = strchr(buf, '\n');
        if (p) *p = '\0';

        log_msg("Received from %s: %s", c->id, buf);
        if (has_prefix(buf, "ROLE|")) {
            char *role = buf + 5;
            if (strcmp(role, "admin") == 0) {
                strcpy(c->role, "admin");
                c->authenticated = 0;
                send(c->sockfd, "RESPONSE|ROLE_OK\n", 17, 0);
            } else {
                strcpy(c->role, "observer");
                c->authenticated = 0;
                send(c->sockfd, "RESPONSE|ROLE_OK\n", 17, 0);
            }
        } else if (has_prefix(buf, "AUTH|")) {
            char user[64] = {0}, pass[64] = {0};
            char *kv = buf + 5;
            char *u = strstr(kv, "user=");
            char *pw = strstr(kv, "pass=");
            if (u) {
                u += 5;
                char *semi = strchr(u, ';');
                if (semi) {
                    *semi = '\0';
                    strncpy(user, u, sizeof(user)-1);
                    *semi = ';';
                } else strncpy(user, u, sizeof(user)-1);
            }
            if (pw) {
                pw += 5;
                strncpy(pass, pw, sizeof(pass)-1);
            }
            if (strcmp(user, ADMIN_USER) == 0 && strcmp(pass, ADMIN_PASS) == 0) {
                c->authenticated = 1;
                strcpy(c->role, "admin");
                send(c->sockfd, "RESPONSE|OK\n", 12, 0);
                log_msg("Admin authenticated: %s (%s)", user, c->id);
            } else {
                c->authenticated = 0;
                send(c->sockfd, "RESPONSE|ERROR;reason=auth_failed\n", 34, 0);
                log_msg("Authentication failed from %s (user=%s)", c->id, user);
            }
        } else if (has_prefix(buf, "COMMAND|")) {
            if (strcmp(c->role, "admin") != 0 || !c->authenticated) {
                send(c->sockfd, "RESPONSE|ERROR;reason=not_authorized\n", 36, 0);
                log_msg("Command rejected: not authorized: %s", c->id);
            } else {
                char *cmd = buf + 8;
                handle_command_from_admin(cmd, c);
            }
        } else if (strcmp(buf, "LISTUSERS") == 0) {
            if (strcmp(c->role, "admin") != 0 || !c->authenticated) {
                send(c->sockfd, "RESPONSE|ERROR;reason=not_authorized\n", 36, 0);
            } else {
                send_listusers(c);
            }
        } else {
            send(c->sockfd, "RESPONSE|ERROR;reason=invalid_message\n", 38, 0);
        }
    }

    if (n == 0) {
        log_msg("Client disconnected: %s", c->id);
    } else if (n < 0) {
        log_msg("Recv error from %s: %s", c->id, strerror(errno));
    }
    close(c->sockfd);
    remove_client(c);
    free(c);
    return NULL;
}

void *metro_thread(void *arg) {
    (void)arg;
    while (1) {
        sleep(10);

        pthread_mutex_lock(&metro.lock);
        if (!metro.stopped) {
            metro.station += 1;
        }
        if (!metro.stopped) metro.battery -= 1;
        if (metro.battery < 0) metro.battery = 0;
        pthread_mutex_unlock(&metro.lock);

        pthread_mutex_lock(&metro.lock);
        int arrived = 1;
        pthread_mutex_unlock(&metro.lock);

        if (arrived) {
            broadcast_telemetry();

            pthread_mutex_lock(&metro.lock);
            metro.stopped = 1;
            metro.speed = 0.0;
            pthread_mutex_unlock(&metro.lock);

            log_msg("Arrived at station %d. Stopping 20s.", metro.station);
            sleep(20);

            pthread_mutex_lock(&metro.lock);
            metro.stopped = 0;
            metro.speed = 30.0;
            metro.stations_since_reverse += 1;
            if (metro.stations_since_reverse >= 5) {
                metro.dir = (metro.dir == FWD) ? REV : FWD;
                metro.stations_since_reverse = 0;
                log_msg("Direction reversed. New dir: %s", (metro.dir==FWD)?"FWD":"REV");
            }
            pthread_mutex_unlock(&metro.lock);
        }

        broadcast_telemetry();
    }
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <port> <LogsFile>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    int port = atoi(argv[1]);
    const char *logsfile_path = argv[2];

    logfile = fopen(logsfile_path, "a");
    if (!logfile) {
        perror("fopen logsfile");
        exit(EXIT_FAILURE);
    }

    pthread_mutex_init(&metro.lock, NULL);
    metro.speed = 20.0;
    metro.battery = 100;
    metro.station = 0;
    metro.dir = FWD;
    metro.stations_since_reverse = 0;
    metro.stopped = 0;

    int listenfd;
    if ((listenfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    int opt = 1;
    setsockopt(listenfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in servaddr;
    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(port);

    if (bind(listenfd, (struct sockaddr*)&servaddr, sizeof(servaddr)) < 0) {
        perror("bind");
        exit(EXIT_FAILURE);
    }

    if (listen(listenfd, 10) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    log_msg("Server started on port %d. Logs: %s", port, logsfile_path);

    pthread_t metro_tid;
    if (pthread_create(&metro_tid, NULL, metro_thread, NULL) != 0) {
        perror("pthread_create metro");
        exit(EXIT_FAILURE);
    }

    while (1) {
        struct sockaddr_in cliaddr;
        socklen_t clilen = sizeof(cliaddr);
        int connfd = accept(listenfd, (struct sockaddr*)&cliaddr, &clilen);
        if (connfd < 0) {
            log_msg("Accept error: %s", strerror(errno));
            continue;
        }

        client_t *c = calloc(1, sizeof(client_t));
        c->sockfd = connfd;
        c->addr = cliaddr;
        c->authenticated = 0;
        strcpy(c->role, "observer");
        char ipstr[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &(cliaddr.sin_addr), ipstr, sizeof(ipstr));
        int portn = ntohs(cliaddr.sin_port);
        snprintf(c->id, sizeof(c->id), "%s:%d", ipstr, portn);

        pthread_t tid;
        if (pthread_create(&tid, NULL, client_thread, c) != 0) {
            log_msg("Error creating client thread");
            close(connfd);
            free(c);
        } else {
            pthread_detach(tid);
        }
    }

    fclose(logfile);
    close(listenfd);
    return 0;
}
