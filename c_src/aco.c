/* ============================================================
   aco.c  —  ACO solver with OpenMP parallelism
   Key section:  #pragma omp parallel for  (ant exploration loop)
   Group 2 : Parallel and Distributed Computing
   ============================================================ */

#include "aco.h"
#include "grid.h"
#include <math.h>
#include <string.h>
#include <omp.h>

/* ── Utilities ──────────────────────────────────────────────── */
double aco_path_length(const int *pr, const int *pc, int len) {
    if (len < 2) return DBL_MAX;
    double total = 0.0;
    for (int i = 0; i < len - 1; i++) {
        double dr = pr[i+1] - pr[i];
        double dc = pc[i+1] - pc[i];
        total += sqrt(dr*dr + dc*dc);
    }
    return total;
}

/* ── Initialise pheromone matrix ────────────────────────────── */
void aco_init(ACOState *s, const Grid *g) {
    for (int r = 0; r < g->N; r++)
        for (int c = 0; c < g->N; c++)
            s->pheromone[r][c] = (g->cells[r][c] == 0) ? 0.1 : 0.0;

    s->best_path_len = 0;
    s->best_length   = DBL_MAX;
    s->iteration     = 0;
    s->valid_ants    = 0;
    memset(s->convergence, 0, sizeof(s->convergence));
}

/* ── Single ant path construction (called inside OMP region) ── */
static void ant_walk(Ant *ant, const Grid *g,
                     const double ph[MAX_N][MAX_N],
                     const ACOParams *p) {
    int  N        = g->N;
    int  goal_r   = g->goal_r,  goal_c = g->goal_c;
    int  max_steps = N * N * 3;

    /* Per-ant visited array — private to this stack frame */
    int visited[MAX_N][MAX_N];
    memset(visited, 0, sizeof(visited));

    ant->path_len    = 0;
    ant->reached_goal = 0;
    ant->length       = DBL_MAX;

    int r = g->start_r, c = g->start_c;
    ant->path_r[ant->path_len] = r;
    ant->path_c[ant->path_len] = c;
    ant->path_len++;
    visited[r][c] = 1;

    for (int step = 0; step < max_steps; step++) {

        if (r == goal_r && c == goal_c) {
            ant->reached_goal = 1;
            break;
        }

        /* ── Build candidate list ─────────────────────────── */
        int    nb_r[8], nb_c[8];
        double weight[8];
        int    nb_n    = 0;
        double w_total = 0.0;

        for (int d = 0; d < 8; d++) {
            int nr = r + DR[d], nc = c + DC[d];
            if (!grid_valid(g, nr, nc) || visited[nr][nc]) continue;

            double tau = ph[nr][nc];
            if (tau < 1e-10) tau = 1e-10;

            /* Heuristic: inverse Manhattan distance to goal */
            int dist = abs(nr - goal_r) + abs(nc - goal_c);
            double eta = 1.0 / (dist > 0 ? dist : 1);

            double w = pow(tau, p->alpha) * pow(eta, p->beta);
            nb_r[nb_n] = nr;
            nb_c[nb_n] = nc;
            weight[nb_n] = w;
            w_total += w;
            nb_n++;
        }

        if (nb_n == 0) return;  /* stuck */

        /* ── Roulette-wheel selection ──────────────────────── */
        double rv  = grid_lcg_double(&ant->rng) * w_total;
        int chosen = nb_n - 1;
        double cum = 0.0;
        for (int i = 0; i < nb_n; i++) {
            cum += weight[i];
            if (rv <= cum) { chosen = i; break; }
        }

        r = nb_r[chosen];
        c = nb_c[chosen];
        visited[r][c] = 1;

        if (ant->path_len < MAX_PATH_LEN) {
            ant->path_r[ant->path_len] = r;
            ant->path_c[ant->path_len] = c;
            ant->path_len++;
        }
    }

    if (ant->reached_goal)
        ant->length = aco_path_length(ant->path_r, ant->path_c, ant->path_len);
}

/* ── One full ACO iteration ─────────────────────────────────── */
int aco_run_iteration(ACOState *s, Grid *g,
                      const ACOParams *p, Ant *ants) {
    int N = g->N;

    /* ╔══════════════════════════════════════════════════════════╗
       ║  PARALLEL ANT EXPLORATION — each ant is independent     ║
       ║  Read-only: s->pheromone, g->cells                      ║
       ║  Write:     ants[i]  (private per iteration i)          ║
       ╚══════════════════════════════════════════════════════════╝ */
    #pragma omp parallel for schedule(dynamic) \
                             num_threads(p->n_threads) \
                             default(none) \
                             shared(ants, g, s, p)
    for (int i = 0; i < p->n_ants; i++) {
        /* Deterministic but varied seed per ant/iteration */
        ants[i].rng = (unsigned int)(s->iteration * 7919u + i * 1013u + 42u);
        ant_walk(&ants[i], g,
                 (const double (*)[MAX_N])s->pheromone, p);
    }
    /* ── Implicit OMP barrier: all ants done before proceeding ─ */

    /* ── SERIAL: evaporate pheromones ───────────────────────── */
    for (int r = 0; r < N; r++)
        for (int c = 0; c < N; c++) {
            s->pheromone[r][c] *= (1.0 - p->rho);
            if (s->pheromone[r][c] < 1e-10) s->pheromone[r][c] = 1e-10;
            if (g->cells[r][c] == 1)        s->pheromone[r][c] = 0.0;
        }

    /* ── SERIAL: deposit pheromones, track best path ────────── */
    int valid = 0;
    for (int i = 0; i < p->n_ants; i++) {
        if (!ants[i].reached_goal || ants[i].length >= DBL_MAX) continue;
        valid++;

        double deposit = p->Q / ants[i].length;
        for (int j = 0; j < ants[i].path_len; j++)
            s->pheromone[ants[i].path_r[j]][ants[i].path_c[j]] += deposit;

        if (ants[i].length < s->best_length) {
            s->best_length   = ants[i].length;
            s->best_path_len = ants[i].path_len;
            memcpy(s->best_path_r, ants[i].path_r,
                   ants[i].path_len * sizeof(int));
            memcpy(s->best_path_c, ants[i].path_c,
                   ants[i].path_len * sizeof(int));
        }
    }

    /* Zero obstacles (deposits may have leaked) */
    for (int r = 0; r < N; r++)
        for (int c = 0; c < N; c++)
            if (g->cells[r][c] == 1) s->pheromone[r][c] = 0.0;

    s->valid_ants = valid;
    if (s->iteration < MAX_HISTORY)
        s->convergence[s->iteration] =
            (s->best_length < DBL_MAX) ? s->best_length : 0.0;

    s->iteration++;
    return valid;
}
