import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import lexicon as lx  # noqa: E402


def lem(word, *vocab):
    return lx.lemma(word, set(vocab))


class LemmaTest(unittest.TestCase):
    def test_surface_form_wins_when_it_is_itself_known(self):
        self.assertEqual(lem("glasses", "glass", "glasses"), "glasses")
        self.assertEqual(lem("news", "new", "news"), "news")

    def test_unknown_word_is_returned_unchanged(self):
        self.assertEqual(lx.lemma("stopped"), "stopped")
        self.assertEqual(lem("stopped", "walk"), "stopped")

    def test_regular_inflections(self):
        self.assertEqual(lem("cities", "city"), "city")
        self.assertEqual(lem("tried", "try"), "try")
        self.assertEqual(lem("happier", "happy"), "happy")
        self.assertEqual(lem("happiest", "happy"), "happy")
        self.assertEqual(lem("happily", "happy"), "happy")
        self.assertEqual(lem("boxes", "box"), "box")
        self.assertEqual(lem("watches", "watch"), "watch")
        self.assertEqual(lem("dishes", "dish"), "dish")
        self.assertEqual(lem("classes", "class"), "class")
        self.assertEqual(lem("stopped", "stop"), "stop")
        self.assertEqual(lem("running", "run"), "run")
        self.assertEqual(lem("hoped", "hope"), "hope")
        self.assertEqual(lem("making", "make"), "make")
        self.assertEqual(lem("walked", "walk"), "walk")
        self.assertEqual(lem("slowly", "slow"), "slow")

    def test_derivations(self):
        self.assertEqual(lem("invitation", "invite"), "invite")
        self.assertEqual(lem("investment", "invest"), "invest")
        self.assertEqual(lem("argument", "argue"), "argue")
        self.assertEqual(lem("reasonably", "reasonable"), "reasonable")
        self.assertEqual(lem("basically", "basic"), "basic")
        self.assertEqual(lem("dramatically", "dramatic"), "dramatic")

    def test_irregular_forms(self):
        self.assertEqual(lem("went", "go"), "go")
        self.assertEqual(lem("was", "be"), "be")
        self.assertEqual(lem("taken", "take"), "take")
        self.assertEqual(lem("didn't", "do"), "do")
        self.assertEqual(lem("won't", "will", "win"), "will")

    def test_possessives_and_contractions(self):
        self.assertEqual(lem("dog's", "dog"), "dog")
        self.assertEqual(lem("teacher's", "teacher"), "teacher")
        self.assertEqual(lem("driver's", "driver", "drive"), "driver")
        self.assertEqual(lem("she's", "she"), "she")


class LemmaAmbiguityTest(unittest.TestCase):
    """When more than one candidate is a known word, the choice must be the base
    form the surface was actually built from. Every case here is a real token
    from the corpus that used to resolve to the wrong known word."""

    def test_silent_e_base_beats_bare_stem_after_a_vowel_suffix(self):
        self.assertEqual(lem("caring", "car", "care"), "care")
        self.assertEqual(lem("cared", "car", "care"), "care")
        self.assertEqual(lem("noting", "not", "note"), "note")
        self.assertEqual(lem("noted", "not", "note"), "note")
        self.assertEqual(lem("used", "us", "use"), "use")
        self.assertEqual(lem("hoping", "hop", "hope"), "hope")
        self.assertEqual(lem("staring", "star", "stare"), "stare")
        self.assertEqual(lem("later", "lat", "late"), "late")

    def test_bare_stem_still_wins_when_it_is_the_real_base(self):
        self.assertEqual(lem("cooking", "cook", "cooke"), "cook")
        self.assertEqual(lem("asked", "ask", "aske"), "ask")
        self.assertEqual(lem("opened", "open"), "open")
        self.assertEqual(lem("visited", "visit"), "visit")
        self.assertEqual(lem("hopping", "hop", "hope"), "hop")
        self.assertEqual(lem("played", "play", "playe"), "play")

    def test_plural_of_a_word_ending_in_e_keeps_the_e(self):
        self.assertEqual(lem("notes", "not", "note"), "note")
        self.assertEqual(lem("ones", "on", "one"), "one")
        self.assertEqual(lem("uses", "us", "use"), "use")
        self.assertEqual(lem("cares", "car", "care"), "care")

    def test_true_es_plurals_still_resolve(self):
        self.assertEqual(lem("buses", "bus"), "bus")
        self.assertEqual(lem("goes", "go"), "go")
        self.assertEqual(lem("tomatoes", "tomato"), "tomato")
        self.assertEqual(lem("houses", "house"), "house")

    def test_ly_adverb_prefers_the_full_adjective_over_a_shorter_stem(self):
        self.assertEqual(lem("normally", "norm", "normal"), "normal")
        self.assertEqual(lem("informally", "inform", "informal"), "informal")
        self.assertEqual(lem("professionally", "profession", "professional"), "professional")
        self.assertEqual(lem("personally", "person", "personal"), "personal")
        self.assertEqual(lem("formally", "form", "formal"), "formal")


if __name__ == "__main__":
    unittest.main()
