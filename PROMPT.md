# Generation Prompt

The canonical prompt for writing a new story. Using it verbatim keeps output
consistent across sessions, people and models. Fill in the bracketed parts.

---

You are writing a graded reading story for adult English learners in the
`english-stories` repository. Follow these instructions exactly.

**Target:** level `[A1/A2/B1/…]`, story number `[NN]`, topic `[topic]`.

**Before you write, read:**

- `SPECIFICATIONS.md` — the rules.
- `config/levels.json` — the word range, new-word budget, allowed grammar and
  banned structures for this level.
- `wordlists/` for every level up to and including the target level — this is
  the vocabulary the reader is assumed to know. You may use these words freely.
- `[LEVEL]/VOCABULARY.md` — every word already taught at this level. You may
  **not** teach any of them again, and you may not teach a word that already
  appeared in an earlier story at this level.
- `[LEVEL]/README.md` — the recurring cast and the existing stories, so the new
  story fits the sequence and reuses characters.

**Write the story:**

1. **Audience.** Adults roughly 20-45. Everyday adult situations: work, money,
   health, family, travel, friendship, home. No children's themes, no school
   settings, no talking animals.

2. **Cast.** Reuse the level's existing characters where it makes sense. If you
   introduce a new one, add the name to `wordlists/names.txt`.

3. **Vocabulary.** Every content word must either be in the wordlists up to
   this level, already taught in an earlier story at this level, or declared in
   your `## New Words` glossary. The glossary is capped by the level's
   `new_word_budget`. Choose target words that genuinely belong to this level's
   band — not words the reader already knows from a lower level.

4. **Grammar.** Use only structures in the level's `grammar_allowed` inventory
   (which inherits from lower levels). Do not use anything matching
   `grammar_banned`. At A1 that means no present perfect, no past perfect, no
   passive, no `should`/`must`, no past continuous, no relative clauses with
   `which`/`whose`/`whom`. At A2, no past perfect, no passive, no second
   conditional.

5. **Length.** Inside the level's `word_count` range. Within a level, later
   stories should be slightly longer than earlier ones.

6. **Language variant.** US English, spelling and vocabulary both.

7. **Story quality.** It still has to be worth reading: a small real situation,
   a complication, and an ending that lands. Simple language is not an excuse
   for a flat story. Use dialogue — it is natural, it breaks up the text, and
   it is easier to read than dense narration.

**Format.** Exactly the structure in `SPECIFICATIONS.md` §4: YAML front matter,
`# Title`, prose, `## New Words` as `- **word** — definition` lines, then
`## Questions` with five comprehension questions and the answers inside a
`<details>` block. Definitions must be written in language at or below the
target level — a definition full of harder words is useless.

**Then verify.** Run:

```sh
python3 tools/build.py --fix-meta
python3 tools/validate.py --level [LEVEL]
```

Fix every finding and re-run until it passes. Then run `python3 tools/build.py`
to regenerate the indexes. Do not edit generated files by hand, and do not add
a word to a wordlist purely to silence a finding — if the word does not belong
at that level, change the story instead.
