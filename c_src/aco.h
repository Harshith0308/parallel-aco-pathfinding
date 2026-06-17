#ifndef ACO_H
#define ACO_H

/* ============================================================
   aco.h  —  ACO solver structs and declarations
   Parallelism: #pragma omp parallel for across the ant loop
   Group 2 : Parallel and Distributed Computing
   ============================================================ */

#include "grid.h"
#include <float.h>

/* Max cells a single ant can visit (N*N unique cells) */
#define MAX_PATH_LEN  (MAX_N * MAX_N)

/* Max iterations stored in convergence history */
#define MAX_HISTORY   1000

/* ── Per-ant state (independent → safe to parallelise) ──────── */
typedef struct {
    int          path_r[MAX_PATH_LEN];
    int          path_c[MAX_PATH_LEN];
    int          path_len;
    int          reached_goal;
    double       length;
    unsigned int rng;   /* per-ant LCG state */
} Ant;

/* ── ACO hyper-parameters ────────────────────────────────────── */
typedef struct {
    double alpha;            /* pheromone weight          */
    double beta;             /* heuristic weight          */
    double rho;              /* evaporation rate          */
    double Q;                /* pheromone deposit amount  */
    int    n_ants;
    int    n_iterations;
    int    n_threads;        /* OpenMP thread count       */
    int    dynamic_obstacles;
    int    dynamic_interval; /* add obstacles every N iters */
} ACOParams;

/* ── Shared solver state (updated serially between iterations) ── */
typedef struct {
    double pheromone[MAX_N][MAX_N];

    int    best_path_r[MAX_PATH_LEN];
    int    best_path_c[MAX_PATH_LEN];
    int    best_path_len;
    double best_length;

    double convergence[MAX_HISTORY]; /* best length per iteration */
    int    iteration;                /* iterations completed      */
    int    valid_ants;               /* successful ants last iter */
} ACOState;

/* Initialise pheromone matrix from grid */
void   aco_init(ACOState *s, const Grid *g);

/* Run ONE iteration:
   - Parallel ant walk  (OpenMP #pragma omp parallel for)
   - Serial pheromone update
   Returns number of ants that reached the goal. */
int    aco_run_iteration(ACOState *s, Grid *g,
                         const ACOParams *p, Ant *ants);

/* Euclidean path length */
double aco_path_length(const int *pr, const int *pc, int len);

#endif /* ACO_H */
