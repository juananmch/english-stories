---
name: new-story
description: Write one or more new graded stories for a CEFR level in this repository, following the level contract, and verify them with the validator. Use when the user asks to generate, add or write stories for A1, A2, B1, B2, C1 or C2 — for example "genera 5 historias A2", "add a B1 story about a job interview", or "/new-story A2".
---

# Writing a new story

Arguments are free-form: a level (required), optionally a count and a topic.
Examples: `A2`, `B1 5 stories`, `A1 about going to the doctor`.

## Before writing

1. Read `PROMPT.md` — it is the canonical instruction set for story content.
   Follow it; do not improvise a different standard.
2. Read `config/levels.json` for the target level's word range, new-word budget,
   allowed grammar and banned structures.
3. Read `<LEVEL>/VOCABULARY.md` — you may not teach a word already taught at
   this level or any lower one, and you may not teach a word that already
   appeared in an earlier story here.
4. Read `<LEVEL>/README.md` for the recurring cast and the existing sequence, so
   the new story fits and reuses characters.
5. Read the `wordlists/` files up to and including the target level.

**If the target is B1, B2 or C1, stop and check the wordlist first.** Those are
starter lists, not real level inventories. If it still looks like a starter list,
tell the user that expanding it should come first and offer to do that — writing
stories against an incomplete list produces dozens of false "above level"
findings and wastes a long iteration loop.

## Writing

Number the file after the last existing story at that level:
`<LEVEL>/NN-title-in-kebab-case.md`. Use the exact structure in
`SPECIFICATIONS.md` §4. Later stories in a level should be slightly longer than
earlier ones.

Register any new character in `wordlists/names.txt`.

## Verifying — do not skip this

```sh
python3 tools/build.py --fix-meta
python3 tools/validate.py --level <LEVEL>
```

Fix every finding and re-run until it passes. When the validator reports a word
as above level, decide honestly whether the word belongs to that CEFR level:
if it does, add it to the wordlist; if it does not, rewrite that part of the
story. Never add a word purely to make a finding disappear.

Then regenerate the derived files:

```sh
python3 tools/build.py
```

## Finishing

Report to the user what was written, how many words each story teaches, and any
wordlist changes you made and why. Commit and push only if the user asked you
to — pushing to `main` publishes the story to the live site.
