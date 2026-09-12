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
- Created `feature/level-contract-audit` off `main`.

### Workstream 1 — review decks (same day, later)

- Built per-story cloze review decks in `site.py`, test-first. 17 tests in
  `tests/test_site.py`, all green; CI now runs them before the validator.
- Each card is a `<details>` block: the sentence where the reader first met the
  word, with the word blanked. Opening it fills the blank from `data-answer` via
  CSS `::after` and shows the definition — no script at all. Deviates from the
  plan's "progressive enhancement, hidden without JS" toward strictly better:
  works everywhere.
- Sentence splitting had to be quote-aware. The corpus uses straight `"` only,
  17 `Mr.`/`Ms.` abbreviations, and quotations that span sentences. A boundary
  now requires the next sentence to visibly start (capital or opening quote)
  and an even quote count, so `"Welcome!" she said.` and `"We have a backup.
  It takes a minute."` each stay whole.
- Coverage on the real corpus: 499 of 500 taught words get a card.
- Fixed a pre-existing `find_spans` bug found along the way: hyphenated entries
  (`second-guess`, `single-handedly`) were never located because the tokenizer
  splits on the hyphen. They now match as phrases, which also means they are
  marked in the prose on the live site for the first time.
- The one remaining miss is `glass` in `A1/07`: the prose says `glasses`, which
  is itself an A1 headword (eyewear), so the lemmatizer stops there. The
  validator and the site disagree on this word — a real inconsistency, and a
  content question rather than a tool bug. Left for the audit.
- Verified visually in the browser: dark and light themes, desktop and mobile,
  reveal interaction. Added `.claude/launch.json` so the preview tool can serve
  `_site/`.
- Also confirmed the plan's sentence-length concern with real specimens: C2
  sentences of 74–92 words surfaced as cloze prompts.

**Pending next:** workstream 2 — test suite for `lexicon.py` lemmatization and
the `validate.py` vocabulary checks, before touching any wordlist.
