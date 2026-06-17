"""
Flask dev-server for the ACO Path Planner frontend.
Group 2 — Parallel and Distributed Computing

Routes
------
GET  /                    → serve frontend/index.html
POST /api/grid-preview    → generate grid, return JSON
POST /api/run             → SSE stream: runs ACO, pushes progress events
"""

import json
import queue
import threading

import numpy as np
from flask import Flask, Response, jsonify, request, send_from_directory

from aco_grid import Grid, ACOPathfinder

app = Flask(__name__, static_folder="frontend", static_url_path="")


# ---------------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


# ---------------------------------------------------------------------------
# Grid preview
# ---------------------------------------------------------------------------

@app.route("/api/grid-preview", methods=["POST"])
def grid_preview():
    d       = request.get_json(force=True)
    N       = int(d.get("N", 20))
    density = float(d.get("density", 0.2))
    seed    = int(d.get("seed", 42))

    grid = Grid(N, obstacle_density=min(density, 0.6), seed=seed)

    return jsonify({
        "cells":       grid.grid.tolist(),
        "start":       list(grid.start),
        "goal":        list(grid.goal),
        "has_path":    grid.has_path(),
        "n_obstacles": int(grid.grid.sum()),
    })


# ---------------------------------------------------------------------------
# ACO run — SSE
# ---------------------------------------------------------------------------

@app.route("/api/run", methods=["POST"])
def run_aco():
    d = request.get_json(force=True)

    N            = int(d.get("N", 20))
    density      = float(d.get("density", 0.2))
    seed         = int(d.get("seed", 42))
    n_ants       = max(1,  int(d.get("n_ants", 30)))
    n_iters      = max(1,  int(d.get("n_iterations", 100)))
    alpha        = float(d.get("alpha", 1.0))
    beta         = float(d.get("beta",  2.5))
    rho          = float(d.get("rho",   0.1))
    parallel     = bool(d.get("parallel", True))
    dynamic      = bool(d.get("dynamic", False))
    custom_cells = d.get("cells")
    custom_start = d.get("start")
    custom_goal  = d.get("goal")

    q = queue.Queue()

    def worker():
        try:
            # ---- build grid ----
            if custom_cells is not None:
                grid                  = Grid.__new__(Grid)
                grid.N                = N
                grid.obstacle_density = density
                grid.grid             = np.array(custom_cells, dtype=np.int8)
                grid.start            = tuple(custom_start) if custom_start else (0, 0)
                grid.goal             = tuple(custom_goal)  if custom_goal  else (N - 1, N - 1)
                grid.grid[grid.start] = 0
                grid.grid[grid.goal]  = 0
            else:
                grid = Grid(N, obstacle_density=min(density, 0.6), seed=seed)

            if not grid.has_path():
                q.put({"type": "error",
                       "message": "No valid path in this grid. Try a lower density or different seed."})
                return

            # ---- send initial grid state ----
            q.put({
                "type":  "grid",
                "cells": grid.grid.tolist(),
                "start": list(grid.start),
                "goal":  list(grid.goal),
            })

            # ---- run ACO ----
            aco = ACOPathfinder(
                grid, n_ants=n_ants, n_iterations=n_iters,
                alpha=alpha, beta=beta, rho=rho,
            )

            aco.run(
                parallel=parallel,
                verbose=False,
                dynamic_obstacles=dynamic,
                dynamic_interval=25,
                progress_callback=q.put,
            )

            q.put({
                "type":        "done",
                "best_length": aco.best_length if aco.best_length != float("inf") else None,
                "best_path":   [[int(r), int(c)] for r, c in aco.best_path] if aco.best_path else None,
            })

        except Exception as exc:
            q.put({"type": "error", "message": str(exc)})
        finally:
            q.put(None)  # sentinel

    threading.Thread(target=worker, daemon=True).start()

    def stream():
        try:
            while True:
                item = q.get(timeout=300)
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
        except (GeneratorExit, Exception):
            pass

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(port=5000, threaded=True)
