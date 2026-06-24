# Related Work matrix

One row per paper you read. Fill the columns as you go — the last two columns are
the raw material for your Related Work prose and for positioning your contribution.
When done, add a verified BibTeX entry for each to `../tex/refs.bib` and cite it.

**Bucket** = `FND` (foundational ACO) · `PAR` (parallel/GPU ACO) · `APP` (ACO path planning) · `PERF` (performance modeling)

| # | Bucket | Citation key | Authors (year) | Venue | Core idea | Parallel platform (if any) | Reported speedup / result | How it differs from ours | Read? |
|---|--------|--------------|----------------|-------|-----------|----------------------------|---------------------------|--------------------------|-------|
| 1 | FND | dorigo1996ant | Dorigo et al. (1996) | IEEE T-SMC-B | Original Ant System | — | — | We use AS-style update; not a contribution | ✓ |
| 2 | PAR | randall2002parallel | Randall & Lewis (2002) | JPDC | Parallel ACO taxonomy + impl | (fill) | (fill) | They propose a parallel impl; we *compare execution models* | ☐ |
| 3 | PAR | (key) | Pedemonte et al. (2011) | Applied Soft Comput. | Survey of parallel ACO | — | — | Survey; we add an empirical process-vs-thread study | ☐ |
| 4 |  |  |  |  |  |  |  |  | ☐ |
| 5 |  |  |  |  |  |  |  |  | ☐ |
| 6 |  |  |  |  |  |  |  |  | ☐ |
| 7 |  |  |  |  |  |  |  |  | ☐ |
| 8 |  |  |  |  |  |  |  |  | ☐ |
| 9 |  |  |  |  |  |  |  |  | ☐ |
| 10 |  |  |  |  |  |  |  |  | ☐ |
| 11 |  |  |  |  |  |  |  |  | ☐ |
| 12 |  |  |  |  |  |  |  |  | ☐ |
| 13 |  |  |  |  |  |  |  |  | ☐ |
| 14 |  |  |  |  |  |  |  |  | ☐ |
| 15 |  |  |  |  |  |  |  |  | ☐ |

## The one-sentence positioning (write this after the matrix)

> Unlike prior parallel-ACO work that ____________, and unlike path-planning ACO
> work that ____________, we ____________ (hold the algorithm fixed and compare
> process- vs thread-based execution on identical instances).

Fill the blanks from the "How it differs" column — that sentence goes near the end
of your Introduction and Related Work.
