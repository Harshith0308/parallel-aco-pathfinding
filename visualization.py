"""
Visualization utilities for ACO grid path planning.
Group 2 - Parallel and Distributed Computing
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec


# ---------------------------------------------------------------------------
# Colour constants
# ---------------------------------------------------------------------------
C_FREE     = [0.94, 0.94, 0.94]
C_OBSTACLE = [0.18, 0.18, 0.18]
C_START    = [0.10, 0.72, 0.10]
C_GOAL     = [0.85, 0.15, 0.15]
C_PATH     = [0.20, 0.47, 0.90]


# ---------------------------------------------------------------------------
# Individual plots
# ---------------------------------------------------------------------------

def plot_grid(grid, path=None, title="Grid", ax=None, show=True, save_path=None):
    """Grid display: free cells, obstacles, start, goal, and optional path."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(7, 7))

    N = grid.N
    img = np.array([[C_FREE if grid.grid[r, c] == 0 else C_OBSTACLE
                     for c in range(N)] for r in range(N)], dtype=float)

    sr, sc = grid.start
    gr, gc = grid.goal
    img[sr, sc] = C_START
    img[gr, gc] = C_GOAL

    if path:
        for r, c in path:
            if (r, c) not in (grid.start, grid.goal):
                img[r, c] = C_PATH

    ax.imshow(img, origin="upper", interpolation="nearest")

    # Thin grid lines
    for i in range(N + 1):
        ax.axhline(i - 0.5, color="gray", lw=0.25, alpha=0.4)
        ax.axvline(i - 0.5, color="gray", lw=0.25, alpha=0.4)

    if path and len(path) > 1:
        rows = [p[0] for p in path]
        cols = [p[1] for p in path]
        ax.plot(cols, rows, color=C_PATH, lw=2.2, alpha=0.85, zorder=3)

    ax.plot(sc, sr, "o", color=C_START, ms=9, zorder=4)
    ax.plot(gc, gr, "o", color=C_GOAL,  ms=9, zorder=4)

    legend_handles = [
        mpatches.Patch(facecolor=C_FREE,     edgecolor="gray", label="Free"),
        mpatches.Patch(facecolor=C_OBSTACLE,               label="Obstacle"),
        mpatches.Patch(facecolor=C_START,                  label="Start"),
        mpatches.Patch(facecolor=C_GOAL,                   label="Goal"),
    ]
    if path:
        legend_handles.append(mpatches.Patch(facecolor=C_PATH, label="Best Path"))
    ax.legend(handles=legend_handles, loc="upper right", fontsize=8)

    ax.set_title(title, fontweight="bold")
    ax.set_xticks([])
    ax.set_yticks([])

    if standalone:
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        plt.close()


def plot_pheromone_heatmap(grid, pheromone, path=None,
                            title="Pheromone Heatmap",
                            ax=None, show=True, save_path=None):
    """Heatmap of pheromone trails with obstacle overlay and best-path line."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(7, 7))

    masked = pheromone.copy().astype(float)
    masked[grid.grid == 1] = np.nan

    cmap = plt.cm.YlOrRd.copy()
    cmap.set_bad("black", 1.0)

    im = ax.imshow(masked, cmap=cmap, origin="upper", interpolation="nearest")
    plt.colorbar(im, ax=ax, label="Pheromone level", shrink=0.85)

    sr, sc = grid.start
    gr, gc = grid.goal
    ax.plot(sc, sr, "*", color=C_START, ms=14, zorder=5, label="Start")
    ax.plot(gc, gr, "*", color=C_GOAL,  ms=14, zorder=5, label="Goal")

    if path and len(path) > 1:
        rows = [p[0] for p in path]
        cols = [p[1] for p in path]
        ax.plot(cols, rows, color="dodgerblue", lw=2.5, alpha=0.9,
                label="Best Path", zorder=4)

    ax.set_title(title, fontweight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc="upper right", fontsize=9)

    if standalone:
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        plt.close()


def plot_convergence(history, title="Convergence Rate",
                     label="Run", color="steelblue",
                     ax=None, show=True, save_path=None):
    """Best path length per iteration."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(9, 4))

    finite = [v for v in history if v != float("inf")]
    plot_y = [v if v != float("inf") else None for v in history]
    iters  = range(1, len(history) + 1)

    ax.plot(iters, plot_y, color=color, lw=1.8, alpha=0.9, label=label)

    if finite:
        best = min(finite)
        # Find first iteration where best was achieved
        first_best = next(i + 1 for i, v in enumerate(history) if v == best)
        ax.axhline(best, color="tomato", ls="--", lw=1.5, alpha=0.8,
                   label=f"Best = {best:.2f} (iter {first_best})")

    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Best Path Length", fontsize=11)
    ax.set_title(title, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    if standalone:
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        plt.close()


# ---------------------------------------------------------------------------
# Composite dashboard
# ---------------------------------------------------------------------------

def plot_full_results(aco, title_prefix="ACO Results",
                      save_path=None, show=True):
    """
    2×2 dashboard:
      [0,0] Grid + best path
      [0,1] Pheromone heatmap (final)
      [1,0] Convergence curve
      [1,1] Pheromone evolution: early snapshot vs final
    """
    fig = plt.figure(figsize=(16, 13))
    gs  = GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.28)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])

    plot_grid(aco.grid, path=aco.best_path,
              title="Grid & Best Path", ax=ax1, show=False)

    plot_pheromone_heatmap(aco.grid, aco.pheromone, path=aco.best_path,
                            title="Pheromone Heatmap (Final)",
                            ax=ax2, show=False)

    plot_convergence(aco.convergence_history,
                     title="Convergence Rate",
                     ax=ax3, show=False)

    # Pheromone evolution panel
    if len(aco.pheromone_history) >= 2:
        inner = gs[1, 1].subgridspec(1, 2, wspace=0.35)
        ax4a  = fig.add_subplot(inner[0, 0])
        ax4b  = fig.add_subplot(inner[0, 1])

        cmap = plt.cm.YlOrRd.copy()
        cmap.set_bad("black", 1.0)

        for ax_evo, (snap_iter, snap_ph) in [
            (ax4a, aco.pheromone_history[0]),
            (ax4b, aco.pheromone_history[-1]),
        ]:
            masked = snap_ph.copy().astype(float)
            masked[aco.grid.grid == 1] = np.nan
            ax_evo.imshow(masked, cmap=cmap, origin="upper", interpolation="nearest")
            ax_evo.set_title(f"Pheromone\nIter {snap_iter}", fontsize=10)
            ax_evo.set_xticks([])
            ax_evo.set_yticks([])
    else:
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis("off")
        ax4.text(0.5, 0.5, "Not enough history snapshots",
                 ha="center", va="center", transform=ax4.transAxes)

    fig.suptitle(title_prefix, fontsize=15, fontweight="bold", y=0.99)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# Evaluation plots
# ---------------------------------------------------------------------------

def plot_density_evaluation(densities, results, save_path=None, show=True):
    """Bar/line charts: path length and success rate vs obstacle density."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    valid_d = [d for d in densities if results[d]["length"] != float("inf")]
    valid_l = [results[d]["length"] for d in valid_d]
    valid_e = [results[d]["std"]    for d in valid_d]

    ax = axes[0]
    ax.errorbar(valid_d, valid_l, yerr=valid_e,
                fmt="bo-", lw=2, ms=7, capsize=4)
    ax.set_xlabel("Obstacle Density", fontsize=12)
    ax.set_ylabel("Mean Best Path Length", fontsize=12)
    ax.set_title("Path Length vs Obstacle Density", fontweight="bold")
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    success = [results[d]["success_rate"] for d in densities]
    ax.bar(densities, success, width=0.025, color="steelblue", alpha=0.8)
    ax.set_xlabel("Obstacle Density", fontsize=12)
    ax.set_ylabel("Path-Found Rate", fontsize=12)
    ax.set_title("Success Rate vs Obstacle Density", fontweight="bold")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close()


def plot_parallel_speedup(process_counts, times, save_path=None, show=True):
    """Actual vs ideal linear speedup."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    base = times[0]
    speedups = [base / t for t in times]

    ax = axes[0]
    ax.plot(process_counts, times, "ro-", lw=2, ms=8)
    ax.set_xlabel("Processes", fontsize=12)
    ax.set_ylabel("Wall-clock Time (s)", fontsize=12)
    ax.set_title("Execution Time vs Processes", fontweight="bold")
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(process_counts, speedups, "bo-", lw=2, ms=8, label="Actual")
    ax.plot(process_counts, [p / process_counts[0] for p in process_counts],
            "g--", lw=1.5, alpha=0.7, label="Ideal linear")
    ax.set_xlabel("Processes", fontsize=12)
    ax.set_ylabel("Speedup", fontsize=12)
    ax.set_title("Parallel Speedup (Amdahl)", fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close()
