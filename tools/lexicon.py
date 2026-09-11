"""Shared loading, parsing and lemmatization for the story toolchain.

Dependency-free on purpose: this runs in CI and on any machine with Python 3,
with no install step.
"""

from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "levels.json")
WORDLIST_DIR = os.path.join(ROOT, "wordlists")

# Past participles used to build the banned-grammar patterns. Regular -ed forms
# are matched by the trailing alternative, so this only needs the irregulars.
IRREGULAR_PARTICIPLES = """
been had done gone seen made said told given taken come become known found
thought got gotten left felt kept held brought bought caught sent spent sat
stood lost met paid run written read begun broken chosen driven eaten fallen
forgotten grown heard hidden kept known lain led lent let lost meant paid put
risen sold sent shown shut slept spoken spent stolen stuck struck sung sat
swum taught torn thought thrown understood woken worn won
"""

PARTICIPLE_ALTERNATION = (
    "(?:" + "|".join(sorted(set(IRREGULAR_PARTICIPLES.split()), key=len, reverse=True)) + r"|\w+ed)"
)

# Irregular lemma map: surface form -> lemma. Only forms the suffix rules below
# cannot reach correctly.
IRREGULAR_LEMMAS = {
    "am": "be", "is": "be", "are": "be", "was": "be", "were": "be", "been": "be", "being": "be",
    "has": "have", "had": "have", "having": "have",
    "does": "do", "did": "do", "done": "do", "doing": "do",
    "went": "go", "gone": "go", "goes": "go",
    "said": "say", "saw": "see", "seen": "see", "made": "make", "took": "take", "taken": "take",
    "came": "come", "knew": "know", "known": "know", "got": "get", "gotten": "get",
    "gave": "give", "given": "give", "found": "find", "thought": "think", "told": "tell",
    "became": "become", "left": "leave", "felt": "feel", "kept": "keep", "held": "hold",
    "brought": "bring", "bought": "buy", "caught": "catch", "sent": "send", "spent": "spend",
    "sat": "sit", "stood": "stand", "lost": "lose", "met": "meet", "paid": "pay", "ran": "run",
    "wrote": "write", "written": "write", "read": "read", "began": "begin", "begun": "begin",
    "broke": "break", "broken": "break", "chose": "choose", "chosen": "choose",
    "drove": "drive", "driven": "drive", "ate": "eat", "eaten": "eat", "fell": "fall",
    "fallen": "fall", "forgot": "forget", "forgotten": "forget", "grew": "grow", "grown": "grow",
    "heard": "hear", "hid": "hide", "hidden": "hide", "led": "lead", "lent": "lend",
    "rose": "rise", "risen": "rise", "sold": "sell", "showed": "show", "shown": "show",
    "shut": "shut", "slept": "sleep", "spoke": "speak", "spoken": "speak", "stole": "steal",
    "stolen": "steal", "struck": "strike", "sang": "sing", "sung": "sing", "swam": "swim",
    "taught": "teach", "tore": "tear", "torn": "tear", "threw": "throw", "thrown": "throw",
    "understood": "understand", "woke": "wake", "woken": "wake", "wore": "wear", "worn": "wear",
    "won": "win", "put": "put", "cut": "cut", "let": "let", "set": "set", "cost": "cost",
    "drank": "drink", "drunk": "drink", "flew": "fly", "flown": "fly", "hung": "hang",
    "rang": "ring", "rung": "ring", "swum": "swim", "blew": "blow", "blown": "blow",
    "drew": "draw", "drawn": "draw", "threw": "throw", "wrote": "write", "rode": "ride",
    "ridden": "ride", "sank": "sink", "sunk": "sink", "bit": "bite", "bitten": "bite",
    "chose": "choose", "froze": "freeze", "frozen": "freeze", "hit": "hit", "hurt": "hurt",
    "knelt": "kneel", "laid": "lay", "lain": "lie", "meant": "mean",
    "shone": "shine", "shot": "shoot", "slid": "slide", "spread": "spread",
    "sprang": "spring", "stuck": "stick", "swept": "sweep", "swore": "swear",
    "woke": "wake", "wound": "wind", "built": "build", "burnt": "burn", "burned": "burn",
    "dealt": "deal", "dug": "dig", "fed": "feed", "fled": "flee", "ground": "grind",
    "hidden": "hide", "held": "hold", "leapt": "leap", "learnt": "learn", "lit": "light",
    "children": "child", "people": "person", "men": "man", "women": "woman", "feet": "foot",
    "teeth": "tooth", "geese": "goose", "mice": "mouse", "lives": "life", "wives": "wife",
    "knives": "knife", "leaves": "leaf", "shelves": "shelf", "better": "good", "best": "good",
    "worse": "bad", "worst": "bad", "more": "much", "most": "much", "less": "little",
    "clothes": "clothes", "glasses": "glasses", "pants": "pants", "stairs": "stairs",
    "dishes": "dish", "watches": "watch",
}

CONTRACTION_TAILS = {"s", "t", "re", "ve", "ll", "d", "m"}


SUFFIX_RULES = (
    ("ies", "y"),
    ("ied", "y"),
    ("iest", "y"),
    ("ier", "y"),
    ("sses", "ss"),
    ("shes", "sh"),
    ("ches", "ch"),
    ("xes", "x"),
    ("zes", "z"),
    ("es", ""),
    ("s", ""),
    ("ing", ""),
    ("ed", ""),
    ("est", ""),
    ("er", ""),
    ("ly", ""),
)


def candidates(word: str) -> list:
    """Every plausible dictionary form of a surface word, most likely first.

    Suffix stripping is ambiguous in English ('nervous' is not 'nervou' + s,
    'stopped' is 'stop' not 'stopp'), so this generates alternatives rather than
    committing to one. `lemma()` picks between them using the actual vocabulary.
    """
    w = word.lower().strip("'")
    if not w:
        return [""]
    out = [w]
    if w in IRREGULAR_LEMMAS:
        out.append(IRREGULAR_LEMMAS[w])

    # possessives and contractions: dog's -> dog, teacher's -> teacher
    if "'" in w:
        head, _, tail = w.partition("'")
        if tail in CONTRACTION_TAILS and head:
            out.append(head)
            if head in IRREGULAR_LEMMAS:
                out.append(IRREGULAR_LEMMAS[head])
            w = head

    for suffix, replacement in SUFFIX_RULES:
        if not w.endswith(suffix) or len(w) - len(suffix) < 2:
            continue
        stem = w[: -len(suffix)] + replacement
        if not stem:
            continue
        out.append(stem)
        # silent e: making -> make, hoped -> hope, arrived -> arrive
        if not replacement:
            out.append(stem + "e")
        # doubled consonant: stopped -> stop, running -> run, planned -> plan
        if len(stem) > 2 and stem[-1] == stem[-2] and stem[-1] not in "aeiou":
            out.append(stem[:-1])
        for form in (stem, stem + "e"):
            if form in IRREGULAR_LEMMAS:
                out.append(IRREGULAR_LEMMAS[form])

    seen, ordered = set(), []
    for candidate in out:
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def lemma(word: str, vocab: set | None = None) -> str:
    """Canonical headword for a surface form.

    With `vocab`, returns the first candidate that is actually a known word —
    this is what makes 'stopped' resolve to 'stop' rather than 'stopp'. Without
    it, returns the surface form, which is conservative: an unrecognized word is
    never silently reduced into a known one.
    """
    forms = candidates(word)
    if vocab:
        for form in forms:
            if form in vocab:
                return form
    return forms[0]


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _read_wordfile(path: str) -> set:
    if not os.path.exists(path):
        return set()
    words = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0]
            for token in re.split(r"[,\s]+", line):
                token = token.strip().lower()
                if token:
                    words.add(token)
    return words


def load_wordlist(level: str) -> set:
    """Headwords first assumed known at exactly this level."""
    return _read_wordfile(os.path.join(WORDLIST_DIR, f"{level}.txt"))


def load_cumulative_wordlist(level: str, order: list) -> set:
    """Everything a reader at this level is assumed to know."""
    words = set()
    for lvl in order:
        words |= load_wordlist(lvl)
        if lvl == level:
            break
    return words


def load_names() -> set:
    return _read_wordfile(os.path.join(WORDLIST_DIR, "names.txt"))


FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_front_matter(text: str):
    """Parse the YAML subset used by story files: scalars and inline lists.

    Returns (metadata dict, body without the front matter).
    """
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            meta[key] = [v.strip().strip("\"'") for v in inner.split(",") if v.strip()] if inner else []
        elif value.isdigit():
            meta[key] = int(value)
        else:
            meta[key] = value.strip("\"'")
    return meta, text[match.end():]


SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def split_sections(body: str) -> dict:
    """Split a story body into {section title: content}, plus 'story' for the
    prose above the first '##' heading."""
    sections = {}
    matches = list(SECTION_RE.finditer(body))
    head = body[: matches[0].start()] if matches else body
    sections["story"] = re.sub(r"^#\s+.*$", "", head, count=1, flags=re.MULTILINE).strip()
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[m.group(1).strip().lower()] = body[m.end():end].strip()
    return sections


GLOSSARY_ENTRY_RE = re.compile(r"^-\s+\*\*(.+?)\*\*\s*[—-]\s*(.+?)\s*$", re.MULTILINE)


def parse_glossary(section: str):
    """Parse '- **word** — definition' lines into [(word, definition), ...]."""
    return [(m.group(1).strip().lower(), m.group(2).strip()) for m in GLOSSARY_ENTRY_RE.finditer(section)]


# Accented letters are included so 'café' tokenizes as one word rather than
# splitting into a meaningless 'caf'.
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ']*")


def tokenize(text: str):
    """Prose words only: strips markdown emphasis markers and headings."""
    text = re.sub(r"`[^`]*`", " ", text)
    return WORD_RE.findall(text)


def count_words(text: str) -> int:
    return len(tokenize(text))


def story_files(level: str):
    """Story markdown files for a level, in reading order."""
    level_dir = os.path.join(ROOT, level)
    if not os.path.isdir(level_dir):
        return []
    names = sorted(
        f for f in os.listdir(level_dir)
        if f.endswith(".md") and f[0].isdigit()
    )
    return [os.path.join(level_dir, f) for f in names]


def load_story(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    meta, body = parse_front_matter(text)
    sections = split_sections(body)
    glossary = parse_glossary(sections.get("new words", ""))
    title_match = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    return {
        "path": path,
        "rel": os.path.relpath(path, ROOT),
        "meta": meta,
        "body": body,
        "title": title_match.group(1).strip() if title_match else os.path.basename(path),
        "sections": sections,
        "prose": sections.get("story", ""),
        "glossary": glossary,
        "glossary_words": [w for w, _ in glossary],
    }
