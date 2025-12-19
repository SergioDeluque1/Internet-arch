// server.c
// Compilar: gcc -pthread -o server server.c
// Uso: ./server <port> <LogsFile>

#define _POSIX_C_SOURCE 200112L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <stdarg.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#endif

#include <pthread.h>

#define MAXLINE 1024
#define MAXCLIENTS 100
#define ADMIN_USER "admin"
#define ADMIN_PASS "adminpass"

// Metro state
typedef enum { FWD, REV } direction_t;

typedef struct {
    double speed;      // km/h
    int battery;       // %
    int station;       // station index
    direction_t dir;
    int stations_since_reverse;
    int stopped;       // 1 if stopped
    pthread_mutex_t lock;
} metro_state_t;

metro_state_t metro;

// Client info
typedef struct client {
    int sockfd;
    struct sockaddr_in addr;
    char role[16]; // "observer" or "admin"
    int authenticated; // 1 if admin authenticated
    char id[64]; // "ip:port"
    struct client *next;
} client_t;

client_t *clients_head = NULL;
pthread_mutex_t clients_lock = PTHREAD_MUTEX_INITIALIZER;
FILE *logfile = NULL;
pthread_mutex_t log_lock = PTHREAD_MUTEX_INITIALIZER;

// Utility: timestamped log (console + file)
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

// Helper: add client
void add_client(client_t *c) {
    pthread_mutex_lock(&clients_lock);
    c->next = clients_head;
    clients_head = c;
    pthread_mutex_unlock(&clients_lock);
}

// Helper: remove client
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

// Broadcast telemetry to all connected clients
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
            // If send fails we will leave removal to handler on error
            log_msg("Error enviando telemetría a %s: %s", it->id, strerror(errno));
        }
        it = it->next;
    }
    pthread_mutex_unlock(&clients_lock);
    log_msg("Telemetría enviada a todos: %s", msg);
}

// Parse simple key=value;... into buffer (helper)
int has_prefix(const char *s, const char *p) {
    return strncmp(s, p, strlen(p)) == 0;
}

// Execute command if possible; returns message for client
void handle_command_from_admin(const char *cmd, client_t *c) {
    char response[MAXLINE];

    pthread_mutex_lock(&metro.lock);
    // check battery threshold for safety
    if (metro.battery < 5 && strcmp(cmd, "STARTNOW") != 0) {
        snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=battery_too_low\n");
        send(c->sockfd, response, strlen(response), 0);
        pthread_mutex_unlock(&metro.lock);
        log_msg("Comando %s denegado para %s: batería baja (%d%%)", cmd, c->id, metro.battery);
        return;
    }

    if (strcmp(cmd, "SPEEDUP") == 0) {
        if (metro.stopped) {
            snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=stopped\n");
        } else {
            metro.speed += 5.0;
            if (metro.speed > 120.0) metro.speed = 120.0;
            snprintf(response, sizeof(response), "RESPONSE|OK\n");
            log_msg("SPEEDUP ejecutado. Nueva velocidad: %.1f", metro.speed);
        }
    } else if (strcmp(cmd, "SLOWDOWN") == 0) {
        metro.speed -= 5.0;
        if (metro.speed < 0.0) metro.speed = 0.0;
        snprintf(response, sizeof(response), "RESPONSE|OK\n");
        log_msg("SLOWDOWN ejecutado. Nueva velocidad: %.1f", metro.speed);
    } else if (strcmp(cmd, "STOPNOW") == 0) {
        metro.speed = 0.0;
        metro.stopped = 1;
        snprintf(response, sizeof(response), "RESPONSE|OK\n");
        log_msg("STOPNOW ejecutado.");
    } else if (strcmp(cmd, "STARTNOW") == 0) {
        if (metro.stopped) {
            metro.stopped = 0;
            metro.speed = 20.0; // reanudar a velocidad inicial
            snprintf(response, sizeof(response), "RESPONSE|OK\n");
            log_msg("STARTNOW ejecutado. Velocidad: %.1f", metro.speed);
        } else {
            snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=not_stopped\n");
        }
    } else {
        snprintf(response, sizeof(response), "RESPONSE|ERROR;reason=unknown_command\n");
    }
    pthread_mutex_unlock(&metro.lock);
    send(c->sockfd, response, strlen(response), 0);
}

// List users to admin
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
    log_msg("LISTUSERS solicitado por %s", c->id);
}

// Handler per client
void *client_thread(void *arg) {
    client_t *c = (client_t *)arg;
    char buf[MAXLINE];
    ssize_t n;

    log_msg("Nuevo cliente conectado: %s", c->id);
    add_client(c);

    // On connect, expect role declaration or simply accept default observer
    // We'll allow client to send "ROLE|observer" or "ROLE|admin"
    while ((n = recv(c->sockfd, buf, sizeof(buf)-1, 0)) > 0) {
        buf[n] = '\0';
        // trim newline
        char *p = strchr(buf, '\n');
        if (p) *p = '\0';

        log_msg("Recibido de %s: %s", c->id, buf);
        // parse
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
            // format: AUTH|user=...;pass=...
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
            // Auth check
            if (strcmp(user, ADMIN_USER) == 0 && strcmp(pass, ADMIN_PASS) == 0) {
                c->authenticated = 1;
                strcpy(c->role, "admin");
                send(c->sockfd, "RESPONSE|OK\n", 12, 0);
                log_msg("Admin autenticado: %s (%s)", user, c->id);
            } else {
                c->authenticated = 0;
                send(c->sockfd, "RESPONSE|ERROR;reason=auth_failed\n", 34, 0);
                log_msg("Autenticación fallida desde %s (user=%s)", c->id, user);
            }
        } else if (has_prefix(buf, "COMMAND|")) {
            if (strcmp(c->role, "admin") != 0 || !c->authenticated) {
                send(c->sockfd, "RESPONSE|ERROR;reason=not_authorized\n", 36, 0);
                log_msg("Comando rechazado por no autorizado: %s", c->id);
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
        log_msg("Cliente desconectado: %s", c->id);
    } else if (n < 0) {
        log_msg("Recv error de %s: %s", c->id, strerror(errno));
    }
    close(c->sockfd);
    remove_client(c);
    free(c);
    return NULL;
}

// Thread: metro simulation and telemetry sending every 10s
void *metro_thread(void *arg) {
    (void)arg;
    while (1) {
        // Sleep 10 seconds between telemetry sends
        sleep(10);

        // Update metro state between telemetry sends
        pthread_mutex_lock(&metro.lock);
        if (!metro.stopped) {
            // move: speed affects progress to next station (we simulate station arrival simply)
            // We'll increment station every cycle based on some heuristic
            // Simpler: every telemetry tick we assume moves to next station occasionally
            // We'll increment station by 1 each telemetry tick to trigger station behavior in demo
            metro.station += 1;
            if (metro.station > 1000000) metro.station = 0; // safety
        }
        // battery drains slowly
        if (!metro.stopped) metro.battery -= 1;
        if (metro.battery < 0) metro.battery = 0;
        pthread_mutex_unlock(&metro.lock);

        // If arrived to a station, do stop for 20s
        // For this simulation: treat every "station increment" as arrival
        pthread_mutex_lock(&metro.lock);
        int arrived = 1; // because we increment station each tick
        pthread_mutex_unlock(&metro.lock);

        if (arrived) {
            // Broadcast arrival telemetry first
            broadcast_telemetry();

            // Stop for 20 seconds
            pthread_mutex_lock(&metro.lock);
            metro.stopped = 1;
            metro.speed = 0.0;
            pthread_mutex_unlock(&metro.lock);

            log_msg("Llegada a estación %d. Parando 20s.", metro.station);
            sleep(20);

            // After stop, increase stations_since_reverse and maybe reverse
            pthread_mutex_lock(&metro.lock);
            metro.stopped = 0;
            metro.speed = 30.0; // resume baseline
            metro.stations_since_reverse += 1;
            if (metro.stations_since_reverse >= 5) {
                // reverse direction
                metro.dir = (metro.dir == FWD) ? REV : FWD;
                metro.stations_since_reverse = 0;
                log_msg("Se invierte la marcha. Nueva dirección: %s", (metro.dir==FWD)?"FWD":"REV");
            }
            pthread_mutex_unlock(&metro.lock);
        }

        // broadcast telemetry (again after resume)
        broadcast_telemetry();
    }
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Uso: %s <port> <LogsFile>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    int port = atoi(argv[1]);
    const char *logsfile_path = argv[2];

    logfile = fopen(logsfile_path, "a");
    if (!logfile) {
        perror("fopen logsfile");
        exit(EXIT_FAILURE);
    }

    // Initialize metro state
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

    log_msg("Servidor arrancado en puerto %d. Logs: %s", port, logsfile_path);

    // Start metro simulation thread
    pthread_t metro_tid;
    if (pthread_create(&metro_tid, NULL, metro_thread, NULL) != 0) {
        perror("pthread_create metro");
        exit(EXIT_FAILURE);
    }

    // Accept loop
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
            log_msg("Error creando hilo cliente");
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
