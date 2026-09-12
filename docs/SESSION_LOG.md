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

### Workstream 2, part 1 — lemmatizer tests and fixes (same day, later)

- `tests/test_lexicon.py`: 30 tests pinning the lemmatizer contract —
  surface-form-wins, inflections, derivations, irregulars, possessives, and
  every resolved ambiguity with its counter-case.
- Writing the characterization tests exposed how `lemma()` works: `candidates()`
  emits every matching suffix rule's stem in rule order and `lemma()` takes the
  first that is a known word. So rule order decides ties between two real
  words. A scan of the corpus for tokens with 2+ known candidates found 15,
  **8 resolving to the wrong word**: `caring`/`cared` → `car`,
  `noted`/`notes`/`noting` → `not`, `used` → `us`, `ones` → `on`,
  `normally` → `norm`, `informally` → `inform`, `professionally` → `profession`.
- Three ordering fixes (commit `8fc6428`): silent-e base before bare stem after
  a vowel suffix when the stem is CVC; `-s` before `-es`; `-ly` before `-ally`.
  All 15 ambiguities now resolve correctly. Validator still passes.
- One prospective fix (commit `1494a1a`): a one-syllable CVC stem is never
  offered as the base of a vowel-suffixed word, since such a base would have
  doubled its consonant (`hop` → `hopping`). This closes the
  `forest` → `for` / `scared` → `scar` / `caring` → `car`-when-`care`-unknown
  class of silent false negative *before* the wordlists grow enough to trigger
  it. Verified to change no lemma in today's corpus.
- **Known limitation, not fixable in the tool:** when a legitimate word is
  absent from the vocabulary and a shorter word it strips down to is present,
  it still collapses (`evening` → `even`, `department` → `depart`). The
  only real guard is wordlist completeness — every legitimate word present as
  its own headword. This is an argument *for* the audit, and the audit's
  curation pass should watch for it.
- `lives` → `life` remains: verb vs. plural noun is undecidable without
  part-of-speech tagging; both are A1 so it cannot affect a level judgment.
- Pushed workstream 1 after the `gh` token gained the `workflow` scope.

### Workstream 2, part 2 — validator tests (same day, later)

- `tests/test_validate.py`: 28 tests for the six vocabulary checks. Each test
  writes a tiny repository (two wordlists, a cast, one or two stories) to a
  temp dir, points `lx.ROOT` / `lx.WORDLIST_DIR` at it and calls `check_level`
  with an inline config. No change to `validate.py` was needed.
- Being characterization tests they were green on first run, so the "red"
  phase was a mutation check instead: disabling each check in turn
  (`ceiling`, `budget`, `glossary`, `reteach`, `teach-late`, `known`) makes
  2–4 tests fail. All six confirmed.
- Two facts about the validator worth knowing, now pinned by tests:
  - `reteach` at the same level always arrives with `teach-late` — a word
    taught earlier necessarily appeared earlier.
  - **Declaring a different surface form evades `known` and `reteach`.**
    `cats` next to a known `cat` is not caught, because the declared surface
    is itself vocabulary and a known surface beats a stem. A corpus scan found
    33 glossary entries that survive only because of this: mostly legitimate
    distinct items (`shower`/`show`, `friendly`/`friend`, `trainer`/`train`,
    `dealer`, `foreigner`, `disagreement`, `documentation`, `valuation`,
    `bewilderment`), plus a debatable band of participial adjectives
    (`shared`, `missing`, `qualified`, `determined`, `convinced`, `settled`,
    `entitled`, `promising`) and `-ly` adverbs of known adjectives
    (`softly`, `gradually`, `significantly`, `consistently`, `considerably`,
    `deliberately`, `implicitly`, `acutely`, `tentatively`). Not fixable in
    the tool without part-of-speech information, and the protection is doing
    real work, so this stays a **curation item for the audit**: review that
    band by hand, one level at a time.
- One more instance of the wordlist-completeness limitation: `wounded` →
  `wound` → `wind`, via the irregular-past map applied to a stem. Harmless
  today (`wounded` is declared in `C2/02`); would only bite if `wound` were
  missing from the wordlists while `wind` were present.
- Suite is now 58 tests (`test_site` 17, `test_lexicon` 13, `test_validate`
  28). Validator and `build.py --check` still clean. Workstream 2 complete.
- Correction to the part 1 entry above: `test_lexicon.py` has 13 tests
  carrying 72 assertions, not "30 tests".

**Pending next:** workstream 3 at B1 — vendor a SUBTLEX-US lemma-rank slice
(with Brysbaert & New 2009 attribution), lemmatize and curate, expand B1,
validate, fix B1 stories; then the lexical-band and sentence-length warnings
with the a priori thresholds from `docs/PLAN.md`. Include the 33-entry
surface-form list above in the B1 curation pass.
