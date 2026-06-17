#ifndef GRID_H
#define GRID_H

/* ============================================================
   grid.h  —  NxN grid with random obstacle placement
   Group 2 : Parallel and Distributed Computing
   ============================================================ */

#define MAX_N 50

/* 8-directional movement (shared with aco.c / viz.c) */
static const int DR[8] = { 0,  0,  1, -1,  1,  1, -1, -1 };
static const int DC[8] = { 1, -1,  0,  0,  1, -1,  1, -1 };

typedef struct {
    int          N;
    int          cells[MAX_N][MAX_N];   /* 0 = free, 1 = obstacle */
    int          start_r, start_c;
    int          goal_r,  goal_c;
    double       density;
    unsigned int seed;
} Grid;

/* Initialise grid with random obstacles (Fisher-Yates shuffle) */
void grid_init(Grid *g, int N, double density, unsigned int seed);

/* Returns 1 if (r,c) is in-bounds and free */
int  grid_valid(const Grid *g, int r, int c);

/* Add n_new new obstacles to currently free cells */
void grid_add_dynamic_obstacles(Grid *g, int n_new);

/* BFS reachability check: returns 1 if start->goal path exists */
int  grid_has_path(const Grid *g);

/* Thread-safe LCG random helpers (per-ant state passed by pointer) */
unsigned int grid_lcg(unsigned int *state);
double       grid_lcg_double(unsigned int *state);

#endif /* GRID_H */
