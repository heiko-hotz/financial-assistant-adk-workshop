import re
import unittest

from module_02.rag_lab import (
    STRATEGIES,
    Passage,
    Question,
    evidence_hits,
    load_corpus,
    load_questions,
    pack_context,
    split_document,
)


class RetrievalLabTest(unittest.TestCase):
    def test_all_strategies_partition_the_source_without_losing_words(self):
        for source, text in load_corpus().items():
            expected = {(source, word.start()) for word in re.finditer(r"\S+", text)}
            for strategy in STRATEGIES:
                with self.subTest(source=source, strategy=strategy):
                    chunks = list(split_document(source, text, strategy))
                    self.assertEqual(sum(chunk.word_count for chunk in chunks), len(expected))
                    actual = {word for chunk in chunks for word in chunk.word_positions()}
                    self.assertEqual(actual, expected)
                    for chunk in chunks:
                        self.assertEqual(chunk.text, text[chunk.start:chunk.end])

    def test_section_chunks_keep_headings_separate(self):
        text = "1. First section\n\nFirst paragraph.\n\n2. Next section\n\nNext paragraph."
        self.assertEqual(
            [chunk.text for chunk in split_document("sample.txt", text, "sections")],
            ["1. First section\n\nFirst paragraph.", "2. Next section\n\nNext paragraph."],
        )

    def test_last_ranked_chunk_is_clipped_and_only_visible_words_score(self):
        first = Passage("policy.txt", 0, "The limit")
        second = Passage("policy.txt", 10, "is five percent.")
        question = Question("cap", "What is the limit?", (Passage("policy.txt", 0, "The limit is five percent."),))

        clipped = pack_context([first, second], 4)
        self.assertEqual([chunk.text for chunk in clipped], ["The limit", "is five"])
        self.assertEqual(evidence_hits(clipped, question), [False])
        self.assertEqual(evidence_hits(pack_context([first, second], 5), question), [True])

    def test_same_words_in_a_different_document_do_not_count(self):
        passage = Passage("policy.txt", 0, "The limit is five percent.")
        question = Question("cap", "What is the limit?", (passage,))
        distractor = Passage("outlook.txt", 0, passage.text)
        self.assertEqual(evidence_hits([distractor], question), [False])

    def test_question_ids_are_unique_and_every_question_has_evidence(self):
        questions = list(load_questions(load_corpus()))
        self.assertEqual(len(questions), len({question.id for question in questions}))
        self.assertTrue(questions)
        self.assertTrue(all(question.evidence for question in questions))


if __name__ == "__main__":
    unittest.main()
