"""
Core ACO implementation for grid-based robot path planning.
Group 2 - Parallel and Distributed Computing

Each ant explores independently — path construction is parallelized
using multiprocessing.Pool so true parallelism bypasses the GIL.
"""

import numpy as np
import random
import time
from multiprocessing import Pool, cpu_count


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

class Grid:
    """NxN grid with configurable random obstacle placement."""

    def __init__(self, N, obstacle_density=0.2, start=None, goal=None, seed=None):
        self.N = N
        self.obstacle_density = obstacle_density
        self.start = start or (0, 0)
        self.goal  = goal  or (N - 1, N - 1)

        rng = random.Random(seed)
        self.grid = np.zeros((N, N), dtype=np.int8)
        self._place_obstacles(rng)
        # Always keep start/goal clear
        self.grid[self.start] = 0
        self.grid[self.goal]  = 0

    def _place_obstacles(self, rng):
        all_cells = [
            (r, c)
            for r in range(self.N)
            for c in range(self.N)
            if (r, c) != self.start and (r, c) != self.goal
        ]
        n_obs = int(len(all_cells) * self.obstacle_density)
        for r, c in rng.sample(all_cells, min(n_obs, len(all_cells))):
            self.grid[r, c] = 1

    def is_valid(self, r, c):
        return 0 <= r < self.N and 0 <= c < self.N and self.grid[r, c] == 0

    def get_neighbors(self, r, c):
        """8-directional neighbors that are free."""
        moves = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
        return [(r+dr, c+dc) for dr, dc in moves if self.is_valid(r+dr, c+dc)]

    def add_dynamic_obstacles(self, n_new=5):
        """Randomly block n_new currently free cells (dynamic obstacle demo)."""
        free = [
            (r, c)
            for r in range(self.N) for c in range(self.N)
            if self.grid[r, c] == 0
            and (r, c) != self.start and (r, c) != self.goal
        ]
        for r, c in random.sample(free, min(n_new, len(free))):
            self.grid[r, c] = 1

    def has_path(self):
        """BFS reachability check from start to goal."""
        visited = {self.start}
        queue = [self.start]
        while queue:
            cur = queue.pop(0)
            if cur == self.goal:
                return True
            for nb in self.get_neighbors(*cur):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        return False

    def copy(self):
        g = Grid.__new__(Grid)
        g.N = self.N
        g.obstacle_density = self.obstacle_density
        g.start = self.start
        g.goal  = self.goal
        g.grid  = self.grid.copy()
        return g


# ---------------------------------------------------------------------------
# Standalone ant worker  (must be top-level for multiprocessing pickling)
# ---------------------------------------------------------------------------

_MOVES = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]


def _ant_walk(args):
    """
    Construct one ant's path on the grid.
    Runs in a worker process — receives a snapshot of the pheromone matrix
    and the grid array so no shared state is needed.
    Returns the path list, or None if the ant gets stuck.
    """
    pheromone, grid_arr, N, start, goal, alpha, beta, max_steps, seed = args

    rng = random.Random(seed)
    np.random.seed(seed & 0xFFFFFFFF)

    path    = [start]
    visited = {start}
    current = start
    gr, gc  = goal

    for _ in range(max_steps):
        if current == goal:
            return path

        r, c = current
        neighbors = []
        for dr, dc in _MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and grid_arr[nr, nc] == 0 and (nr, nc) not in visited:
                neighbors.append((nr, nc))

        if not neighbors:
            return None

        # Probability: tau^alpha * eta^beta  (eta = 1 / Manhattan dist to goal)
        weights = []
        for nr, nc in neighbors:
            tau = float(pheromone[nr, nc]) ** alpha
            dist = abs(nr - gr) + abs(nc - gc) or 1e-9
            eta  = (1.0 / dist) ** beta
            weights.append(tau * eta)

        total = sum(weights) or 1.0
        weights = [w / total for w in weights]

        # Roulette-wheel selection
        rv, cum = rng.random(), 0.0
        chosen = neighbors[-1]
        for nb, w in zip(neighbors, weights):
            cum += w
            if rv <= cum:
                chosen = nb
                break

        path.append(chosen)
        visited.add(chosen)
        current = chosen

    return None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def path_length(path):
    """Euclidean length of a cell-path."""
    if not path or len(path) < 2:
        return float('inf')
    total = 0.0
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        total += ((r2 - r1) ** 2 + (c2 - c1) ** 2) ** 0.5
    return total


# ---------------------------------------------------------------------------
# ACO Solver
# ---------------------------------------------------------------------------

class ACOPathfinder:
    """
    Ant Colony Optimisation for grid path planning.

    parallel=True  → each ant runs in its own process via Pool.map
    parallel=False → sequential reference implementation
    """

    def __init__(self, grid,
                 n_ants=20,
                 n_iterations=100,
                 alpha=1.0,
                 beta=2.5,
                 rho=0.1,
                 Q=1.0,
                 n_processes=None):

        self.grid         = grid
        self.n_ants       = n_ants
        self.n_iterations = n_iterations
        self.alpha        = alpha
        self.beta         = beta
        self.rho          = rho
        self.Q            = Q
        self.n_processes  = n_processes or cpu_count()

        # Pheromone matrix — obstacles stay at 0
        self.pheromone = np.full((grid.N, grid.N), 0.1)
        self.pheromone[grid.grid == 1] = 0.0

        self.best_path   = None
        self.best_length = float('inf')

        # Tracking
        self.convergence_history = []   # best length per iteration
        self.pheromone_history   = []   # (iter, snapshot) every 10 iters
        self.iteration_times     = []

    # ------------------------------------------------------------------

    def run(self, parallel=True, verbose=True,
            dynamic_obstacles=False, dynamic_interval=25,
            progress_callback=None):
        """
        Run the optimiser.

        dynamic_obstacles   : inject new obstacles every dynamic_interval iters.
        progress_callback   : called with a dict after every iteration — used
                              by the Flask server to stream SSE events.
        """
        N         = self.grid.N
        max_steps = N * N * 3

        pool = Pool(processes=self.n_processes) if parallel else None

        t_total = time.time()
        try:
            for it in range(self.n_iterations):
                t_iter = time.time()

                # ---- dynamic obstacles ----
                if dynamic_obstacles and it > 0 and it % dynamic_interval == 0:
                    n_new = max(1, N // 5)
                    self.grid.add_dynamic_obstacles(n_new)
                    self.pheromone[self.grid.grid == 1] = 0.0
                    if verbose:
                        print(f"  [Dynamic] +{n_new} obstacles at iter {it}")

                # ---- build args for every ant ----
                base_seed = random.randint(0, 2**30)
                args_list = [
                    (
                        self.pheromone.copy(),
                        self.grid.grid,
                        N,
                        self.grid.start,
                        self.grid.goal,
                        self.alpha,
                        self.beta,
                        max_steps,
                        base_seed + i,
                    )
                    for i in range(self.n_ants)
                ]

                # ---- parallel or sequential exploration ----
                if parallel and pool is not None:
                    paths = pool.map(_ant_walk, args_list)
                else:
                    paths = [_ant_walk(a) for a in args_list]

                valid = [p for p in paths if p and p[-1] == self.grid.goal]

                # ---- pheromone update ----
                self.pheromone *= (1.0 - self.rho)
                self.pheromone  = np.maximum(self.pheromone, 1e-10)
                self.pheromone[self.grid.grid == 1] = 0.0

                for p in valid:
                    length = path_length(p)
                    deposit = self.Q / length
                    for cell in p:
                        self.pheromone[cell] += deposit
                    if length < self.best_length:
                        self.best_length = length
                        self.best_path   = p

                # ---- bookkeeping ----
                self.convergence_history.append(self.best_length)
                if it % 10 == 0:
                    self.pheromone_history.append((it, self.pheromone.copy()))

                elapsed = time.time() - t_iter
                self.iteration_times.append(elapsed)

                if progress_callback is not None:
                    ph      = self.pheromone
                    max_ph  = float(ph.max())
                    ph_norm = (ph / max_ph).tolist() if max_ph > 0 else ph.tolist()
                    progress_callback({
                        "type":        "progress",
                        "iteration":   it + 1,
                        "total":       self.n_iterations,
                        "best_length": self.best_length if self.best_length != float("inf") else None,
                        "valid_ants":  len(valid),
                        "pheromone":   ph_norm,
                        "best_path":   [[int(r), int(c)] for r, c in self.best_path] if self.best_path else None,
                        "cells":       self.grid.grid.tolist(),
                        "iter_time":   round(elapsed, 4),
                    })

                if verbose and (it + 1) % 10 == 0:
                    print(
                        f"  Iter {it+1:4d}/{self.n_iterations} | "
                        f"Best: {self.best_length:8.2f} | "
                        f"Valid ants: {len(valid):3d}/{self.n_ants} | "
                        f"{elapsed:.3f}s"
                    )

        finally:
            if pool:
                pool.close()
                pool.join()

        if verbose:
            print(f"\nTotal: {time.time() - t_total:.2f}s  "
                  f"Best path length: {self.best_length:.2f}  "
                  f"Steps: {len(self.best_path) if self.best_path else 0}")

        return self.best_path, self.best_length
