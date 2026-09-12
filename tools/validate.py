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
  band         share of prose outside the core frequency band is in the level's
               target range (registered names excluded)
  sentence-length
               mean words per sentence is inside the level's range
  new-word-floor
               the glossary teaches at least the level's minimum

Checks named in the config's "warning_checks" are reported and counted but do
not fail the run. That is how a new check is introduced: as a warning, until
its thresholds have been checked against the corpus.
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
    def __init__(self, story: str, check: str, message: str, severity: str = "error"):
        self.story = story
        self.check = check
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        prefix = "warning: " if self.severity == "warning" else ""
        return f"  [{self.check}] {prefix}{self.message}"


def describe_range(bounds: dict, unit: str = "") -> str:
    low, high = bounds.get("min"), bounds.get("max")
    if low is not None and high is not None:
        return f"{low}–{high}{unit}"
    if low is not None:
        return f"at least {low}{unit}"
    return f"at most {high}{unit}"


def in_core_band(token: str, core_band: set) -> bool:
    """Whether a prose token counts as core vocabulary.

    A token is core if any dictionary form of it is. SUBTLEX-US splits words on
    apostrophes, so "o'clock" has no rank of its own there; a token with an
    apostrophe that does not resolve as a whole is judged by its pieces.
    """
    if lx.lemma(token, core_band) in core_band:
        return True
    pieces = [p for p in token.lower().split("'") if p]
    return len(pieces) > 1 and all(lx.lemma(p, core_band) in core_band for p in pieces)


def outside_range(value: float, bounds: dict) -> bool:
    low, high = bounds.get("min"), bounds.get("max")
    return (low is not None and value < low) or (high is not None and value > high)


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
    own_wordlist = lx.load_wordlist(level)
    lower_levels = order[: order.index(level)]
    known_below = lx.load_cumulative_wordlist(lower_levels[-1], order) if lower_levels else set()
    names = lx.load_names()
    banned = build_banned_patterns(level_cfg)
    us_map = {k: v for k, v in config["us_english"].items() if not k.startswith("_")}
    warning_checks = set(config.get("warning_checks", []))

    # The core band: the most frequent surface forms of the language, against
    # which the lexical-band check measures how much of the prose is "hard".
    core_band = set()
    if "core_band" in config:
        ranks = lx.load_frequency()
        core_band = {word for word, rank in ranks.items() if rank <= config["core_band"]}

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
            severity = "warning" if check in warning_checks else "error"
            findings.append(Finding(rel, check, message, severity))

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
        floor = level_cfg.get("new_word_floor")
        if floor is not None and 0 < len(glossary) < floor:
            add("new-word-floor", f"glossary declares {len(glossary)} words, fewer than the floor of {floor}")

        # --- lexical band ---
        # How much of the prose is outside the most frequent words of the
        # language. This is the texture of the story rather than its glossary:
        # a level is not made of the words it teaches but of the words it is
        # written in. Names are left out, since a cast is not vocabulary.
        band_bounds = level_cfg.get("lexical_band")
        if band_bounds and core_band:
            counted = outside = 0
            for token in lx.tokenize(prose):
                low = token.lower()
                if low in names or lx.lemma(token, names) in names:
                    continue
                counted += 1
                if not in_core_band(token, core_band):
                    outside += 1
            if counted:
                share = 100.0 * outside / counted
                if outside_range(share, band_bounds):
                    add("band", f"{share:.1f}% of words are outside the top {config['core_band']} "
                                f"(target {describe_range(band_bounds, '%')})")

        # --- sentence length ---
        length_bounds = level_cfg.get("sentence_length")
        if length_bounds:
            sentences = lx.sentences(prose)
            if sentences:
                mean = sum(lx.count_words(s) for s in sentences) / len(sentences)
                if outside_range(mean, length_bounds):
                    add("sentence-length", f"mean sentence length is {mean:.1f} words "
                                           f"(target {describe_range(length_bounds)})")

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
            if head in own_wordlist:
                add("known", f"{word!r} is in wordlists/{level}.txt itself — a reader is assumed to "
                              f"know it from the start of the level, so it cannot also be 'taught' here")

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
    errors = [f for f in total_findings if f.severity != "warning"]
    warnings = [f for f in total_findings if f.severity == "warning"]
    stories = plural(total_stories, "story", "stories")
    warned = f"{plural(len(warnings), 'warning')} ({by_check(warnings)})" if warnings else ""
    if errors:
        print(f"FAILED — {plural(len(errors), 'finding')} across {stories} ({by_check(errors)})"
              + (f", {warned}" if warned else ""))
        return 1
    print(f"PASSED — {stories}, {warned or 'no findings'}")
    return 0


def plural(count: int, singular: str, plural_form: str | None = None) -> str:
    return f"{count} {singular if count == 1 else plural_form or singular + 's'}"


def by_check(findings: list) -> str:
    counts = {}
    for finding in findings:
        counts[finding.check] = counts.get(finding.check, 0) + 1
    return ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))


if __name__ == "__main__":
    sys.exit(main())
