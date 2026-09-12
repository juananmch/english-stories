# Session Log

Working log for this repository. Newest entry first. Read this before starting a
session to recover context.

## 2026-09-12

- Audited the repo's actual state rather than its documented state. Validator
  passes (60 stories, no findings), generated files current, CI green. Original
  scope (A1–C2, 10 stories each, published site) is complete.
- Measured the vocabulary universe per level: cumulative assumed-known runs
  756 / 1,423 / 1,931 / 2,368 / 3,053 for A1–C1, against real CEFR inventories
  of roughly 750 / 2,000 / 3,000 / 5,000 / 8,000. Well calibrated at A1/A2,
  progressively under-built above. `CLAUDE.md`'s "starter lists" warning for
  B1/B2/C1 is still accurate.
- Measured syntax: mean sentence length 8.2 → 35.8 words A1→C2 while type-token
  ratio stays flat at ~0.55. Levels are differentiated by syntax, which the
  validator does not check, not by vocabulary, which it does.
- Found the upper-level *taught* words are well chosen; the defect is the thin
  prose substrate beneath them.
- Found zero tests across 1,354 lines of tooling.
- Confirmed SUBTLEX-US is safe to vendor (ISC repackaging; Brysbaert's
  any-purpose redistribution permission).
- Decided the program of work and wrote it up in `docs/PLAN.md`: review decks →
  test suite → wordlist audit (bottom-up, warnings first, no grandfathering) →
  new stories at every level.
- Created `feature/level-contract-audit` off `main`. No code changes yet.

**Pending next:** start workstream 1 (per-story cloze review decks in `site.py`).
