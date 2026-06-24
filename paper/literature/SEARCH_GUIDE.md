# Literature search guide

A step-by-step process for building the Related Work section. The goal is
**~15–20 references you have actually read**, in two buckets:

1. **ACO for robot / grid path planning** (the application)
2. **Parallel / multi-core / GPU ACO** (your contribution's context)

> Do NOT cite anything you have not opened and skimmed. Reviewers check. A wrong
> or hallucinated citation is an instant credibility hit.

---

## 1. Where to search

| Source | Use it for |
|---|---|
| **Google Scholar** (scholar.google.com) | broad discovery, "cited by", BibTeX export |
| **IEEE Xplore** | the venues you're targeting; clean BibTeX + DOI |
| **ACM Digital Library** | parallel-computing papers |
| **Semantic Scholar** | "influential citations", TLDR summaries |
| **Connected Papers** (connectedpapers.com) | visual graph from one seed paper — great for finding neighbours |
| **arXiv** (cs.DC, cs.NE, cs.RO) | preprints, open access |

Tip: find one strong recent survey, then mine its reference list and its
"cited by" — this snowballs a reading list fast.

## 2. Search queries (copy-paste)

Application bucket:
- `ant colony optimization path planning grid`
- `ACO mobile robot path planning obstacle avoidance`
- `ant colony optimization global path planning survey`

Parallel bucket:
- `parallel ant colony optimization survey`
- `ant colony optimization OpenMP multicore`
- `ant colony optimization GPU CUDA`
- `parallelization strategies ant colony optimization`

Add `after:2018` in Google Scholar to surface recent work; keep a few seminal
older papers too.

## 3. Seed reading list (verify every detail before citing)

These are well-known works that anchor the two buckets. **I have listed them
from memory — you MUST open each one and confirm the authors, title, venue,
year, volume, and pages before putting it in `refs.bib`.** Get the BibTeX from
the publisher/DOI, not from this file.

**Start here — a survey that is almost perfectly on-topic:**
- Pedemonte, Nesmachnow, Cancela — *A survey on parallel ant colony
  optimization* — Applied Soft Computing (~2011). This gives you a taxonomy of
  parallel ACO and dozens of references. Read this first; it will shape your
  Related Work structure.

Foundational ACO (some already in `refs.bib`):
- Dorigo, Maniezzo, Colorni — *Ant System* — IEEE T-SMC-B, 1996. ✓ in refs.bib
- Dorigo, Gambardella — *Ant Colony System* — IEEE T-Evol. Comput., 1997.
- Stützle, Hoos — *MAX–MIN Ant System* — FGCS, 2000. ✓ in refs.bib
- Dorigo, Birattari, Stützle — *Ant Colony Optimization* (tutorial) — IEEE
  Computational Intelligence Magazine, 2006.

Parallel / GPU ACO:
- Stützle — *Parallelization strategies for ant colony optimization* — PPSN V, 1998.
- Randall, Lewis — *A parallel implementation of ACO* — JPDC, 2002. ✓ in refs.bib
- Manfrin, Birattari, Stützle, Dorigo — *Parallel ACO for the TSP* — ANTS, 2006.
- Delévacq, Delisle, Gravel, Krajecki — *Parallel ACO on GPUs* — JPDC, ~2013.
- Cecilia, García, Nisbet, Amos, Ujaldón — *Enhancing data parallelism for ACO
  on GPUs* — JPDC, ~2013.

Path-planning-specific papers: search the application queries above and pick the
2–4 most-cited recent ones yourself — this subfield moves fast and I won't guess
specific titles.

## 4. Screening (include / exclude)

Include if the paper: (a) applies ACO to path/route planning, OR (b) parallelizes
ACO (any platform), OR (c) is a foundational/most-cited reference. Exclude if it's
unrelated ACO applications (scheduling, TSP-only) unless it's about the
*parallelization*, or low-quality/predatory venues.

Aim: ~5–7 path-planning, ~7–10 parallel-ACO, ~3–4 foundational.

## 5. Capture notes as you read

Fill in [`related_work_matrix.md`](related_work_matrix.md) — one row per paper.
The "How it differs from ours" column is the most important: it's literally the
sentences you'll write.

## 6. Turn the matrix into prose

Write Related Work **by theme, not paper-by-paper**. For each theme (foundational
ACO / parallel ACO / ACO path planning), synthesize 2–4 papers in a few sentences,
then end the paragraph by positioning *your* study against them — e.g. "unlike
[X], which proposes a new parallel variant, we hold the algorithm fixed and
compare two execution models." The `tex/main.tex` Related Work section is already
scaffolded with these three themes.

## 7. Citation hygiene

- One verified BibTeX entry per paper in `tex/refs.bib`; include the DOI.
- Prefer the publisher's BibTeX over Scholar's (Scholar sometimes mangles fields).
- Double-check author initials, year, and venue. Verify page numbers.
- Never cite a paper you couldn't access and at least skim.

## 8. Time budget

A focused day or two: ~half a day searching + screening, one day reading the top
~15 and filling the matrix, half a day writing the section. Quality over quantity.
