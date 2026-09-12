"""Tests for tools/audit.py, the wordlist-audit helper that proposes headwords
from the frequency table for a level's curation pass."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import audit  # noqa: E402

ROWS = [
    (1, "you", 900), (2, "I", 890), (3, "the", 880), (4, "s", 870), (5, "walked", 860),
    (6, "Jack", 850), (7, "parents", 840), (8, "parent", 830), (9, "quickly", 820),
    (10, "event", 810), (11, "events", 800), (12, "don", 790), (13, "Okay", 780),
    (14, "bakery", 770), (15, "bakeries", 760), (16, "clothes", 750), (17, "cloth", 740),
    (18, "salaries", 730), (19, "salary", 720),
    # Shorter surface forms that are not the dictionary form of the frequent word.
    (30, "power", 700), (31, "pow", 690), (32, "arrest", 680), (33, "ar", 670),
    (34, "gas", 660), (35, "ga", 650), (36, "bit", 640), (37, "bite", 630),
    (38, "stopped", 620), (39, "stop", 610), (40, "houses", 600), (41, "house", 590),
    (99, "beyond", 10),
]
KNOWN = {"you", "i", "the", "walk", "quick"}


class ProposeTest(unittest.TestCase):
    def setUp(self):
        self.result = audit.propose(ROWS, KNOWN, limit=20)

    def test_new_headwords_in_rank_order_with_the_surface_that_earned_them(self):
        self.assertEqual(
            self.result["new"],
            [(7, "parents", "parent"), (10, "event", "event"), (14, "bakery", "bakery"),
             (16, "clothes", "cloth"), (18, "salaries", "salary")],
        )

    def test_a_plural_that_outranks_its_singular_proposes_the_singular(self):
        heads = [head for _rank, _surface, head in self.result["new"]]
        self.assertIn("parent", heads)
        self.assertNotIn("parents", heads)

    def test_only_plain_inflections_fold_onto_a_shorter_surface_form(self):
        # -er/-est stripping, two-letter stems and the irregular map all find a
        # real surface form that is not the dictionary form of the word.
        result = audit.propose(ROWS, KNOWN, limit=41)
        folds = {surface: head for _rank, surface, head in result["new"]}
        self.assertEqual(folds["power"], "power")
        self.assertEqual(folds["arrest"], "arrest")
        self.assertEqual(folds["gas"], "gas")
        self.assertEqual(folds["bit"], "bit")
        self.assertEqual(folds["stopped"], "stop")
        self.assertEqual(folds["houses"], "house")
        self.assertIn("bite", folds)

    def test_later_inflections_of_an_accepted_headword_are_absorbed(self):
        surfaces = [surface for _rank, surface, _head in self.result["new"]]
        self.assertNotIn("parent", surfaces)
        self.assertNotIn("events", surfaces)
        self.assertNotIn("bakeries", surfaces)
        self.assertNotIn("cloth", surfaces)

    def test_derivations_of_known_words_are_listed_separately(self):
        self.assertEqual(self.result["derived"], [(9, "quickly", "quick")])

    def test_plain_inflections_of_known_words_are_silent(self):
        for section in self.result.values():
            self.assertNotIn("walked", [row[1] for row in section])

    def test_capitalized_unknowns_are_set_aside_for_review(self):
        self.assertEqual(self.result["capitalized"], [(6, "Jack"), (13, "Okay")])

    def test_apostrophe_fragments_are_dropped(self):
        for section in self.result.values():
            self.assertNotIn("s", [row[1] for row in section])
            self.assertNotIn("don", [row[1] for row in section])

    def test_rows_beyond_the_limit_are_ignored(self):
        for section in self.result.values():
            self.assertNotIn("beyond", [row[1] for row in section])

    def test_inflection_stems(self):
        self.assertEqual(audit.inflection_stems("parents"), ["parent"])
        self.assertEqual(audit.inflection_stems("salaries"), ["salary", "salarie"])
        self.assertEqual(audit.inflection_stems("movies"), ["movy", "movie"])
        self.assertEqual(audit.inflection_stems("stopped"), ["stopp", "stoppe", "stop"])
        self.assertEqual(audit.inflection_stems("wanted"), ["want", "wante"])
        # A one-syllable CVC base would have doubled its consonant, so it is
        # not offered: scared is scare+d, not scar+ed.
        self.assertEqual(audit.inflection_stems("scared"), ["scare"])
        self.assertEqual(audit.inflection_stems("staring"), ["stare"])
        # Words ending in -ss are not plurals.
        self.assertEqual(audit.inflection_stems("mass"), [])
        self.assertEqual(audit.inflection_stems("princess"), [])
        # The silent-e base is tried before the bare stem for -es.
        self.assertEqual(audit.inflection_stems("bones"), ["bone", "bon"])
        self.assertEqual(audit.inflection_stems("boxes"), ["boxe", "box"])
        # -ying is -ie + ing: dying, lying, tying.
        self.assertEqual(audit.inflection_stems("dying"), ["die", "dye"])
        # Nothing shorter than three letters.
        self.assertEqual(audit.inflection_stems("gas"), [])

    def test_headword_count_at_each_cutoff(self):
        # How many headwords the level would have if every candidate up to the
        # cutoff were accepted — the number the curation pass sizes itself by.
        self.assertEqual(audit.headword_counts(ROWS, KNOWN, [8, 12, 20]), [(8, 6), (12, 7), (20, 10)])


if __name__ == "__main__":
    unittest.main()
