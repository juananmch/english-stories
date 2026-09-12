import importlib.util
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))


def _load_tool(name: str):
    # tools/site.py shadows the stdlib `site` module, so it has to be loaded by path.
    spec = importlib.util.spec_from_file_location(f"tool_{name}", os.path.join(ROOT, "tools", f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


site = _load_tool("site")

APARTMENT = ("apartment", "a set of rooms to live in")
TIRED = ("tired", "needing rest")


def cards(prose, glossary):
    vocab = {w for word, _ in glossary for w in word.lower().split()}
    return site.cloze_cards(prose, glossary, vocab)


class ClozeCardsTest(unittest.TestCase):
    def test_extracts_only_the_sentence_containing_the_word(self):
        prose = "Laura opened the door. The apartment was small but clean. She smiled."
        [card] = cards(prose, [APARTMENT])
        self.assertEqual(card["word"], "apartment")
        self.assertEqual(card["definition"], "a set of rooms to live in")
        self.assertEqual(card["before"], "The ")
        self.assertEqual(card["answer"], "apartment")
        self.assertEqual(card["after"], " was small but clean.")

    def test_uses_the_first_occurrence(self):
        prose = "The apartment was cold. Later, the apartment was warm."
        [card] = cards(prose, [APARTMENT])
        self.assertEqual(card["after"], " was cold.")

    def test_keeps_the_inflected_surface_form(self):
        prose = "They looked at two apartments. Both were expensive."
        [card] = cards(prose, [APARTMENT])
        self.assertEqual(card["before"], "They looked at two ")
        self.assertEqual(card["answer"], "apartments")
        self.assertEqual(card["after"], ".")

    def test_dialogue_sentence_ending_in_a_closing_quote(self):
        prose = 'He waited. "This apartment is perfect," said Laura. She laughed.'
        [card] = cards(prose, [APARTMENT])
        self.assertEqual(card["before"], '"This ')
        self.assertEqual(card["after"], ' is perfect," said Laura.')

    def test_title_abbreviation_is_not_a_sentence_boundary(self):
        prose = "Mr. Reyes showed them the apartment. It was bright."
        [card] = cards(prose, [APARTMENT])
        self.assertEqual(card["before"], "Mr. Reyes showed them the ")
        self.assertEqual(card["after"], ".")

    def test_multi_word_entry_is_blanked_as_a_whole(self):
        prose = "She bought ice cream for everyone. It melted fast."
        [card] = cards(prose, [("ice cream", "frozen sweet food")])
        self.assertEqual(card["before"], "She bought ")
        self.assertEqual(card["answer"], "ice cream")
        self.assertEqual(card["after"], " for everyone.")

    def test_cards_follow_glossary_order_not_prose_order(self):
        prose = "She was tired. The apartment was quiet."
        result = cards(prose, [APARTMENT, TIRED])
        self.assertEqual([c["word"] for c in result], ["apartment", "tired"])

    def test_word_absent_from_prose_yields_no_card(self):
        self.assertEqual(cards("Nothing to see here.", [("elevator", "a lift")]), [])

    def test_quotation_spanning_two_sentences_stays_whole(self):
        prose = '"We have a backup. It takes a minute to restore the apartment file," he said.'
        [card] = cards(prose, [APARTMENT])
        self.assertEqual(card["before"], '"We have a backup. It takes a minute to restore the ')
        self.assertEqual(card["after"], ' file," he said.')

    def test_attribution_after_a_closing_quote_stays_attached(self):
        prose = 'She looked around. "What an apartment!" she said. Then she sat down.'
        [card] = cards(prose, [APARTMENT])
        self.assertEqual(card["before"], '"What an ')
        self.assertEqual(card["after"], '!" she said.')

    def test_taught_word_at_the_start_of_a_sentence(self):
        prose = "She smiled. Apartments here are cheap. He nodded."
        [card] = cards(prose, [APARTMENT])
        self.assertEqual(card["before"], "")
        self.assertEqual(card["answer"], "Apartments")
        self.assertEqual(card["after"], " here are cheap.")

    def test_hyphenated_entry_is_found_and_blanked_whole(self):
        prose = "She did it single-handedly. Nobody helped."
        [card] = cards(prose, [("single-handedly", "alone, without help")])
        self.assertEqual(card["before"], "She did it ")
        self.assertEqual(card["answer"], "single-handedly")
        self.assertEqual(card["after"], ".")

    def test_finds_words_in_later_paragraphs_with_wrapped_lines(self):
        prose = "First paragraph here.\n\nThe apartment was on\nthe third floor. It had a view."
        [card] = cards(prose, [APARTMENT])
        self.assertEqual(card["before"], "The ")
        self.assertEqual(card["after"], " was on the third floor.")


class RenderReviewTest(unittest.TestCase):
    def test_no_cards_renders_nothing(self):
        self.assertEqual(site.render_review([]), "")

    def test_card_is_a_details_block_with_blank_and_answer(self):
        html = site.render_review([
            {"word": "apartment", "definition": "rooms <to> live in",
             "before": "The ", "answer": "apartment", "after": " was small."},
        ])
        self.assertIn('<section class="review">', html)
        self.assertIn('<details class="cloze">', html)
        self.assertIn('<summary>The <span class="blank" data-answer="apartment"></span> was small.</summary>', html)
        self.assertIn("<strong>apartment</strong>", html)
        self.assertIn("rooms &lt;to&gt; live in", html)
        self.assertNotIn("<to>", html)


class StoryPageTest(unittest.TestCase):
    def story(self, glossary):
        return {
            "path": "A1/01-test.md",
            "title": "A Test",
            "meta": {"topic": "testing"},
            "prose": "The apartment was small. Laura liked it.",
            "glossary": glossary,
            "sections": {"questions": "1. Was it big?\n<details>\n1. No.\n</details>"},
        }

    def test_review_sits_after_questions_and_before_pager(self):
        vocab = {"apartment"}
        nxt = {"path": "A1/02-next.md", "title": "Next"}
        html = site.story_page(self.story([APARTMENT]), "A1", vocab, None, nxt, ["A1"])
        questions = html.index("<h2>Questions</h2>")
        review = html.index('<section class="review">')
        pager = html.index('<nav class="pager">')
        self.assertLess(questions, review)
        self.assertLess(review, pager)

    def test_no_review_when_nothing_is_taught(self):
        html = site.story_page(self.story([]), "A1", set(), None, None, ["A1"])
        self.assertNotIn('class="review"', html)


if __name__ == "__main__":
    unittest.main()
