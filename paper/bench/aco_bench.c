/* ============================================================
   aco_bench.c — benchmark driver for the C/OpenMP ACO solver.

   Wraps the existing c_src/ solver (aco.c, grid.c) with a timed
   main() and emits one CSV row per repeat to stdout:

     impl,N,density,n_ants,n_iters,threads,repeat,total_s,per_iter_ms,best_length,valid_last,reached

   Timing covers ONLY the iteration loop (grid/pheromone init excluded),
   measured with omp_get_wtime(). Ant seeding in aco_run_iteration is
   deterministic, so solution quality is identical across thread counts —
   isolating pure parallel speedup.

   Build (see build.sh):
     gcc -O2 -fopenmp -I../../c_src aco_bench.c ../../c_src/aco.c \
         ../../c_src/grid.c -lm -o aco_bench
   ============================================================ */

#include "aco.h"
#include "grid.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <omp.h>

static int    arg_i(int argc, char **argv, const char *key, int def) {
    for (int i = 1; i < argc - 1; i++)
        if (strcmp(argv[i], key) == 0) return atoi(argv[i + 1]);
    return def;
}
static double arg_d(int argc, char **argv, const char *key, double def) {
    for (int i = 1; i < argc - 1; i++)
        if (strcmp(argv[i], key) == 0) return atof(argv[i + 1]);
    return def;
}
static int    flag(int argc, char **argv, const char *key) {
    for (int i = 1; i < argc; i++)
        if (strcmp(argv[i], key) == 0) return 1;
    return 0;
}
static const char *arg_s(int argc, char **argv, const char *key, const char *def) {
    for (int i = 1; i < argc - 1; i++)
        if (strcmp(argv[i], key) == 0) return argv[i + 1];
    return def;
}

/* Load a grid from a shared text file so the Python and C back-ends solve the
   IDENTICAL instance. Format:
     line 1:  N start_r start_c goal_r goal_c
     N lines: N chars each, '0' = free, '1' = obstacle                       */
static int load_grid(Grid *g, const char *path, double density) {
    FILE *f = fopen(path, "r");
    if (!f) return 0;
    int N, sr, sc, gr, gc;
    if (fscanf(f, "%d %d %d %d %d", &N, &sr, &sc, &gr, &gc) != 5) { fclose(f); return 0; }
    if (N > MAX_N) N = MAX_N;
    g->N = N; g->start_r = sr; g->start_c = sc; g->goal_r = gr; g->goal_c = gc;
    g->density = density; g->seed = 42u;
    memset(g->cells, 0, sizeof(g->cells));
    char row[MAX_N + 8];
    for (int r = 0; r < N; r++) {
        if (fscanf(f, "%s", row) != 1) { fclose(f); return 0; }
        for (int c = 0; c < N && row[c]; c++)
            g->cells[r][c] = (row[c] == '1') ? 1 : 0;
    }
    fclose(f);
    return 1;
}

int main(int argc, char **argv) {
    int    N        = arg_i(argc, argv, "--N",        48);
    double density  = arg_d(argc, argv, "--density",  0.20);
    unsigned seed   = (unsigned) arg_i(argc, argv, "--seed", 42);
    int    n_ants   = arg_i(argc, argv, "--ants",     200);
    int    n_iters  = arg_i(argc, argv, "--iters",    100);
    double alpha    = arg_d(argc, argv, "--alpha",    1.0);
    double beta     = arg_d(argc, argv, "--beta",     2.5);
    double rho      = arg_d(argc, argv, "--rho",      0.10);
    double Q        = arg_d(argc, argv, "--Q",        1.0);
    int    threads  = arg_i(argc, argv, "--threads",  1);
    int    repeats  = arg_i(argc, argv, "--repeats",  5);
    int    warmup   = arg_i(argc, argv, "--warmup",   1);
    int    dynamic  = flag(argc, argv, "--dynamic");
    int    dyn_int  = arg_i(argc, argv, "--dyn-interval", 25);
    int    header   = flag(argc, argv, "--csv-header");
    const char *grid_file = arg_s(argc, argv, "--grid", NULL);

    if (N > MAX_N) N = MAX_N;   /* solver static cap */

    if (header)
        printf("impl,N,density,n_ants,n_iters,threads,repeat,"
               "total_s,per_iter_ms,best_length,valid_last,reached\n");

    /* Heap-allocate the large solver state + ant pool. */
    ACOState *st   = (ACOState *) malloc(sizeof(ACOState));
    Ant      *ants = (Ant *)      malloc(sizeof(Ant) * (size_t) n_ants);
    if (!st || !ants) { fprintf(stderr, "alloc failed\n"); return 1; }

    ACOParams p = {
        .alpha = alpha, .beta = beta, .rho = rho, .Q = Q,
        .n_ants = n_ants, .n_iterations = n_iters,
        .n_threads = threads,
        .dynamic_obstacles = dynamic, .dynamic_interval = dyn_int,
    };

    for (int rep = 0; rep < repeats + warmup; rep++) {
        Grid g;
        if (grid_file) {
            if (!load_grid(&g, grid_file, density)) {
                fprintf(stderr, "failed to load grid: %s\n", grid_file);
                return 1;
            }
        } else {
            grid_init(&g, N, density, seed);
        }
        aco_init(st, &g);

        int valid_last = 0;
        double t0 = omp_get_wtime();
        for (int it = 0; it < n_iters; it++) {
            if (dynamic && it > 0 && it % dyn_int == 0) {
                int n_new = N / 5; if (n_new < 1) n_new = 1;
                grid_add_dynamic_obstacles(&g, n_new);
            }
            valid_last = aco_run_iteration(st, &g, &p, ants);
        }
        double total = omp_get_wtime() - t0;

        if (rep < warmup) continue;   /* discard warm-up run(s) */

        int reached = (st->best_length < DBL_MAX) ? 1 : 0;
        double best = reached ? st->best_length : 0.0;
        printf("c_openmp,%d,%.3f,%d,%d,%d,%d,%.6f,%.4f,%.4f,%d,%d\n",
               N, density, n_ants, n_iters, threads, rep - warmup,
               total, (total / n_iters) * 1000.0, best, valid_last, reached);
        fflush(stdout);
    }

    free(ants);
    free(st);
    return 0;
}
