# Project Specifications

The rules every story in this repository follows. Most of them are enforced by
`tools/validate.py`, which reads `config/levels.json` — so this document
explains the system, and the config is the authority.

## 1. Purpose

Graded short stories for adult English learners, organized by CEFR level
(A1 to C2), for reading practice.

## 2. Audience

Adult learners, roughly **20 to 45 years old**. Topics and characters reflect
adult everyday life — work, family, money, health, travel, friendship — never
children's or school themes.

## 3. Repository layout

```
A1/ … C2/          one directory per level
  NN-title.md      one story per file, numbered in reading order
  README.md        generated index for the level
  VOCABULARY.md    generated log of every word taught at the level
config/levels.json word ranges, new-word budgets, grammar inventory, US spelling map
wordlists/         the vocabulary a reader is assumed to know at each level
tools/             validator and index builder
```

Generated files carry a "do not edit by hand" header. Edit the stories and run
`python3 tools/build.py`.

## 4. Story file format

Every story is Markdown with YAML front matter:

```markdown
---
level: A1
title: A Normal Day
topic: daily routine
grammar: [present simple, prepositions of time and place, basic connectors]
characters: [Laura, Elena]
word_count: 171
new_words: 8
---

# A Normal Day

…prose…

## New Words

- **word** — a definition written in language at or below this level

## Questions

1. …five comprehension questions…

<details>
<summary>Answers</summary>

1. …

</details>
```

`word_count` and `new_words` are derived values — run
`python3 tools/build.py --fix-meta` rather than counting by hand. Entries in
`grammar` and `characters` must not contain commas, since front-matter lists
are comma-separated.

## 5. Language variant

**US English** throughout: `color`, `favorite`, `center`, `organize`;
`apartment` not `flat`, `vacation` not `holiday`, `elevator` not `lift`,
`pants` not `trousers`, `soccer` not `football`, `pharmacy` not `chemist`.
The full map is the `us_english` section of `config/levels.json`, and the
validator rejects any British form listed there.

## 6. Level control — the core of the system

Level is controlled on **two axes**, because CEFR level is driven as much by
grammar as by vocabulary.

### Vocabulary

`wordlists/` defines what a reader at each level is **assumed to know**. The
allowed vocabulary for a story is every list up to and including its level.
Anything outside that must be declared in the story's `## New Words` glossary,
and each story may declare at most `new_word_budget` words (10 at A1, 12 at A2).

That is the whole mechanism, and it closes the hole a hand-maintained log
leaves open: a story cannot quietly introduce fifty unlisted words, because
every word is either already known, explicitly taught, or a validation failure.

A word taught in story 3 counts as known from story 4 onward, so vocabulary
accumulates the way a reader's does.

### Grammar

Each level has a `grammar_allowed` inventory and a set of `grammar_banned`
patterns. A story declares the structures it practices in its front matter,
and the validator checks both directions: the declared structures must exist
in the level's inventory (inherited from all lower levels), and the prose must
not contain a banned structure. This is what keeps past perfect out of A2 and
present perfect out of A1.

## 7. No repeated vocabulary

Each story must teach something genuinely new, enforced by four checks:

- **reteach** — a word already taught at this level, or at any lower level,
  cannot be taught again.
- **teach-late** — a word cannot be taught in story 7 if it already appeared in
  story 3. The reader meets it and learns it in the same place.
- **known** — a word already assumed known at a lower level cannot be taught;
  an A2 story teaches A2-band vocabulary, not A1 vocabulary.
- **glossary** — a declared word must actually appear in the prose, and must
  have a definition.

`VOCABULARY.md` in each level directory is the generated record of this, in
reading order, with a combined alphabetical glossary.

## 8. Length and pacing

Prose length is bounded per level (`word_count` in the config: 150-400 at A1,
250-500 at A2). Within a level, stories are ordered from shortest and simplest
to longest, so a reader working through a directory in order meets a gentle
slope rather than a step.

## 9. Recurring cast

Each level has a small recurring cast, listed in the generated level README.
A reader who has finished three A1 stories already knows who Laura and Elena
are, so attention goes to the language instead of to a new set of names. New
characters must be registered in `wordlists/names.txt` — an unregistered
capitalized word is reported as above level.

## 10. The published site

`tools/site.py` builds a static reading site into `_site/`, deployed to GitHub
Pages by `.github/workflows/pages.yml` on every push to `main`. The workflow
runs the validator first, so a story that breaks the level contract is never
published.

The site exists because it can do one thing the Markdown cannot: mark each word
a story teaches directly in the prose and show its definition where the reader
meets it, instead of in a list at the bottom. Everything on it is generated from
the story files — there is no separate content to keep in sync.

## 11. Adding a story

1. Read `PROMPT.md` and the level's `VOCABULARY.md`.
2. Write the story to `<LEVEL>/NN-title.md` in the format above.
3. `python3 tools/build.py --fix-meta`
4. `python3 tools/validate.py --level <LEVEL>`
5. Fix findings until it passes, then `python3 tools/build.py`.

If the validator reports a word as above level that genuinely belongs to the
level, the fix is to add it to the wordlist — that is a real correction to the
level definition, not a way around the check. Adding a word to silence a
finding when it does not belong at that level defeats the whole system.
