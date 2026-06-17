"""
Evaluation experiments for ACO grid path planning.
Group 2 - Parallel and Distributed Computing

Experiments:
  1. Path length vs obstacle density
  2. Parallel speedup (sequential vs N worker processes)
"""

import time
import numpy as np
from multiprocessing import cpu_count

from aco_grid import Grid, ACOPathfinder


# ---------------------------------------------------------------------------
# Experiment 1 — density sweep
# ---------------------------------------------------------------------------

def evaluate_obstacle_density(densities,
                               N=20,
                               n_trials=3,
                               n_ants=25,
                               n_iterations=80,
                               verbose=True):
    """
    For each obstacle density run n_trials independent grids, record:
      length       — mean best path length across successful trials
      std          — standard deviation of path lengths
      success_rate — fraction of trials where a path was found
    """
    results = {}

    for density in densities:
        if verbose:
            print(f"\nDensity {density:.2f} ({'='*30})")

        lengths = []
        successes = 0

        for trial in range(n_trials):
            grid = Grid(N, obstacle_density=density, seed=trial * 137 + 7)

            if not grid.has_path():
                if verbose:
                    print(f"  Trial {trial+1}: grid has no valid path — skipped")
                continue

            aco = ACOPathfinder(grid, n_ants=n_ants, n_iterations=n_iterations)
            best_path, best_len = aco.run(parallel=True, verbose=False)

            if best_path is not None:
                lengths.append(best_len)
                successes += 1
                if verbose:
                    print(f"  Trial {trial+1}: length = {best_len:.2f}")
            else:
                if verbose:
                    print(f"  Trial {trial+1}: ACO found no path")

        results[density] = {
            "length":       float(np.mean(lengths)) if lengths else float("inf"),
            "std":          float(np.std(lengths))  if lengths else 0.0,
            "success_rate": successes / n_trials,
        }

    return results


# ---------------------------------------------------------------------------
# Experiment 2 — parallelisation speedup
# ---------------------------------------------------------------------------

def evaluate_parallelization(N=25,
                              n_ants=40,
                              n_iterations=50,
                              process_counts=None,
                              verbose=True):
    """
    Run identical ACO jobs with 1 (sequential), 2, 4, … processes.
    Returns (process_counts, wall_times, best_lengths).

    n_proc=1 is deliberately run sequentially (no Pool overhead) as the
    baseline; n_proc>=2 uses multiprocessing.Pool for true parallelism.
    """
    if process_counts is None:
        max_cpu = cpu_count()
        process_counts = sorted({1, 2, 4, min(8, max_cpu)})

    # Build a single grid that is guaranteed solvable
    seed = 42
    grid = Grid(N, obstacle_density=0.2, seed=seed)
    while not grid.has_path():
        seed += 1
        grid = Grid(N, obstacle_density=0.18, seed=seed)

    times   = []
    lengths = []

    for n_proc in process_counts:
        if verbose:
            label = "sequential" if n_proc == 1 else f"{n_proc} processes"
            print(f"\n[{label}]")

        aco = ACOPathfinder(
            grid.copy(),
            n_ants=n_ants,
            n_iterations=n_iterations,
            n_processes=n_proc,
        )

        t0 = time.perf_counter()
        best_path, best_len = aco.run(
            parallel=(n_proc > 1),
            verbose=verbose,
        )
        elapsed = time.perf_counter() - t0

        times.append(elapsed)
        lengths.append(best_len)

        if verbose:
            print(f"  → {elapsed:.2f}s  |  path length: {best_len:.2f}")

    return process_counts, times, lengths
