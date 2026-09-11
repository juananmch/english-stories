#!/usr/bin/env python3
"""Validate every story against the level contract in config/levels.json.

Exit code 0 if all checks pass, 1 otherwise. Run with --level A1 to check a
single level, -v to also print per-story statistics.

Checks, per story:
  ceiling      every content word is assumed-known at the level, declared in
               the glossary, or a registered proper noun
  budget       the glossary declares no more than new_word_budget words
  glossary     every declared word actually appears in the prose
  reteach      a declared word was not already taught at this or a lower level
  teach-late   a declared word did not already appear in an earlier story
  known        a declared word is not already assumed-known at a lower level
  length       word count is inside the level's range
  grammar      no banned structure for the level; declared grammar is allowed
  spelling     no British spellings or non-US vocabulary
  metadata     front matter is present, complete and consistent with the body
"""

from __future__ import annotations

import argparse
import re
import sys

import lexicon as lx

# Levels where the vocabulary ceiling does not apply.
UNRESTRICTED_LEVELS = {"C2"}

# Function words and grammatical forms that never count as taught vocabulary.
# Anything here is exempt from the ceiling check regardless of the wordlists.
ALWAYS_ALLOWED = {
    "n't", "s", "t", "re", "ve", "ll", "d", "m", "o", "ok",
}


class Finding:
    def __init__(self, story: str, check: str, message: str):
        self.story = story
        self.check = check
        self.message = message

    def __str__(self) -> str:
        return f"  [{self.check}] {self.message}"


def build_banned_patterns(level_cfg: dict):
    patterns = []
    for rule in level_cfg.get("grammar_banned", []):
        pattern = rule["pattern"].replace("{PART}", lx.PARTICIPLE_ALTERNATION)
        patterns.append((rule["id"], re.compile(pattern, re.IGNORECASE), rule["message"]))
    return patterns


def check_level(level: str, config: dict, verbose: bool = False):
    order = config["order"]
    level_cfg = config["levels"][level]
    findings = []

    known = lx.load_cumulative_wordlist(level, order)
    lower_levels = order[: order.index(level)]
    known_below = lx.load_cumulative_wordlist(lower_levels[-1], order) if lower_levels else set()
    names = lx.load_names()
    banned = build_banned_patterns(level_cfg)
    us_map = {k: v for k, v in config["us_english"].items() if not k.startswith("_")}

    # A level inherits every structure from the levels below it, so "all A1
    # structures" in the config does not have to be expanded by hand.
    allowed_grammar = set()
    for lvl in order:
        allowed_grammar |= set(config["levels"][lvl].get("grammar_allowed", []))
        if lvl == level:
            break

    taught_so_far = {}      # lemma -> story that taught it
    seen_so_far = {}        # lemma -> first story it appeared in
    stories = [lx.load_story(p) for p in lx.story_files(level)]

    # The lemmatizer resolves a surface form against real vocabulary, so it needs
    # to know every word in play at this level: the ceiling, the cast, every word
    # any story here declares, and everything already taught lower down —
    # otherwise 'smelled' cannot resolve to a 'smell' that an A1 story taught.
    lower_taught_raw = {}
    for lower in lower_levels:
        for path in lx.story_files(lower):
            lower_story = lx.load_story(path)
            for word in lower_story["glossary_words"]:
                lower_taught_raw.setdefault(word.lower(), lower_story["rel"])

    vocab = set(known) | names | set(lower_taught_raw)
    for story in stories:
        for word, _ in story["glossary"]:
            vocab.update(word.lower().split())

    # Words taught at lower levels, so a level never re-teaches what came before.
    taught_below = {lx.glossary_key(word, vocab): rel for word, rel in lower_taught_raw.items()}

    for index, story in enumerate(stories, start=1):
        rel = story["rel"]
        meta = story["meta"]
        prose = story["prose"]
        glossary = story["glossary"]
        declared = {lx.glossary_key(w, vocab): w for w, _ in glossary}

        def add(check, message):
            findings.append(Finding(rel, check, message))

        # --- metadata ---
        if not meta:
            add("metadata", "missing YAML front matter")
        else:
            if meta.get("level") != level:
                add("metadata", f"front matter level is {meta.get('level')!r}, expected {level!r}")
            for field in ("title", "topic", "grammar", "characters"):
                if field not in meta:
                    add("metadata", f"front matter is missing '{field}'")
            declared_count = meta.get("new_words")
            if declared_count is not None and declared_count != len(glossary):
                add("metadata", f"front matter new_words={declared_count} but glossary has {len(glossary)} entries")
            actual_words = lx.count_words(prose)
            stated = meta.get("word_count")
            if stated is not None and abs(stated - actual_words) > 5:
                add("metadata", f"front matter word_count={stated} but prose has {actual_words} words")
            for structure in meta.get("grammar", []):
                if allowed_grammar and structure not in allowed_grammar:
                    add("grammar", f"declared structure {structure!r} is not in the {level} inventory")

        # --- required sections ---
        for section in ("new words", "questions"):
            if section not in story["sections"]:
                add("structure", f"missing '## {section.title()}' section")
        if not glossary:
            add("structure", "glossary is empty or not in '- **word** — definition' form")

        # --- length ---
        words = lx.count_words(prose)
        bounds = level_cfg["word_count"]
        if words < bounds["min"] or words > bounds["max"]:
            add("length", f"prose is {words} words, outside {bounds['min']}-{bounds['max']} for {level}")

        # --- budget ---
        budget = level_cfg["new_word_budget"]
        if len(glossary) > budget:
            add("budget", f"glossary declares {len(glossary)} words, budget is {budget}")

        # --- glossary entries must be earned ---
        prose_lemmas = {lx.lemma(t, vocab) for t in lx.tokenize(prose)}
        prose_lower = prose.lower()
        for word, definition in glossary:
            head = lx.glossary_key(word, vocab)
            phrase_present = word.lower() in prose_lower
            if head not in prose_lemmas and not phrase_present:
                add("glossary", f"declared word {word!r} does not appear in the prose")
            if not definition:
                add("glossary", f"declared word {word!r} has no definition")
            if head in taught_so_far:
                add("reteach", f"{word!r} was already taught in {taught_so_far[head]}")
            if head in taught_below:
                add("reteach", f"{word!r} was already taught at a lower level in {taught_below[head]}")
            if head in seen_so_far and seen_so_far[head] != rel:
                add("teach-late", f"{word!r} is taught here but already appeared in {seen_so_far[head]}")
            if head in known_below:
                add("known", f"{word!r} is already assumed known below {level}; it should not be taught")

        # --- vocabulary ceiling ---
        # A word is legal here if the reader is assumed to know it at this level,
        # if an earlier story already taught it, or if this story declares it.
        if level not in UNRESTRICTED_LEVELS:
            glossary_parts = set()
            for entry, _ in glossary:
                for part in entry.lower().split():
                    glossary_parts.add(part)
                    glossary_parts.add(lx.lemma(part, vocab))
            over = {}
            for token in lx.tokenize(prose):
                low = token.lower()
                head = lx.lemma(token, vocab)
                if low in ALWAYS_ALLOWED or head in ALWAYS_ALLOWED:
                    continue
                if head in known or low in known:
                    continue
                if head in names or low in names:
                    continue
                if head in declared or low in glossary_parts or head in glossary_parts:
                    continue
                if head in taught_so_far or head in taught_below:
                    continue
                over.setdefault(head, token)
            for head, surface in sorted(over.items()):
                add("ceiling", f"{surface!r} (lemma {head!r}) is above {level} and is not declared in the glossary")

        # --- grammar ---
        for rule_id, pattern, message in banned:
            for match in pattern.finditer(prose):
                add("grammar", f"{rule_id}: {match.group(0)!r} — {message}")

        # --- US English ---
        for british, american in us_map.items():
            if re.search(rf"\b{re.escape(british)}\b", prose, re.IGNORECASE):
                add("spelling", f"British/non-US form {british!r} found; use {american!r}")

        if verbose:
            print(f"  {index:02d} {rel:<45} {words:>4} words  {len(glossary):>2} new  "
                  f"{'OK' if not [f for f in findings if f.story == rel] else 'FAIL'}")

        # record state for later stories
        for word, _ in glossary:
            taught_so_far.setdefault(lx.glossary_key(word, vocab), rel)
        for token in lx.tokenize(prose):
            seen_so_far.setdefault(lx.lemma(token, vocab), rel)

    return findings, len(stories)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--level", action="append", help="only check this level (repeatable)")
    parser.add_argument("-v", "--verbose", action="store_true", help="print per-story statistics")
    args = parser.parse_args()

    config = lx.load_config()
    levels = args.level or config["order"]

    total_findings, total_stories = [], 0
    for level in levels:
        stories = lx.story_files(level)
        if not stories:
            continue
        print(f"{level} ({len(stories)} stories)")
        findings, count = check_level(level, config, args.verbose)
        total_stories += count
        if findings:
            by_story = {}
            for finding in findings:
                by_story.setdefault(finding.story, []).append(finding)
            for story, items in by_story.items():
                print(f"\n{story}")
                for item in items:
                    print(item)
            print()
        total_findings.extend(findings)

    print()
    if total_findings:
        checks = {}
        for finding in total_findings:
            checks[finding.check] = checks.get(finding.check, 0) + 1
        summary = ", ".join(f"{k}: {v}" for k, v in sorted(checks.items()))
        print(f"FAILED — {len(total_findings)} findings across {total_stories} stories ({summary})")
        return 1
    print(f"PASSED — {total_stories} stories, no findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
