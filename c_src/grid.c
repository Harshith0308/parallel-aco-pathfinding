/* ============================================================
   grid.c  —  Grid implementation
   Group 2 : Parallel and Distributed Computing
   ============================================================ */

#include "grid.h"
#include <string.h>
#include <stdlib.h>

/* ── LCG random (Numerical Recipes constants) ──────────────────── */
unsigned int grid_lcg(unsigned int *state) {
    *state = 1664525u * (*state) + 1013904223u;
    return *state;
}
double grid_lcg_double(unsigned int *state) {
    return (double)(grid_lcg(state) & 0x7FFFFFFFu) / 2147483647.0;
}

/* ── Grid initialisation ───────────────────────────────────────── */
void grid_init(Grid *g, int N, double density, unsigned int seed) {
    if (N < 2)  N = 2;
    if (N > MAX_N) N = MAX_N;
    if (density < 0.0) density = 0.0;
    if (density > 0.6) density = 0.6;

    g->N       = N;
    g->density = density;
    g->seed    = seed;
    g->start_r = 0;      g->start_c = 0;
    g->goal_r  = N - 1;  g->goal_c  = N - 1;

    memset(g->cells, 0, sizeof(g->cells));

    /* Collect all candidate cells (exclude start and goal) */
    int idx[MAX_N * MAX_N];
    int count = 0;
    for (int r = 0; r < N; r++)
        for (int c = 0; c < N; c++)
            if (!(r == g->start_r && c == g->start_c) &&
                !(r == g->goal_r  && c == g->goal_c))
                idx[count++] = r * N + c;

    /* Fisher-Yates partial shuffle to pick n_obs cells */
    int n_obs = (int)(count * density);
    unsigned int rng = seed;
    for (int i = count - 1; i > count - n_obs - 1 && i > 0; i--) {
        int j = (int)(grid_lcg(&rng) % (unsigned)(i + 1));
        int tmp = idx[i]; idx[i] = idx[j]; idx[j] = tmp;
    }
    for (int i = count - 1; i >= count - n_obs; i--) {
        g->cells[idx[i] / N][idx[i] % N] = 1;
    }
}

/* ── Validity check ────────────────────────────────────────────── */
int grid_valid(const Grid *g, int r, int c) {
    return r >= 0 && r < g->N && c >= 0 && c < g->N && g->cells[r][c] == 0;
}

/* ── Dynamic obstacles ─────────────────────────────────────────── */
void grid_add_dynamic_obstacles(Grid *g, int n_new) {
    int free_idx[MAX_N * MAX_N];
    int count = 0;

    for (int r = 0; r < g->N; r++)
        for (int c = 0; c < g->N; c++)
            if (g->cells[r][c] == 0 &&
                !(r == g->start_r && c == g->start_c) &&
                !(r == g->goal_r  && c == g->goal_c))
                free_idx[count++] = r * g->N + c;

    if (count == 0) return;
    if (n_new > count) n_new = count;

    /* Partial shuffle + place */
    unsigned int rng = g->seed ^ 0xDEADBEEFu;
    for (int i = count - 1; i > count - n_new - 1 && i > 0; i--) {
        int j = (int)(grid_lcg(&rng) % (unsigned)(i + 1));
        int tmp = free_idx[i]; free_idx[i] = free_idx[j]; free_idx[j] = tmp;
    }
    for (int i = count - 1; i >= count - n_new; i--)
        g->cells[free_idx[i] / g->N][free_idx[i] % g->N] = 1;

    /* Bump seed so next call uses different positions */
    g->seed = grid_lcg(&g->seed);
}

/* ── BFS reachability ──────────────────────────────────────────── */
int grid_has_path(const Grid *g) {
    int  visited[MAX_N][MAX_N];
    int  qr[MAX_N * MAX_N], qc[MAX_N * MAX_N];
    int  head = 0, tail = 0;

    memset(visited, 0, sizeof(visited));
    qr[tail] = g->start_r;
    qc[tail] = g->start_c;
    tail++;
    visited[g->start_r][g->start_c] = 1;

    while (head < tail) {
        int r = qr[head], c = qc[head++];
        if (r == g->goal_r && c == g->goal_c) return 1;
        for (int d = 0; d < 8; d++) {
            int nr = r + DR[d], nc = c + DC[d];
            if (grid_valid(g, nr, nc) && !visited[nr][nc]) {
                visited[nr][nc] = 1;
                qr[tail] = nr; qc[tail] = nc; tail++;
            }
        }
    }
    return 0;
}
