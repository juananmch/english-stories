# Wordlists

Each file lists the headwords that become **assumed known** at that level.
The allowed vocabulary for a story is the union of every list up to and
including its level — an A2 story may use `A1.txt` + `A2.txt`, a B1 story may
use `A1.txt` + `A2.txt` + `B1.txt`, and so on.

Anything a story uses that is outside that union must be declared in the
story's `## New Words` glossary, and each story may declare at most
`new_word_budget` of them (see `config/levels.json`). That is the whole
mechanism: the wordlists define what the reader already knows, the glossary
declares what the story teaches, and `tools/validate.py` rejects anything that
is neither.

## Format

One lemma per entry, separated by whitespace or commas. `#` starts a comment.
Only base forms belong here — `tools/lexicon.py` resolves plurals, `-ed`,
`-ing`, `-s`, comparatives, and common irregular forms, so `walk` covers
`walks`, `walked`, and `walking`.

## Provenance

`A1.txt` and `A2.txt` are curated against the CEFR A1/A2 bands as described by
the Cambridge English Vocabulary Profile and the Oxford 3000, restricted to
everyday adult usage. They are deliberately generous on function words and
high-frequency concrete nouns, because those are what simple narrative prose
needs to hold together.

`B1.txt`, `B2.txt` and `C1.txt` are starter lists and need to be expanded
before stories are authored at those levels. An incomplete list does not fail
silently — it reports every unlisted word as above level, which is noisy but
safe. `C2.txt` is intentionally open: the ceiling check is disabled at C2.

## Extending a list

Add the lemma to the file for the level at which a learner is first expected
to know it, not the level where it happens to be used. A word should appear in
exactly one file; the validator reports duplicates across levels.
