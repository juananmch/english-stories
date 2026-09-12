#!/usr/bin/env python3
"""Propose headwords for a level's wordlist from the SUBTLEX-US frequency table.

    python3 tools/audit.py --level B1 --rank 4500        # candidates up to rank 4500
    python3 tools/audit.py --level B1 --sizes            # headword totals at several cutoffs

The output is input to a curation pass, not a wordlist: frequency is a proxy
for level, the lemmatizer's stem choices need a human eye, and capitalized
entries are mostly names. Nothing here writes to wordlists/.

For each surface form up to the cutoff that is not already covered by the
level's cumulative vocabulary, the tool proposes a headword — preferring an
existing shorter surface form when the frequent form is a plural or past tense
('parents' proposes 'parent') — and then treats later inflections of that
headword as covered. Derivations of already-known words ('quickly' from
'quick') are listed separately, since whether they deserve their own entry is
a judgment call. Capitalized unknowns are set aside for review.
"""

from __future__ import annotations

import argparse
import textwrap

import lexicon as lx

# What SUBTLEX-US's apostrophe splitting leaves behind: the halves of
# contractions, which are not words.
FRAGMENTS = {
    "s", "t", "m", "d", "ll", "ve", "re", "em",
    "don", "didn", "doesn", "isn", "wasn", "aren", "weren", "wouldn", "couldn",
    "shouldn", "hasn", "haven", "hadn", "ain", "won",
}

# Suffixes whose stripping changes the word rather than inflecting it.
DERIVATIONAL_SUFFIXES = ("ly", "ment", "ation")

# Plain inflections, longest suffix first. Only these may fold a frequent
# surface form onto a shorter one: -er/-est and the irregular map also reach
# real words ('power' -> 'pow', 'bit' -> 'bite') that are not its base.
INFLECTIONS = (("ies", "y"), ("ied", "y"), ("ing", ""), ("es", ""), ("ed", ""), ("s", ""))


def _is_derivation(surface: str, head: str) -> bool:
    return any(surface.endswith(s) and not head.endswith(s) for s in DERIVATIONAL_SUFFIXES)


def inflection_stems(word: str) -> list:
    """Bases the word could be a plain inflection of, likeliest first. Only the
    most specific matching suffix is considered."""
    for suffix, replacement in INFLECTIONS:
        if not word.endswith(suffix):
            continue
        stem = word[: -len(suffix)]
        if replacement:                                     # -ies/-ied: cities, movies
            forms = [stem + replacement, stem + "ie"]
        elif suffix == "es":                                # bones, boxes
            forms = [stem + "e", stem]
        elif suffix == "s":                                 # parents; not mass
            forms = [] if stem.endswith("s") else [stem]
        elif lx._one_syllable_cvc(stem):                    # scared: scare, never scar
            forms = [stem + "e"]
        else:                                               # wanted, stopped, dying
            forms = [stem, stem + "e"]
            if stem.endswith("y"):
                forms.insert(0, stem[:-1] + "ie")
            if len(stem) > 2 and stem[-1] == stem[-2] and stem[-1] not in lx.VOWELS:
                forms.append(stem[:-1])
        return [f for f in forms if len(f) >= 3]
    return []


def propose(rows: list, known: set, limit: int) -> dict:
    """Split the frequency rows up to `limit` into proposed headwords,
    derivations of known words, and capitalized unknowns.

    Returns {"new": [(rank, surface, headword)], "derived": [(rank, surface,
    known headword)], "capitalized": [(rank, word)]}.
    """
    surfaces = {word.lower() for _rank, word, _count in rows}
    vocab = set(known)
    result = {"new": [], "derived": [], "capitalized": []}
    for rank, word, _count in rows:
        if rank > limit:
            break
        low = word.lower()
        if low in FRAGMENTS or (len(low) < 2 and low not in ("a", "i")):
            continue
        if low in vocab:
            continue
        if word[0].isupper():
            result["capitalized"].append((rank, word))
            continue
        head = lx.lemma(low, vocab)
        if head in vocab:
            if _is_derivation(low, head):
                result["derived"].append((rank, low, head))
            continue
        # Not covered: a new headword. If it is a plain inflection of a shorter
        # form that is itself in the table, that is the dictionary form
        # ('parents' -> 'parent').
        head = next((c for c in inflection_stems(low) if c in surfaces), low)
        result["new"].append((rank, low, head))
        vocab.add(head)
    return result


def headword_counts(rows: list, known: set, cutoffs: list, base: int | None = None) -> list:
    """(cutoff, vocabulary size if every candidate up to it is accepted), where
    the size starts from `base` — by default everything in `known`."""
    base = len(known) if base is None else base
    proposed = propose(rows, known, limit=max(cutoffs))
    return [(cutoff, base + sum(1 for rank, _s, _h in proposed["new"] if rank <= cutoff))
            for cutoff in cutoffs]


def known_at(level: str, order: list) -> set:
    """Everything a reader knows when the level starts: the wordlists through
    the level, the cast, and every word a lower level's stories taught."""
    known = lx.load_cumulative_wordlist(level, order) | lx.load_names()
    for lower in order[: order.index(level)]:
        for path in lx.story_files(lower):
            for word, _definition in lx.load_story(path)["glossary"]:
                known.update(word.lower().split())
    return known


def taught_at_or_above(level: str, order: list) -> dict:
    """Glossary headwords taught by stories at this level or higher, with the
    story that teaches each — the entries an expanded list would collide with."""
    taught = {}
    for lvl in order[order.index(level):]:
        for path in lx.story_files(lvl):
            story = lx.load_story(path)
            for word, _definition in story["glossary"]:
                taught.setdefault(word.lower(), story["rel"])
    return taught


def wrap(words: list) -> str:
    return textwrap.fill(" ".join(words), width=78, initial_indent="  ", subsequent_indent="  ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--level", required=True)
    parser.add_argument("--rank", type=int, default=5000, help="frequency cutoff (default 5000)")
    parser.add_argument("--sizes", action="store_true", help="only print headword totals at several cutoffs")
    args = parser.parse_args()

    config = lx.load_config()
    order = config["order"]
    known = known_at(args.level, order)
    rows = lx.load_frequency_rows()

    if args.sizes:
        cutoffs = [2000, 2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000, 10000, 12000, 15000, 20000]
        vocabulary = len(known - lx.load_names())
        print(f"{args.level}: {len(lx.load_cumulative_wordlist(args.level, order))} wordlist headwords, "
              f"{vocabulary} words known at the start of the level including those taught below")
        for cutoff, total in headword_counts(rows, known, cutoffs, base=vocabulary):
            print(f"  up to rank {cutoff:>6}: {total:>6} words")
        return 0

    proposed = propose(rows, known, args.rank)
    taught = taught_at_or_above(args.level, order)

    print(f"# {args.level}: {len(proposed['new'])} proposed headwords up to rank {args.rank}")
    print("# rank  surface -> headword   (T: currently taught by a story, would collide)")
    for rank, surface, head in proposed["new"]:
        note = f"  T {taught[head]}" if head in taught else ""
        arrow = f" -> {head}" if head != surface else ""
        print(f"{rank:>6}  {surface}{arrow}{note}")

    print(f"\n# {len(proposed['derived'])} derivations of known words (not proposed; review)")
    print(wrap([f"{s}<{h}" for _r, s, h in proposed["derived"]]))

    print(f"\n# {len(proposed['capitalized'])} capitalized unknowns (names, interjections; review)")
    print(wrap([w for _r, w in proposed["capitalized"]]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
