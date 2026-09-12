"""Characterization tests for the vocabulary checks in tools/validate.py.

Each test builds a tiny repository in a temporary directory — wordlists, a cast,
and one or two stories per level — points the lexicon loaders at it, and runs
check_level on it. The real 60 stories are not used: they can only show that the
content agrees with the tools, not that the tools enforce what they claim to.
"""

import os
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import lexicon as lx  # noqa: E402
import validate  # noqa: E402

CONFIG = {
    "order": ["A1", "A2", "C2"],
    "levels": {
        "A1": {"word_count": {"min": 1, "max": 1000}, "new_word_budget": 3},
        "A2": {"word_count": {"min": 1, "max": 1000}, "new_word_budget": 3},
        "C2": {"word_count": {"min": 1, "max": 1000}, "new_word_budget": 3},
    },
    "us_english": {},
}

A1_WORDS = "a the is was he she it to and in not do go cat dog walk stop like eat bread big small good day"
A2_WORDS = "often maybe"
NAMES = "Laura Elena"


def story_text(level, title, prose, glossary):
    lines = [
        "---",
        f"level: {level}",
        f"title: {title}",
        "topic: test",
        "grammar: []",
        "characters: []",
        "---",
        "",
        f"# {title}",
        "",
        textwrap.dedent(prose).strip(),
        "",
        "## New Words",
        "",
    ]
    lines += [f"- **{word}** — {definition}" for word, definition in glossary]
    lines += ["", "## Questions", "", "1. Who?", ""]
    return "\n".join(lines)


class ValidateVocabularyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self._saved = (lx.ROOT, lx.WORDLIST_DIR)
        lx.ROOT = self.root
        lx.WORDLIST_DIR = os.path.join(self.root, "wordlists")
        self.addCleanup(self._restore)
        self.write("wordlists/A1.txt", A1_WORDS)
        self.write("wordlists/A2.txt", A2_WORDS)
        self.write("wordlists/names.txt", NAMES)

    def _restore(self):
        lx.ROOT, lx.WORDLIST_DIR = self._saved

    def write(self, rel, text):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")

    def story(self, level, number, prose, glossary=()):
        title = f"Story {number}"
        rel = f"{level}/{number:02d}-story.md"
        self.write(rel, story_text(level, title, prose, list(glossary)))
        return rel

    def findings(self, level):
        # A story with no glossary is a 'structure' finding; several tests here
        # need such a story, and structure is not what this module is about.
        findings, _count = validate.check_level(level, CONFIG)
        return [f for f in findings if f.check != "structure"]

    def checks(self, level):
        return sorted({(f.story, f.check) for f in self.findings(level)})

    def messages(self, level, check):
        return [f.message for f in self.findings(level) if f.check == check]

    # --- baseline ---

    def test_a_story_inside_the_contract_has_no_findings(self):
        self.story("A1", 1, "Laura likes bread. She walks to the bakery in the day. The bakery is small.",
                   [("bakery", "a shop that sells bread")])
        self.assertEqual(self.findings("A1"), [])

    def test_story_count_is_reported(self):
        self.story("A1", 1, "Laura likes bread.")
        self.story("A1", 2, "Elena likes bread.")
        _findings, count = validate.check_level("A1", CONFIG)
        self.assertEqual(count, 2)

    # --- ceiling ---

    def test_ceiling_flags_an_undeclared_word_above_the_level(self):
        rel = self.story("A1", 1, "Laura likes the enormous cat.")
        self.assertEqual(self.checks("A1"), [(rel, "ceiling")])
        self.assertIn("'enormous'", self.messages("A1", "ceiling")[0])

    def test_ceiling_reports_an_unresolvable_word_as_its_own_lemma(self):
        # 'wander' is not in any wordlist or glossary, so there is nothing for
        # the lemmatizer to resolve against and the surface form is reported.
        self.story("A1", 1, "Laura wandered to the cat.")
        self.assertIn("'wandered' (lemma 'wandered')", self.messages("A1", "ceiling")[0])

    def test_ceiling_accepts_inflections_of_known_words(self):
        self.story("A1", 1, "Laura walked to the dogs. She liked the biggest dog. It stopped.")
        self.assertEqual(self.findings("A1"), [])

    def test_ceiling_accepts_registered_names_and_flags_unregistered_ones(self):
        rel = self.story("A1", 1, "Laura and Marcus walk to the dog.")
        self.assertEqual(self.checks("A1"), [(rel, "ceiling")])
        self.assertIn("'Marcus'", self.messages("A1", "ceiling")[0])

    def test_ceiling_accepts_a_declared_word_and_its_inflections(self):
        self.story("A1", 1, "Laura wandered to the cat. The cat wanders in the day.",
                   [("wander", "to walk with no plan")])
        self.assertEqual(self.findings("A1"), [])

    def test_ceiling_accepts_every_part_of_a_multi_word_entry(self):
        self.story("A1", 1, "Laura did not give up. She likes the cat.",
                   [("give up", "to stop trying")])
        self.assertEqual(self.findings("A1"), [])

    def test_ceiling_accepts_a_word_taught_by_an_earlier_story_at_the_level(self):
        self.story("A1", 1, "Laura walks to the bakery.", [("bakery", "a shop that sells bread")])
        self.story("A1", 2, "Elena likes the bakeries. The dog likes bread.")
        self.assertEqual(self.findings("A1"), [])

    def test_ceiling_does_not_accept_a_word_taught_by_a_later_story(self):
        first = self.story("A1", 1, "Elena likes the bakeries.")
        self.story("A1", 2, "Laura walks to the bakery.", [("bakery", "a shop that sells bread")])
        self.assertIn((first, "ceiling"), self.checks("A1"))
        # The later glossary is still vocabulary for the lemmatizer, so the
        # finding names the headword the reader will eventually be taught.
        self.assertIn("'bakeries' (lemma 'bakery')", self.messages("A1", "ceiling")[0])

    def test_ceiling_accepts_a_word_taught_at_a_lower_level(self):
        self.story("A1", 1, "Laura walks to the bakery.", [("bakery", "a shop that sells bread")])
        self.story("A2", 1, "Elena often walks to the bakery.")
        self.assertEqual(self.findings("A2"), [])

    def test_ceiling_accepts_the_lower_levels_wordlists(self):
        self.story("A2", 1, "Elena often walks to the dog. Maybe the cat likes bread.")
        self.assertEqual(self.findings("A2"), [])

    def test_ceiling_is_not_applied_at_an_unrestricted_level(self):
        self.story("C2", 1, "Elena perambulated toward the ineffable bakery.",
                   [("perambulate", "to walk about")])
        self.assertNotIn("ceiling", {f.check for f in self.findings("C2")})

    # --- budget ---

    def test_budget_allows_exactly_the_configured_number_of_words(self):
        self.story("A1", 1, "Laura wandered to the bakery. She was famished.",
                   [("wander", "to walk with no plan"), ("bakery", "a shop that sells bread"),
                    ("famished", "very hungry")])
        self.assertEqual(self.findings("A1"), [])

    def test_budget_flags_one_word_too_many(self):
        rel = self.story("A1", 1, "Laura wandered to the bakery. She was famished and exhausted.",
                        [("wander", "to walk with no plan"), ("bakery", "a shop that sells bread"),
                         ("famished", "very hungry"), ("exhausted", "very tired")])
        self.assertEqual(self.checks("A1"), [(rel, "budget")])
        self.assertIn("declares 4 words, budget is 3", self.messages("A1", "budget")[0])

    # --- glossary ---

    def test_glossary_flags_a_declared_word_that_is_not_in_the_prose(self):
        rel = self.story("A1", 1, "Laura likes the cat.", [("bakery", "a shop that sells bread")])
        self.assertEqual(self.checks("A1"), [(rel, "glossary")])
        self.assertIn("'bakery' does not appear", self.messages("A1", "glossary")[0])

    def test_glossary_accepts_an_inflected_occurrence(self):
        self.story("A1", 1, "Laura wandered to the cat.", [("wander", "to walk with no plan")])
        self.assertEqual(self.findings("A1"), [])

    def test_glossary_accepts_a_multi_word_entry_present_as_a_phrase(self):
        self.story("A1", 1, "Laura did not give up.", [("give up", "to stop trying")])
        self.assertEqual(self.findings("A1"), [])

    def test_glossary_rejects_a_multi_word_entry_whose_parts_are_split(self):
        rel = self.story("A1", 1, "Laura did not give it up.", [("give up", "to stop trying")])
        self.assertEqual(self.checks("A1"), [(rel, "glossary")])

    # --- reteach ---

    def test_reteach_flags_a_word_taught_earlier_at_the_same_level(self):
        first = self.story("A1", 1, "Laura walks to the bakery.", [("bakery", "a shop that sells bread")])
        second = self.story("A1", 2, "Elena likes the bakery.", [("bakery", "a shop that sells bread")])
        # A word taught earlier necessarily appeared earlier, so teach-late
        # fires alongside reteach within one level.
        self.assertEqual(self.checks("A1"), [(second, "reteach"), (second, "teach-late")])
        self.assertIn(f"already taught in {first}", self.messages("A1", "reteach")[0])

    def test_reteach_flags_a_word_taught_at_a_lower_level(self):
        first = self.story("A1", 1, "Laura walks to the bakery.", [("bakery", "a shop that sells bread")])
        second = self.story("A2", 1, "Elena often likes the bakery.", [("bakery", "a shop that sells bread")])
        self.assertEqual(self.checks("A2"), [(second, "reteach")])
        self.assertIn(f"lower level in {first}", self.messages("A2", "reteach")[0])

    def test_reteach_is_evaded_by_declaring_a_different_surface_form(self):
        # The declared surface is itself vocabulary, and a known surface always
        # wins over a stem, so 'wanders' is a distinct entry from 'wander'. This
        # is what lets 'friendly', 'trainer' or 'gradually' be taught as their
        # own words next to 'friend', 'train' and 'gradual'; the price is that
        # a plain inflection declared as new is not caught either.
        self.story("A1", 1, "Laura wandered to the cat.", [("wander", "to walk with no plan")])
        self.story("A1", 2, "Elena wanders in the day.", [("wanders", "walks with no plan")])
        self.assertEqual(self.findings("A1"), [])

    # --- teach-late ---

    def test_teach_late_flags_a_word_that_already_appeared_in_an_earlier_story(self):
        first = self.story("A1", 1, "Elena likes the bakery.")
        second = self.story("A1", 2, "Laura walks to the bakery.", [("bakery", "a shop that sells bread")])
        self.assertIn((second, "teach-late"), self.checks("A1"))
        self.assertIn(f"already appeared in {first}", self.messages("A1", "teach-late")[0])

    def test_teach_late_is_not_raised_for_the_story_that_teaches_the_word(self):
        self.story("A1", 1, "Laura walks to the bakery. The bakery is small.",
                   [("bakery", "a shop that sells bread")])
        self.assertEqual(self.findings("A1"), [])

    # --- known ---

    def test_known_flags_a_word_from_a_lower_levels_wordlist(self):
        rel = self.story("A2", 1, "Elena often likes the cat.", [("cat", "a small animal")])
        self.assertEqual(self.checks("A2"), [(rel, "known")])
        self.assertIn("already assumed known below A2", self.messages("A2", "known")[0])

    def test_known_flags_a_word_from_the_levels_own_wordlist(self):
        rel = self.story("A1", 1, "Laura likes the cat.", [("cat", "a small animal")])
        self.assertEqual(self.checks("A1"), [(rel, "known")])
        self.assertIn("wordlists/A1.txt itself", self.messages("A1", "known")[0])

    def test_known_is_evaded_by_declaring_a_different_surface_form(self):
        # Same trade-off as for reteach: 'cats' is its own entry once declared.
        self.story("A2", 1, "Elena often likes the cats.", [("cats", "small animals")])
        self.assertEqual(self.findings("A2"), [])

    def test_known_still_fires_when_the_prose_uses_the_inflected_form(self):
        # Only the declared spelling is protected; the entry is keyed on its
        # own lemma, so declaring the headword 'cat' is caught however the
        # prose inflects it.
        rel = self.story("A2", 1, "Elena often likes the cats.", [("cat", "a small animal")])
        self.assertEqual(self.checks("A2"), [(rel, "known")])


if __name__ == "__main__":
    unittest.main()
