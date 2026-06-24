# Related Work matrix

The references below were located via literature search, verified, and added to
`../tex/refs.bib` with DOIs. **Before final submission, open each DOI and read at
least the abstract/intro/results of every paper you cite** — that is on you.

**Bucket** = `FND` (foundational ACO) · `PAR` (parallel/GPU ACO) · `APP` (ACO path planning) · `PERF` (performance modeling)

| # | Bucket | Citation key | Authors (year) | Venue | DOI | How it differs from ours | Read? |
|---|--------|--------------|----------------|-------|-----|--------------------------|-------|
| 1 | FND | dorigo1996ant | Dorigo, Maniezzo, Colorni (1996) | IEEE T-SMC-B | 10.1109/3477.484436 | Original Ant System; we reuse its update, not a contribution | ☐ |
| 2 | FND | dorigo1997acs | Dorigo, Gambardella (1997) | IEEE T-Evol. Comput. | 10.1109/4235.585892 | ACS variant; algorithmic, not parallel-execution focus | ☐ |
| 3 | FND | stutzle2000maxmin | Stützle, Hoos (2000) | FGCS | 10.1016/S0167-739X(00)00043-1 | MMAS variant; quality-focused | ☐ |
| 4 | FND | dorigo2004aco | Dorigo, Stützle (2004) | MIT Press (book) | — | Reference text | ☐ |
| 5 | FND | dorigo2006aco | Dorigo, Birattari, Stützle (2006) | IEEE Comp. Intell. Mag. | 10.1109/MCI.2006.329691 | Tutorial/survey | ☐ |
| 6 | APP | ali2020pathplanning | Ali, Gong, Wang, Dai (2020) | Front. Neurorobotics | 10.3389/fnbot.2020.00044 | Improves grid-path *quality* (ACO+MDP); sequential | ☐ |
| 7 | APP | li2024islands | Li, Li, Cui (2024) | Int. J. Adv. Robotic Syst. | 10.1177/17298806241278170 | Island/pheromone-init *quality* improvements; sequential | ☐ |
| 8 | PAR | pedemonte2011survey | Pedemonte, Nesmachnow, Cancela (2011) | Applied Soft Computing | 10.1016/j.asoc.2011.05.042 | Survey of parallel ACO; we add an empirical process-vs-thread study | ☐ |
| 9 | PAR | stutzle1998parallel | Stützle (1998) | PPSN V (LNCS 1498) | 10.1007/BFb0056914 | Parallel independent runs; different strategy | ☐ |
| 10 | PAR | randall2002parallel | Randall, Lewis (2002) | JPDC | 10.1006/jpdc.2002.1854 | Proposes a parallel impl; we *compare execution models* | ☐ |
| 11 | PAR | delevacq2013gpu | Delévacq et al. (2013) | JPDC | 10.1016/j.jpdc.2012.01.003 | GPU ACO (speedup ~23.6x); different platform | ☐ |
| 12 | PAR | cecilia2013enhancing | Cecilia et al. (2013) | JPDC | 10.1016/j.jpdc.2012.01.002 | GPU data-parallel ACO; different platform | ☐ |
| 13 | PAR/APP | si2024parallel | Si, Bao (2024) | Math. Biosci. Eng. | 10.3934/mbe.2024113 | Parallel ACO *for path planning* — closest work; proposes a new algorithm vs our execution-model comparison | ☐ |
| 14 | PERF | amdahl1967 | Amdahl (1967) | AFIPS | 10.1145/1465482.1465560 | Speedup bound we fit | ☐ |
| 15 | PERF | gustafson1988 | Gustafson (1988) | CACM | 10.1145/42411.42415 | Scaled-workload view | ☐ |
| 16 | PERF | dagum1998openmp | Dagum, Menon (1998) | IEEE CS&E | 10.1109/99.660313 | OpenMP model we use | ☐ |

## Positioning (already written into the paper)

> Unlike prior parallel-ACO work that proposes new parallel algorithms or targets
> GPUs, and unlike path-planning ACO work that improves solution quality on a
> sequential solver, we hold a single algorithm fixed and empirically contrast
> process- vs thread-based CPU execution on identical instances.

## Optional: add a few more

The set above is enough for a short paper. To strengthen further, search
`ant colony optimization OpenMP multicore` and add 2–3 recent multi-core CPU ACO
papers (e.g. shared-memory OpenMP studies) so your thread-based back-end has
direct comparators.
