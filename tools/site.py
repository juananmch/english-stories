#!/usr/bin/env python3
"""Build the static reading site into _site/.

Dependency-free, like the rest of the toolchain. The output is plain HTML and
one stylesheet, so it can be served by GitHub Pages with no build plugins.

The point of the site, over reading the Markdown on github.com, is the glossary:
every word a story teaches is marked in the prose and shows its definition where
the reader meets it, instead of at the bottom of the page.
"""

from __future__ import annotations

import html
import os
import re
import shutil
import sys

import lexicon as lx

OUT = os.path.join(lx.ROOT, "_site")

LEVEL_BLURB = {
    "A1": "Beginner",
    "A2": "Elementary",
    "B1": "Intermediate",
    "B2": "Upper Intermediate",
    "C1": "Advanced",
    "C2": "Proficiency",
}

STYLE = """
:root {
  color-scheme: light dark;
  --bg: #fbfaf8;
  --surface: #ffffff;
  --text: #23201c;
  --muted: #6b645c;
  --line: #e5e0d8;
  --accent: #8a5a2b;
  --accent-soft: #f3e9dd;
  --shadow: 0 1px 2px rgba(0,0,0,.05), 0 8px 24px rgba(0,0,0,.05);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #171513;
    --surface: #201d1a;
    --text: #ece7e0;
    --muted: #a49b90;
    --line: #332e29;
    --accent: #d9a066;
    --accent-soft: #3a2e22;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.3);
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-text-size-adjust: 100%;
}
.wrap { max-width: 40rem; margin: 0 auto; padding: 0 20px; }
.wrap-wide { max-width: 52rem; }
a { color: var(--accent); }
header.site {
  border-bottom: 1px solid var(--line);
  background: var(--surface);
  position: sticky; top: 0; z-index: 10;
}
header.site .wrap {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; padding-block: 12px; flex-wrap: wrap;
}
header.site a.brand { font-weight: 650; color: var(--text); text-decoration: none; letter-spacing: -.01em; }
header.site nav { display: flex; gap: 4px; flex-wrap: wrap; }
header.site nav a {
  text-decoration: none; color: var(--muted); font-size: .8125rem; font-weight: 600;
  padding: 4px 9px; border-radius: 6px;
}
header.site nav a:hover { background: var(--accent-soft); color: var(--accent); }
header.site nav a.on { background: var(--accent-soft); color: var(--accent); }
main { padding-block: 40px 72px; }
h1 { font-size: 1.9rem; line-height: 1.2; letter-spacing: -.02em; margin: 0 0 12px; }
h2 { font-size: 1.15rem; letter-spacing: -.01em; margin: 40px 0 12px; }
.lede { color: var(--muted); margin: 0 0 32px; }
.meta { color: var(--muted); font-size: .8125rem; margin: 0 0 28px; }
.meta .dot { opacity: .5; margin: 0 7px; }
.badge {
  display: inline-block; background: var(--accent-soft); color: var(--accent);
  font-size: .6875rem; font-weight: 700; letter-spacing: .06em;
  padding: 3px 7px; border-radius: 5px; vertical-align: 1px;
}

/* story prose */
article p { margin: 0 0 1.15em; }
article.story { font-size: 1.125rem; line-height: 1.75; }
article.story p { margin: 0 0 1.3em; }

/* glossary word in prose — text-decoration rather than a border, so the mark
   hugs the text and survives a phrase wrapping across two lines */
.gloss {
  text-decoration: underline dotted var(--accent);
  text-decoration-thickness: 2px;
  text-underline-offset: 4px;
  cursor: pointer; position: relative; color: inherit;
  background: none; border: 0; font: inherit; padding: 0;
}
.gloss:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }
.gloss:hover { background: var(--accent-soft); }
.gloss .def {
  display: none; position: absolute; left: 50%; bottom: calc(100% + 9px);
  transform: translateX(-50%);
  background: var(--surface); color: var(--text);
  border: 1px solid var(--line); border-radius: 9px;
  box-shadow: var(--shadow);
  padding: 9px 12px; width: max-content; max-width: min(19rem, 80vw);
  font-size: .875rem; line-height: 1.45; font-weight: 400;
  text-align: left; white-space: normal; z-index: 20;
}
.gloss[aria-expanded="true"] .def { display: block; }
@media (hover: hover) { .gloss:hover .def { display: block; } }

/* cards */
.cards { display: grid; gap: 10px; padding: 0; margin: 0; list-style: none; }
.card {
  display: block; background: var(--surface); border: 1px solid var(--line);
  border-radius: 11px; padding: 15px 17px; text-decoration: none; color: inherit;
  transition: border-color .15s, transform .15s;
}
.card:hover { border-color: var(--accent); transform: translateY(-1px); }
.card .num { color: var(--muted); font-variant-numeric: tabular-nums; font-size: .8125rem; font-weight: 600; }
.card .title { font-weight: 650; margin: 2px 0 5px; letter-spacing: -.01em; }
.card .sub { color: var(--muted); font-size: .8125rem; }

/* glossary list */
.glossary { list-style: none; padding: 0; margin: 0; }
.glossary li { padding: 11px 0; border-bottom: 1px solid var(--line); }
.glossary li:last-child { border-bottom: 0; }
.glossary .w { font-weight: 650; }
.glossary .d { color: var(--muted); }

/* questions */
ol.questions { padding-left: 1.25rem; margin: 0; }
ol.questions li { margin-bottom: .55em; }
details {
  margin-top: 20px; background: var(--surface); border: 1px solid var(--line);
  border-radius: 11px; padding: 13px 17px;
}
details summary { cursor: pointer; font-weight: 650; font-size: .9375rem; }
details[open] summary { margin-bottom: 11px; }

/* tables */
table { border-collapse: collapse; width: 100%; font-size: .9375rem; }
th, td { text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 700; }
.scroll { overflow-x: auto; }

/* pager */
.pager { display: flex; gap: 10px; margin-top: 48px; }
.pager a {
  flex: 1; background: var(--surface); border: 1px solid var(--line); border-radius: 11px;
  padding: 13px 15px; text-decoration: none; color: inherit; min-width: 0;
}
.pager a:hover { border-color: var(--accent); }
.pager .dir { color: var(--muted); font-size: .75rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; }
.pager .t { font-weight: 650; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pager .next { text-align: right; }

footer.site { border-top: 1px solid var(--line); color: var(--muted); font-size: .8125rem; padding-block: 24px 40px; }
footer.site a { color: var(--muted); }
@media (max-width: 480px) {
  h1 { font-size: 1.55rem; }
  article.story { font-size: 1.0625rem; }
  .pager { flex-direction: column; }
  .pager .next { text-align: left; }
}
"""

SCRIPT = """
document.addEventListener('click', function (e) {
  var hit = e.target.closest('.gloss');
  document.querySelectorAll('.gloss[aria-expanded="true"]').forEach(function (el) {
    if (el !== hit) el.setAttribute('aria-expanded', 'false');
  });
  if (hit) {
    hit.setAttribute('aria-expanded', hit.getAttribute('aria-expanded') === 'true' ? 'false' : 'true');
  }
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.gloss[aria-expanded="true"]').forEach(function (el) {
      el.setAttribute('aria-expanded', 'false');
    });
    return;
  }
  if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('gloss')) {
    e.preventDefault();
    e.target.setAttribute('aria-expanded', e.target.getAttribute('aria-expanded') === 'true' ? 'false' : 'true');
  }
});
"""


def page(title: str, body: str, depth: int, active: str = "", wide: bool = False, levels=()) -> str:
    up = "../" * depth
    nav_items = []
    for lvl in levels:
        css = ' class="on"' if lvl == active else ""
        nav_items.append(f'<a href="{up}{lvl}/"{css}>{lvl}</a>')
    nav = "".join(nav_items)
    wrap = "wrap wrap-wide" if wide else "wrap"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<header class="site"><div class="wrap">
<a class="brand" href="{up}">English Stories</a>
<nav>{nav}</nav>
</div></header>
<main><div class="{wrap}">
{body}
</div></main>
<footer class="site"><div class="wrap">
Graded reading for adult learners &middot;
<a href="https://github.com/juananmch/english-stories">Source on GitHub</a>
</div></footer>
<script>{SCRIPT}</script>
</body>
</html>
"""


def find_spans(text: str, glossary: list, vocab: set) -> list:
    """Locate every glossary word in the prose, longest phrases first.

    Returns non-overlapping (start, end, word, definition) spans.
    """
    spans: list = []
    taken: list = []

    def free(start: int, end: int) -> bool:
        return all(end <= s or start >= e for s, e in taken)

    # Multi-word entries first, so "ice cream" wins over a bare "cream".
    ordered = sorted(glossary, key=lambda item: -len(item[0].split()))
    for word, definition in ordered:
        parts = word.split()
        if len(parts) > 1:
            pattern = re.compile(r"\b" + r"\W+".join(re.escape(p) for p in parts) + r"\w*\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                if free(match.start(), match.end()):
                    spans.append((match.start(), match.end(), word, definition))
                    taken.append((match.start(), match.end()))

    heads = {}
    for word, definition in glossary:
        if len(word.split()) == 1:
            heads[lx.lemma(word, vocab)] = (word, definition)
    if heads:
        for match in lx.WORD_RE.finditer(text):
            head = lx.lemma(match.group(0), vocab)
            if head in heads and free(match.start(), match.end()):
                word, definition = heads[head]
                spans.append((match.start(), match.end(), word, definition))
                taken.append((match.start(), match.end()))

    return sorted(spans)


def render_prose(prose: str, glossary: list, vocab: set) -> str:
    """Prose as HTML paragraphs, with taught words marked and defined inline."""
    out = []
    for block in re.split(r"\n\s*\n", prose.strip()):
        text = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if not text:
            continue
        spans = find_spans(text, glossary, vocab)
        pieces, cursor = [], 0
        for start, end, _word, definition in spans:
            pieces.append(html.escape(text[cursor:start]))
            surface = html.escape(text[start:end])
            pieces.append(
                f'<span class="gloss" role="button" tabindex="0" aria-expanded="false">{surface}'
                f'<span class="def">{html.escape(definition)}</span></span>'
            )
            cursor = end
        pieces.append(html.escape(text[cursor:]))
        out.append("<p>" + "".join(pieces) + "</p>")
    return "\n".join(out)


NUMBERED_RE = re.compile(r"^\s*\d+\.\s+(.*\S)\s*$", re.MULTILINE)


def parse_questions(section: str):
    head, _, tail = section.partition("<details>")
    return NUMBERED_RE.findall(head), NUMBERED_RE.findall(tail)


def slug(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0] + ".html"


def reading_minutes(words: int) -> int:
    # Graded readers are read slowly and deliberately; 120 wpm, minimum 1.
    return max(1, round(words / 120))


def story_page(story: dict, level: str, vocab: set, prev, nxt, levels) -> str:
    words = lx.count_words(story["prose"])
    meta = story["meta"]
    body = [
        f'<span class="badge">{level}</span>',
        f"<h1>{html.escape(story['title'])}</h1>",
        f'<p class="meta">{words} words<span class="dot">&middot;</span>'
        f'about {reading_minutes(words)} min<span class="dot">&middot;</span>'
        f'{len(story["glossary"])} new words<span class="dot">&middot;</span>'
        f'{html.escape(str(meta.get("topic", "")))}</p>',
        f'<article class="story">{render_prose(story["prose"], story["glossary"], vocab)}</article>',
    ]

    if story["glossary"]:
        items = "".join(
            f'<li><span class="w">{html.escape(w)}</span> — <span class="d">{html.escape(d)}</span></li>'
            for w, d in story["glossary"]
        )
        body.append(f"<h2>New words</h2><ul class=\"glossary\">{items}</ul>")

    questions, answers = parse_questions(story["sections"].get("questions", ""))
    if questions:
        qs = "".join(f"<li>{html.escape(q)}</li>" for q in questions)
        body.append(f'<h2>Questions</h2><ol class="questions">{qs}</ol>')
        if answers:
            as_ = "".join(f"<li>{html.escape(a)}</li>" for a in answers)
            body.append(
                f'<details><summary>Show answers</summary><ol class="questions">{as_}</ol></details>'
            )

    pager = []
    if prev:
        pager.append(
            f'<a href="{slug(prev["path"])}"><div class="dir">Previous</div>'
            f'<div class="t">{html.escape(prev["title"])}</div></a>'
        )
    if nxt:
        pager.append(
            f'<a class="next" href="{slug(nxt["path"])}"><div class="dir">Next</div>'
            f'<div class="t">{html.escape(nxt["title"])}</div></a>'
        )
    if pager:
        body.append(f'<nav class="pager">{"".join(pager)}</nav>')

    return page(f"{story['title']} — {level}", "\n".join(body), depth=1, active=level, levels=levels)


def level_page(level: str, stories: list, config: dict, levels) -> str:
    cfg = config["levels"][level]
    cards = "".join(
        f'<li><a class="card" href="{slug(s["path"])}">'
        f'<div class="num">{i:02d}</div>'
        f'<div class="title">{html.escape(s["title"])}</div>'
        f'<div class="sub">{lx.count_words(s["prose"])} words &middot; '
        f'{len(s["glossary"])} new words &middot; {html.escape(str(s["meta"].get("topic", "")))}</div>'
        f"</a></li>"
        for i, s in enumerate(stories, start=1)
    )
    taught = sum(len(s["glossary"]) for s in stories)
    cast = []
    for s in stories:
        for c in s["meta"].get("characters", []):
            if c not in cast:
                cast.append(c)

    body = [
        f'<span class="badge">{level}</span>',
        f"<h1>{LEVEL_BLURB[level]}</h1>",
        f'<p class="lede">{len(stories)} stories, read in order. '
        f'{cfg["word_count"]["min"]}–{cfg["word_count"]["max"]} words each, '
        f'up to {cfg["new_word_budget"]} new words per story, {taught} taught in total.</p>',
        f'<ul class="cards">{cards}</ul>' if stories else "<p>No stories at this level yet.</p>",
    ]
    if cast:
        body.append(
            "<h2>The people in these stories</h2>"
            f"<p>{html.escape(', '.join(cast))}. They come back from story to story, so you "
            "get to know them instead of meeting new names every time.</p>"
        )
    if stories:
        body.append(f'<p style="margin-top:32px"><a href="vocabulary.html">All {taught} words taught at {level} &rarr;</a></p>')
    return page(f"{level} — {LEVEL_BLURB[level]}", "\n".join(body), depth=1, active=level, levels=levels)


def vocabulary_page(level: str, stories: list, levels) -> str:
    rows = []
    for word, definition, title, filename in sorted(
        (w, d, s["title"], slug(s["path"])) for s in stories for w, d in s["glossary"]
    ):
        rows.append(
            f"<tr><td><strong>{html.escape(word)}</strong></td><td>{html.escape(definition)}</td>"
            f'<td><a href="{filename}">{html.escape(title)}</a></td></tr>'
        )
    body = [
        f'<span class="badge">{level}</span>',
        "<h1>Words taught at this level</h1>",
        f'<p class="lede">{len(rows)} words, each taught once. No story repeats a word '
        "that an earlier story already taught.</p>",
        '<div class="scroll"><table><thead><tr><th>Word</th><th>Meaning</th><th>Taught in</th>'
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>",
    ]
    return page(f"{level} vocabulary", "\n".join(body), depth=1, active=level, wide=True, levels=levels)


def home_page(config: dict, all_stories: dict, levels) -> str:
    cards = []
    for level in config["order"]:
        stories = all_stories.get(level, [])
        taught = sum(len(s["glossary"]) for s in stories)
        sub = (
            f"{len(stories)} stories &middot; {taught} words taught"
            if stories else "Coming later"
        )
        cards.append(
            f'<li><a class="card" href="{level}/">'
            f'<div class="num">{level}</div>'
            f'<div class="title">{LEVEL_BLURB[level]}</div>'
            f'<div class="sub">{sub}</div></a></li>'
        )
    body = [
        "<h1>English Stories</h1>",
        '<p class="lede">Short stories for adult English learners, graded by CEFR level. '
        "Every story stays inside the vocabulary and grammar of its level, and teaches a "
        "small set of new words — marked in the text, so you can see what a word means "
        "where you meet it.</p>",
        f'<ul class="cards">{"".join(cards)}</ul>',
        "<h2>How to use them</h2>",
        "<p>Start at your level and read in order: within a level the stories get a little "
        "longer, and each one builds on the words taught before it. Read once without "
        "stopping, then read again and tap the <span class=\"gloss\" aria-expanded=\"false\">"
        "underlined words<span class=\"def\">Like this — tap or hover to see what a word means."
        "</span></span> you did not know. The questions at the end are there to check you "
        "followed the story, not to test your grammar.</p>",
    ]
    return page("English Stories", "\n".join(body), depth=0, levels=levels)


def main() -> int:
    config = lx.load_config()
    levels = config["order"]

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    with open(os.path.join(OUT, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(STYLE)

    all_stories = {}
    pages = 1  # home
    for level in levels:
        stories = [lx.load_story(p) for p in lx.story_files(level)]
        all_stories[level] = stories
        level_dir = os.path.join(OUT, level)
        os.makedirs(level_dir, exist_ok=True)

        known = lx.load_cumulative_wordlist(level, levels)
        vocab = set(known) | lx.load_names()
        for story in stories:
            for word, _ in story["glossary"]:
                vocab.update(word.lower().split())

        with open(os.path.join(level_dir, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(level_page(level, stories, config, levels))
        pages += 1

        if stories:
            with open(os.path.join(level_dir, "vocabulary.html"), "w", encoding="utf-8") as fh:
                fh.write(vocabulary_page(level, stories, levels))
            pages += 1

        for index, story in enumerate(stories):
            prev = stories[index - 1] if index else None
            nxt = stories[index + 1] if index + 1 < len(stories) else None
            with open(os.path.join(level_dir, slug(story["path"])), "w", encoding="utf-8") as fh:
                fh.write(story_page(story, level, vocab, prev, nxt, levels))
            pages += 1

    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(home_page(config, all_stories, levels))

    print(f"built {pages} pages into {os.path.relpath(OUT, lx.ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
