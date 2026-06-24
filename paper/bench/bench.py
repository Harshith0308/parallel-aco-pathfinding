"""
Unified benchmark runner for the ACO parallelization study.

Drives BOTH implementations across configurations and writes a single tidy CSV
plus a platform-info file for reproducibility:

  * Python multiprocessing  (aco_grid.ACOPathfinder, process-based)
  * C / OpenMP              (./aco_bench, thread-based shared memory)

Phases
------
  A  Strong scaling : fixed workload, sweep worker/thread count (-> speedup).
  B  Quality vs density : fixed workers, sweep obstacle density (-> path length).

Each (impl, workers, repeat) is recorded as one row. A warm-up run is discarded
and every config is repeated so the plots can show mean +/- 95% CI.

Usage
-----
  python bench.py            # full run
  python bench.py --quick    # fast smoke run (small sweep, few repeats)
"""

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))   # main project dir
sys.path.insert(0, ROOT)

import multiprocessing as mp                                  # noqa: E402
from aco_grid import Grid, ACOPathfinder                      # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")
# Columns emitted by the C binary (order matters — must match aco_bench.c).
C_COLS = ["impl", "N", "density", "n_ants", "n_iters", "threads",
          "repeat", "total_s", "per_iter_ms", "best_length",
          "valid_last", "reached"]
# Final CSV adds a phase tag ("A" scaling, "B" density).
CSV_COLS = C_COLS + ["phase"]


# ---------------------------------------------------------------------------
# Platform / reproducibility info
# ---------------------------------------------------------------------------

def _cmd(args):
    try:
        return subprocess.check_output(args, stderr=subprocess.STDOUT,
                                       text=True).strip()
    except Exception:
        return "n/a"


def capture_platform():
    info = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "cpu": platform.processor() or "n/a",
        "machine": platform.machine(),
        "logical_cores": mp.cpu_count(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python": platform.python_version(),
        "numpy": _np_version(),
        "gcc": _cmd(["gcc", "--version"]).splitlines()[0] if _cmd(["gcc", "--version"]) != "n/a" else "n/a",
    }
    return info


def _np_version():
    try:
        import numpy
        return numpy.__version__
    except Exception:
        return "n/a"


# ---------------------------------------------------------------------------
# C / OpenMP runner
# ---------------------------------------------------------------------------

def _bin_path():
    for name in ("aco_bench.exe", "aco_bench"):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("aco_bench not built — run: bash build.sh")


def run_c(N, density, ants, iters, threads, repeats, warmup,
          alpha=1.0, beta=2.5, rho=0.10, seed=42, grid_file=None):
    cmd = [_bin_path(),
           "--N", str(N), "--density", str(density), "--ants", str(ants),
           "--iters", str(iters), "--threads", str(threads),
           "--repeats", str(repeats), "--warmup", str(warmup),
           "--alpha", str(alpha), "--beta", str(beta), "--rho", str(rho),
           "--seed", str(seed)]
    if grid_file:
        cmd += ["--grid", grid_file]
    out = subprocess.check_output(cmd, text=True)
    rows = []
    for line in out.strip().splitlines():
        f = line.split(",")
        rows.append(dict(zip(C_COLS, f)))
    return rows


# ---------------------------------------------------------------------------
# Shared-grid I/O — lets both back-ends solve the IDENTICAL instance
# ---------------------------------------------------------------------------

def write_grid_file(grid, path):
    with open(path, "w") as f:
        f.write(f"{grid.N} {grid.start[0]} {grid.start[1]} "
                f"{grid.goal[0]} {grid.goal[1]}\n")
        for r in range(grid.N):
            f.write("".join("1" if grid.grid[r, c] else "0"
                            for c in range(grid.N)) + "\n")


def load_py_grid(path, density):
    import numpy as np
    with open(path) as f:
        N, sr, sc, gr, gc = map(int, f.readline().split())
        cells = np.array([[1 if ch == "1" else 0 for ch in f.readline().strip()]
                          for _ in range(N)], dtype=np.int8)
    g = Grid.__new__(Grid)
    g.N = N
    g.obstacle_density = density
    g.start = (sr, sc)
    g.goal = (gr, gc)
    g.grid = cells
    return g


def make_feasible_grid(N, density, seed0, path, max_tries=400):
    """Find a grid at the EXACT requested density that has a start->goal path
    (scanning seeds), write it to `path`, and return (feasible, seed_used)."""
    for k in range(max_tries):
        g = Grid(N, obstacle_density=density, seed=seed0 + k)
        if g.has_path():
            write_grid_file(g, path)
            return True, seed0 + k
    return False, None


# ---------------------------------------------------------------------------
# Python multiprocessing runner
# ---------------------------------------------------------------------------

def run_py(N, density, ants, iters, workers, repeats, warmup,
           parallel=True, alpha=1.0, beta=2.5, rho=0.10, seed=42,
           grid_file=None):
    rows = []
    for rep in range(repeats + warmup):
        # Shared instance when provided; otherwise generate (Phase A workload
        # is feasible by construction). No silent density-lowering fallback.
        grid = load_py_grid(grid_file, density) if grid_file \
            else Grid(N, obstacle_density=density, seed=seed)
        aco = ACOPathfinder(grid, n_ants=ants, n_iterations=iters,
                            alpha=alpha, beta=beta, rho=rho,
                            n_processes=workers)
        t0 = time.perf_counter()
        aco.run(parallel=parallel, verbose=False)
        total = time.perf_counter() - t0
        if rep < warmup:
            continue
        per_iter_ms = (sum(aco.iteration_times) / len(aco.iteration_times)) * 1000.0
        reached = 1 if aco.best_length != float("inf") else 0
        rows.append({
            "impl": "py_mp" if parallel else "py_serial",
            "N": N, "density": density, "n_ants": ants, "n_iters": iters,
            "threads": workers if parallel else 1, "repeat": rep - warmup,
            "total_s": round(total, 6),
            "per_iter_ms": round(per_iter_ms, 4),
            "best_length": round(aco.best_length, 4) if reached else 0.0,
            "valid_last": "",
            "reached": reached,
        })
    return rows


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="fast smoke sweep")
    ap.add_argument("--phase", choices=["A", "B", "both"], default="both",
                    help="run only one phase (merges with existing raw.csv)")
    ap.add_argument("--out", default=RESULTS)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cores = mp.cpu_count()

    if args.quick:
        N, density, ants, iters = 32, 0.20, 60, 30
        thread_list = [1, 2, 4]
        repeats, warmup = 2, 1
        densities = [0.10, 0.20, 0.30]
        q_iters = 30
    else:
        N, density, ants, iters = 48, 0.20, 200, 100
        thread_list = sorted({1, 2, 4, 8, 12, min(16, cores), cores})
        thread_list = [t for t in thread_list if t <= cores]
        repeats, warmup = 5, 1
        densities = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
        q_iters = 80

    plat = capture_platform()
    with open(os.path.join(args.out, "platform.json"), "w") as f:
        json.dump(plat, f, indent=2)
    print("Platform:", json.dumps(plat, indent=2))

    csv_path = os.path.join(args.out, "raw.csv")
    rows = []

    def tag(new_rows, phase):
        for r in new_rows:
            r["phase"] = phase
        return new_rows

    # ---- Phase A: strong scaling ----
    if args.phase in ("A", "both"):
        print(f"\n[Phase A] strong scaling  N={N} density={density} "
              f"ants={ants} iters={iters} repeats={repeats}")
        print("  C/OpenMP serial baseline (1 thread) + thread sweep ...")
        for t in thread_list:
            print(f"    C  threads={t}")
            rows += tag(run_c(N, density, ants, iters, t, repeats, warmup), "A")
        print("  Python multiprocessing process sweep ...")
        for w in thread_list:
            print(f"    PY threads={w}")
            rows += tag(run_py(N, density, ants, iters, w, repeats, warmup, parallel=True), "A")
        print("  Python pure-serial reference ...")
        rows += tag(run_py(N, density, ants, iters, 1, repeats, warmup, parallel=False), "A")

    # ---- Phase B: quality vs density (shared, exactly-density feasible grids) ----
    if args.phase in ("B", "both"):
        qt = min(8, cores)
        gdir = os.path.join(args.out, "grids")
        os.makedirs(gdir, exist_ok=True)
        print(f"\n[Phase B] quality vs density  (threads={qt}, iters={q_iters})")
        print("  Both back-ends solve the SAME feasible grid per density.")
        for d in densities:
            gp = os.path.join(gdir, f"grid_N{N}_d{int(round(d * 100)):02d}.txt")
            feasible, seed_used = make_feasible_grid(N, d, 1000, gp)
            if not feasible:
                print(f"    density={d:.2f}  INFEASIBLE after search -> skipped")
                continue
            print(f"    density={d:.2f}  (shared grid seed={seed_used})")
            rows += tag(run_c(N, d, ants, q_iters, qt, repeats, warmup, grid_file=gp), "B")
            rows += tag(run_py(N, d, ants, q_iters, qt, repeats, warmup,
                               parallel=True, grid_file=gp), "B")

    # ---- write CSV (merge-preserve: keep the phase we did NOT run) ----
    if args.phase != "both" and os.path.exists(csv_path):
        with open(csv_path) as f:
            kept = [r for r in csv.DictReader(f) if r.get("phase") != args.phase]
        rows = kept + rows

    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CSV_COLS})

    print(f"\nDone. {len(rows)} rows -> {csv_path}")
    print(f"Platform info  -> {os.path.join(args.out, 'platform.json')}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
