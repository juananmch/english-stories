# Level Contract Audit — Plan

Status: proposed, not started. No code written yet.

## Why this exists

The repository is in a healthy state: 60 stories across A1–C2, `validate.py`
passes with no findings, generated files are current, and the site deploys on
every push. The original scope is complete.

The problem is not what the project produces — it is what the project
*measures*.

Level is controlled on two axes, vocabulary and grammar. Above B1, both have
quietly stopped doing work:

- `grammar_banned` is empty at B2, C1 and C2. Nothing is checked.
- The assumed-known vocabulary is far below real CEFR inventories, and the gap
  widens as the level rises.

| Level | Own list | Cumulative assumed-known | Typical CEFR reference |
|-------|---------:|-------------------------:|------------------------|
| A1    |      756 |                      756 | ~500–1,000 — good      |
| A2    |      743 |                    1,423 | ~1,500–2,500 — close   |
| B1    |      549 |                    1,931 | ~2,500–3,500 — low     |
| B2    |      443 |                    2,368 | ~4,000–6,000 — very low|
| C1    |      688 |                    3,053 | ~8,000+ — far too low  |
| C2    |        0 |        ceiling disabled  | —                      |

Per-level contribution runs 756 → 743 → 549 → 443 → 688. Real vocabulary growth
accelerates with level; this decelerates exactly where it should accelerate.
`CLAUDE.md` already warns that B1/B2/C1 are "starter lists, not real level
inventories." That warning is still accurate, and now quantified.

A second measurement confirms the diagnosis from another direction:

| Level | Mean sentence length | Distinct lemmas | Type-token ratio |
|-------|---------------------:|----------------:|-----------------:|
| A1    |                  8.2 |             123 |             0.49 |
| A2    |                  9.0 |             169 |             0.57 |
| B1    |                 12.8 |             211 |             0.56 |
| B2    |                 17.8 |             264 |             0.55 |
| C1    |                 27.5 |             296 |             0.53 |
| C2    |                 35.8 |             316 |             0.57 |

Sentence length more than quadruples from A1 to C2 while type-token ratio stays
flat at roughly 0.55 throughout. **The levels are differentiated by syntax, not
by vocabulary** — and syntax is the one axis the validator does not measure at
all.

The words the upper levels *teach* are well chosen (`precariousness`,
`complicity`, `conscientious`, `preemptively`, `capitulation`). The problem is
the substrate beneath them: a C1 story is roughly 545 words drawn from a
3,053-word universe with eight advanced words placed on top. That is B1-texture
prose wearing C1 vocabulary. Real C1 difficulty is diffuse — collocation,
register, idiom, syntactic density, and the fact that any of ~8,000 words may
appear unannounced.

## Decisions

These were settled deliberately and should not be revisited without a reason.

1. **Target real CEFR inventory sizes** (~3,000 / ~5,000 / ~8,000 cumulative at
   B1/B2/C1), accepting that the vocabulary ceiling stops constraining anything
   at C1. A contract that passes trivially is honest. A contract that bites by
   keeping the reader's assumed vocabulary artificially small enforces the wrong
   thing.
2. **Thresholds are set a priori**, never calibrated from the existing corpus.
   Calibrating to current output would encode the flat lexical profile that this
   work exists to fix, and turn the validator into a rubber stamp.
3. **No grandfathering.** Stories broken by the expanded lists get fixed. An
   exemption list is precisely the "weaken the contract to silence the validator"
   failure that `CLAUDE.md` names as the one rule that matters most.
4. **Smaller glossaries are a correct outcome.** A C1 story that teaches four
   genuinely C1 words instead of eight padded ones is a better story.
5. **New checks ship as warnings first.** Not a softening of decision 2 — the
   targets stay a priori — but the blast radius is currently unknown, and the
   difference between "ten stories need a paragraph reworked" and "thirty need
   regenerating" should be measured before it is enforced.
6. **Bottom-up, one level at a time.** B1's expansion cascades into B2 and C1,
   so fixing B1 first means B2's findings are real rather than downstream noise.

## Workstreams

### 1. Per-story review decks

Independent of everything else — it only reads data that already exists and is
already validated. Sequenced first as a short, self-contained win.

Cloze cards built from each story's own sentences: the sentence with the taught
word blanked, flipping to reveal the definition. `site.py` already locates every
taught word in the prose via `find_spans` for the tap-to-reveal feature, so the
source sentence is already identified.

Stateless — no progress tracking, no `localStorage`, no scheduling. Per-story
decks are short enough that scheduling adds little, and statelessness sidesteps
the fact that a static site cannot sync between devices.

Proposed placement: a `## Review` section appended to each generated story page,
built as progressive enhancement and hidden when JavaScript is unavailable. No
new route, no new navigation, no change to the level or home pages.

### 2. Test suite

There are currently **no tests** — 1,354 lines across `validate.py`, `build.py`,
`lexicon.py` and `site.py`, and not one test file. CI runs the validator against
the stories, which checks content, not tooling. A mis-stem in the lemmatizer
does not fail anything; it silently mis-classifies a word, and every downstream
check trusts the result.

This is a prerequisite for workstream 3, which pushes roughly 10,000 words
through a lemmatizer whose suffix rules were tuned against ~750 curated ones.

Scope: `lexicon.py` lemmatization and the `validate.py` vocabulary checks
(`ceiling`, `known`, `reteach`, `teach-late`, `glossary`). Standard library
`unittest` only — the zero-dependency promise holds. Not the site renderer.

### 3. The wordlist audit

Bottom-up: expand B1 → validate → fix B1 stories → B2 → C1.

**Source data.** SUBTLEX-US, vendored into the repository as a lemma-rank file.
Subtitle-corpus frequencies match this project's register — adult everyday
situations, heavy dialogue — better than a web- or book-derived list would.
Vendoring a top-15k slice costs on the order of 150KB and keeps the "plain
Python 3, nothing to install" promise intact; a `pip` dependency would break it.

Licensing is clear: the `words/subtlex-word-frequencies` repackaging (74,286
words) is ISC-licensed, and Marc Brysbaert has granted permission to distribute
the SUBTLEX-US lists for any purpose, not only academic use, as documented by
the `wordfreq` project. The vendored file must carry attribution to Brysbaert &
New (2009).

**Lemmatization.** SUBTLEX entries are surface forms; the wordlists are lemmas.
The frequency slice has to pass through `lexicon.py`'s lemmatizer and then a
manual curation pass — at 10k scale the suffix rules will produce junk, and
frequency is a proxy for level, not a synonym for it (`nevertheless` is frequent
and is not A2).

**Two new checks**, both warning-level initially:

- *Lexical band* — share of prose tokens falling outside the top-2,000 frequency
  band. This measures the actual defect (thin substrate) rather than the thing
  that is already fine (glossary word choice).
- *Sentence length* — a per-level band with both a floor and a ceiling. This is
  the axis genuinely carrying the level distinctions today, and it is currently
  unbounded in both directions. Implementing it needs a better sentence splitter
  than a naive `[.!?]` split: dialogue, abbreviations and ellipses all need
  handling.

**A soft floor on new words per story** (warning at fewer than ~3). The budget is
currently a cap with no minimum. Once base lists expand, glossaries shrink; a
story teaching one word is not broken, but it signals that vocabulary targeting
drifted and that should be visible rather than silent.

**C2** keeps its ceiling disabled and no base list. With the two new axes in
place it has a real measurable identity — the highest share of low-frequency
vocabulary and the densest syntax — without needing a base list that would be
most of the language anyway.

### 4. New stories

Only after a level's list is trustworthy. A1 and A2 are already well calibrated
and are unblocked today; B1 upward waits on workstream 3.

Growth is even across all six levels, keeping the collection symmetric.

## Proposed thresholds

Starting values, to be validated against the real distribution during the
warning phase before anything is enforced.

Lexical band — share of prose tokens outside the top 2,000, excluding registered
proper names:

| Level | Target |
|-------|-------:|
| A1    |    ≤ 5% |
| A2    |    ≤ 8% |
| B1    |  8–13% |
| B2    | 12–18% |
| C1    | 16–24% |
| C2    |  ≥ 20% |

Mean sentence length:

| Level | Target | Measured today |
|-------|-------:|---------------:|
| A1    |   6–11 |            8.2 |
| A2    |   8–13 |            9.0 |
| B1    |  11–16 |           12.8 |
| B2    |  14–20 |           17.8 |
| C1    |  18–26 |           27.5 |
| C2    |  20–30 |           35.8 |

C1 and C2 sit above the proposed ceiling. That is deliberate and corrective:
35.8 words per sentence is not sophistication, it is overwriting. Proficient
English prose generally runs 20–25.

## Known risks

- **Blast radius is unmeasured.** Expanding the base lists will reclassify
  currently-taught words (`sacred`, `commission`, `premise`, `initiative`,
  `functional`, `diagnosis`, `hazard`, `facility`) as already-known, failing the
  `known` check. Rough estimate: 10–25 of C1's 77 taught words, with similar
  proportions at B1 and B2. The lexical-band check may fail stories on prose
  texture, which means rewriting passages rather than editing word lists —
  potentially most of B2/C1/C2, around 30 stories. This is why the new checks
  ship as warnings.
- **Frequency is not level.** The curation pass is not optional.
- **The lemmatizer is unproven at scale.** Workstream 2 exists to de-risk this.

## Explicitly not doing

- Distribution, SEO, or a public audience push. This is a personal project,
  shared with a few friends at most.
- Progress tracking, accounts, or cross-device sync. Static site, no backend.
- Spaced repetition. Revisit only if the stateless decks prove useful in practice.
- A GitFlow `develop` branch. For a solo repository with one deploy target,
  `feature/*` branches off `main` are enough, and `validate.yml` already runs on
  all branches while `pages.yml` deploys only from `main`.
