# Project Specifications

This document records the requirements agreed for this repository, so future
work (new stories, new levels) stays consistent.

## 1. Purpose

A collection of short stories for English learners, organized by CEFR level
(A1 to C2), used for reading practice.

## 2. Repository Structure

- One directory per CEFR level: `A1/`, `A2/`, `B1/`, `B2/`, `C1/`, `C2/`.
- Each directory has its own `README.md` describing that level.
- The root `README.md` lists and links all levels.
- Each story is a separate Markdown file inside its level's directory.

## 3. File Naming

`NN-title-in-kebab-case.md`, where `NN` is a two-digit sequence number
within the level (e.g. `01-a-normal-day.md`, `02-my-family.md`).

## 4. Language Variant

All stories must use **US English**:

- Spelling: `color`, `favorite`, `center`, `organize` (not `colour`,
  `favourite`, `centre`, `organise`).
- Vocabulary: `apartment` (not `flat`), `vacation` (not `holiday`),
  `elevator` (not `lift`), `trash`/`garbage` (not `rubbish`), `cell phone`
  (not `mobile`), `store`/`shop` as used in the US, `soccer` (not
  `football`, unless the sport itself is the topic and context makes it
  clear), etc.
- Punctuation and quotation conventions follow US style (e.g. double
  quotation marks for dialogue, period/comma placement inside quotes).

## 5. Target Audience

Adult learners, roughly **20 to 45 years old**. Story topics and
characters should reflect adult, everyday life (work, family, shopping,
travel, hobbies, social life) — not children's or school topics.

## 6. Vocabulary Constraints

- Grammar and vocabulary must stay within the target CEFR level. No words
  or structures above the level should be used.
- As a reference ceiling for allowed vocabulary per level, use an
  established CEFR wordlist (e.g. the Cambridge English Vocabulary Profile,
  Oxford 3000/5000, or the NGSL/CEFR-J lists) rather than judgment alone.

## 7. File Format and Length

- Format: plain Markdown (`.md`), one story per file, starting with a
  level-1 heading (`# Title`).
- Maximum length: **1000 words** per story (in practice, A1 stories are
  much shorter, roughly 200-350 words, to match the level).

## 8. Vocabulary Repetition Control (New Vocabulary per Story)

Goal: every story should teach the reader something new, so **target
vocabulary should not repeat across stories within the same level**.

Recommended method:

1. **Split vocabulary into two tiers:**
   - *Core/structural words* — high-frequency words (articles, pronouns,
     basic verbs like `be`, `have`, `go`, connectors like `and`, `but`,
     `because`). These are expected to repeat across stories; a level
     cannot be written without reusing them.
   - *Target/content words* — the topic-specific nouns, verbs, and
     adjectives a story is built around (e.g. `supermarket`, `cashier`,
     `checkout` in a shopping story). These are the words a story is
     meant to teach.

2. **Keep a running vocabulary log per level**, e.g. `A1/VOCABULARY.md`,
   listing the target/content words already introduced, grouped by story.

3. **Before writing a new story**, check the level's log and avoid
   reusing words already logged as target vocabulary in an earlier story
   at that level. Core/structural words are exempt from this check.

4. **After finishing a story**, append its new target words to the log,
   so the next story (by anyone, human or AI) can consult it and keep
   building on fresh vocabulary instead of repeating it.

5. Optionally, each story can end with a short **"New Words"** list. This
   helps the learner and doubles as the exact source list to append to
   the level's vocabulary log — keeping the log accurate with minimal
   extra effort.

This turns vocabulary tracking into a simple, auditable file (the log)
instead of relying on memory, so it scales correctly as more stories and
levels are added over time.

Each level directory has its own log (e.g. `A1/VOCABULARY.md`,
`A2/VOCABULARY.md`). Before adding a new story to a level, check that
level's log first.
