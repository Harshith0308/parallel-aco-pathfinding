"""
ACO Grid-Based Robot Path Planning with Obstacles
Group 2 — Parallel and Distributed Computing

Entry point.  Runs four self-contained demos:
  1. Basic parallel ACO + full dashboard
  2. Dynamic obstacles (new walls injected mid-run)
  3. Density evaluation  (path length vs obstacle density)
  4. Parallelisation speedup  (sequential vs multi-process)

All plots are saved to ./output/.
"""

import os
import sys
from multiprocessing import freeze_support   # required on Windows

from aco_grid    import Grid, ACOPathfinder
from visualization import (plot_full_results,
                            plot_density_evaluation,
                            plot_parallel_speedup,
                            plot_convergence)
from evaluation  import evaluate_obstacle_density, evaluate_parallelization

OUTPUT = "output"


# ---------------------------------------------------------------------------
# Demo helpers
# ---------------------------------------------------------------------------

def _header(title):
    bar = "=" * 60
    print(f"\n{bar}\n  {title}\n{bar}")


def demo_basic(N=20, density=0.20, n_ants=30, n_iters=100):
    _header("Demo 1 — Basic Parallel ACO")
    print(f"Grid {N}×{N}  |  density {density}  |  {n_ants} ants  |  {n_iters} iters")

    grid = Grid(N, obstacle_density=density, seed=42)
    if not grid.has_path():
        print("  No valid path at requested density — lowering to 0.15")
        grid = Grid(N, obstacle_density=0.15, seed=42)

    print(f"  Start: {grid.start}  Goal: {grid.goal}  "
          f"Obstacles: {grid.grid.sum()}/{N*N}")

    aco = ACOPathfinder(grid, n_ants=n_ants, n_iterations=n_iters)
    aco.run(parallel=True, verbose=True)

    os.makedirs(OUTPUT, exist_ok=True)
    out = f"{OUTPUT}/demo1_basic.png"
    plot_full_results(aco,
                      title_prefix=f"Demo 1 — {N}×{N} Grid  density={density}",
                      save_path=out, show=False)
    print(f"\n  Saved → {out}")
    return aco


def demo_dynamic(N=20, density=0.15, n_ants=30, n_iters=150):
    _header("Demo 2 — Dynamic Obstacles")
    print(f"New obstacles injected every 30 iterations")

    grid = Grid(N, obstacle_density=density, seed=7)
    aco  = ACOPathfinder(grid, n_ants=n_ants, n_iterations=n_iters)
    aco.run(parallel=True, verbose=True,
            dynamic_obstacles=True, dynamic_interval=30)

    os.makedirs(OUTPUT, exist_ok=True)
    out = f"{OUTPUT}/demo2_dynamic.png"
    plot_full_results(aco,
                      title_prefix="Demo 2 — Dynamic Obstacles",
                      save_path=out, show=False)
    print(f"\n  Saved → {out}")
    return aco


def demo_density():
    _header("Demo 3 — Path Length vs Obstacle Density")
    densities = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]

    results = evaluate_obstacle_density(
        densities, N=20, n_trials=3, n_ants=25, n_iterations=80, verbose=True
    )

    print(f"\n  {'Density':>8}  {'Mean Length':>12}  {'Std':>8}  {'Success':>8}")
    print("  " + "-" * 44)
    for d in densities:
        r = results[d]
        length_str = f"{r['length']:12.2f}" if r['length'] != float('inf') else "   no path  "
        print(f"  {d:>8.2f}  {length_str}  {r['std']:>8.2f}  {r['success_rate']:>8.0%}")

    os.makedirs(OUTPUT, exist_ok=True)
    out = f"{OUTPUT}/demo3_density.png"
    plot_density_evaluation(densities, results, save_path=out, show=False)
    print(f"\n  Saved → {out}")
    return densities, results


def demo_speedup():
    _header("Demo 4 — Parallel Speedup")

    proc_counts, times, lengths = evaluate_parallelization(
        N=25, n_ants=40, n_iterations=50, verbose=True
    )

    base = times[0]
    print(f"\n  {'Processes':>10}  {'Time (s)':>10}  {'Speedup':>10}")
    print("  " + "-" * 36)
    for n, t, l in zip(proc_counts, times, lengths):
        print(f"  {n:>10}  {t:>10.2f}  {base/t:>10.2f}×")

    os.makedirs(OUTPUT, exist_ok=True)
    out = f"{OUTPUT}/demo4_speedup.png"
    plot_parallel_speedup(proc_counts, times, save_path=out, show=False)
    print(f"\n  Saved → {out}")
    return proc_counts, times


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    freeze_support()   # Windows multiprocessing guard

    print("ACO Grid-Based Robot Path Planning with Obstacles")
    print("Group 2 — Parallel and Distributed Computing")

    # Quick-run flag: python main.py --quick
    quick = "--quick" in sys.argv
    if quick:
        print("\n[Quick mode: reduced iterations for fast testing]")

    N_BASIC   = 15 if quick else 20
    ITERS     = 40  if quick else 100
    ITERS_DYN = 60  if quick else 150
    ANTS      = 20  if quick else 30

    demo_basic(N=N_BASIC, density=0.20, n_ants=ANTS, n_iters=ITERS)
    demo_dynamic(N=N_BASIC, density=0.15, n_ants=ANTS, n_iters=ITERS_DYN)

    if not quick:
        demo_density()
        demo_speedup()
    else:
        print("\n[Density & speedup evaluations skipped in quick mode]")

    print(f"\n{'='*60}")
    print(f"  Done!  All plots saved to ./{OUTPUT}/")
    print(f"{'='*60}")
