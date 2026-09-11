# CLAUDE.md

Graded English reading stories for adult learners, organized by CEFR level
(A1–C2) and published to GitHub Pages.

The important thing to understand about this repo: a story is not free prose.
Every story is checked against a machine-readable level contract, and most of
what looks like "just writing" is actually constrained by `config/levels.json`
and `wordlists/`. Read `SPECIFICATIONS.md` before changing anything structural,
and `PROMPT.md` before writing a story.

## Workflow for adding or editing a story

```sh
python3 tools/build.py --fix-meta          # recompute word_count / new_words
python3 tools/validate.py --level A2       # check against the level contract
python3 tools/build.py                     # regenerate VOCABULARY.md + indexes
```

Iterate on `validate.py` until it reports no findings, then commit and push to
`main`. The `pages` workflow revalidates, rebuilds the site and deploys; a story
that fails the contract is never published, and the live site stays on the
previous version.

To preview the site before pushing:

```sh
python3 tools/site.py && python3 -m http.server --directory _site
```

Everything is plain Python 3 with no dependencies. There is nothing to install.

## Rules that are easy to get wrong

- **Never edit generated files by hand.** Every `README.md` (root and per level)
  and every `VOCABULARY.md` is written by `tools/build.py` and carries a
  "do not edit" header. Edit the stories, then rebuild. `_site/` is generated
  too and is gitignored.
- **Never add a word to a wordlist just to silence the validator.** Ask whether
  the word genuinely belongs to that CEFR level. If it does, adding it is a real
  correction to the level definition. If it does not, change the story instead.
  Weakening the wordlists empties the whole system of meaning — this is the one
  rule that matters most.
- **Front matter lists must not contain commas inside an entry.** `grammar:` and
  `characters:` are parsed as comma-separated, so `past simple (be, and others)`
  silently splits into two bogus entries. Keep entries short and comma-free.
- **`word_count` and `new_words` are derived.** Never write them by hand; run
  `tools/build.py --fix-meta`.
- **New characters must be registered** in `wordlists/names.txt`, or the
  validator reports the name as above level.
- **B1, B2 and C1 wordlists are starter lists, not real level inventories.**
  Expand the relevant one *before* writing stories at that level, otherwise the
  validator will report dozens of legitimate words as above level and the loop
  gets slow and noisy. A1 and A2 are complete.

## What the validator checks

Vocabulary ceiling, new-word budget, glossary coverage and definitions,
re-teaching a word, teaching a word after it already appeared, teaching a word a
lower level already assumes known, **teaching a word that is already in the
level's own base wordlist** (a level's `wordlists/<LEVEL>.txt` is what a reader
knows *before* any story at that level — declaring one of those words as a
story's own "New Word" is a contradiction, not a level-appropriate choice),
prose length, declared and banned grammar, US English spelling, and
front-matter consistency. `SPECIFICATIONS.md` explains each one and why it
exists.

## Conventions

- **US English** everywhere, spelling and vocabulary. The British→US map lives
  in the `us_english` section of `config/levels.json`.
- **Audience is adults, roughly 20–45.** Everyday adult situations — work,
  money, health, family, travel, friendship. No children's or school themes.
- **Each level has a recurring cast** so readers build context instead of
  meeting new names every story. The level's `README.md` lists it.
- **Stories are ordered by difficulty** within a level: later stories are
  slightly longer and build on vocabulary taught earlier.
