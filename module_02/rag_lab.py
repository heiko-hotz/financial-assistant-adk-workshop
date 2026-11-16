"""Compare three chunking strategies on the same Chroma retrieval task."""

import argparse
import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


HERE = Path(__file__).resolve().parent
STRATEGIES = ("fixed", "paragraphs", "sections")
CHUNK_WORDS = 150
CONTEXT_WORDS = 150
CANDIDATES = 20
WORD = re.compile(r"\S+")
PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")
HEADING = re.compile(r"(?m)^\d+\.[ \t]+")


@dataclass(frozen=True)
class Passage:
    source: str
    start: int
    text: str

    @property
    def end(self):
        return self.start + len(self.text)

    @property
    def word_count(self):
        return len(self.text.split())

    def word_positions(self):
        return {(self.source, self.start + word.start()) for word in WORD.finditer(self.text)}

    def label(self, corpus):
        text = corpus[self.source]
        first_line = text.count("\n", 0, self.start) + 1
        last_line = text.count("\n", 0, self.end) + 1
        return f"{self.source}:{first_line}-{last_line}"


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    evidence: tuple[Passage, ...]


def passage(source, text, start, end):
    excerpt = text[start:end]
    return Passage(source, start + len(excerpt) - len(excerpt.lstrip()), excerpt.strip())


def fixed_windows(chunk, words):
    tokens = list(WORD.finditer(chunk.text))
    for index in range(0, len(tokens), words):
        start = tokens[index].start()
        end = tokens[min(index + words, len(tokens)) - 1].end()
        yield Passage(chunk.source, chunk.start + start, chunk.text[start:end])


def paragraphs(chunk):
    start = 0
    for end in [match.start() for match in PARAGRAPH_BREAK.finditer(chunk.text)] + [len(chunk.text)]:
        paragraph = passage(chunk.source, chunk.text, start, end)
        if paragraph.text:
            yield Passage(paragraph.source, chunk.start + paragraph.start, paragraph.text)
        start = end


def section_chunks(document, max_words):
    boundaries = [0, *(match.start() for match in HEADING.finditer(document.text)), document.end]
    for section_start, section_end in zip(boundaries, boundaries[1:]):
        section = passage(document.source, document.text, section_start, section_end)
        pending = None
        words = 0
        for paragraph in paragraphs(section):
            if words + paragraph.word_count > max_words and pending is not None:
                yield pending
                pending = None
                words = 0
            if paragraph.word_count > max_words:
                yield from fixed_windows(paragraph, max_words)
                continue
            group_start = paragraph.start if pending is None else pending.start
            pending = passage(document.source, document.text, group_start, paragraph.end)
            words += paragraph.word_count
        if pending is not None:
            yield pending


def split_document(source, text, strategy, window_words=CHUNK_WORDS):
    document = Passage(source, 0, text)
    if strategy == "fixed":
        yield from fixed_windows(document, window_words)
    elif strategy == "paragraphs":
        yield from paragraphs(document)
    elif strategy == "sections":
        yield from section_chunks(document, CHUNK_WORDS)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def load_corpus():
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted((HERE / "corpus").glob("*.txt"))
    }


def load_questions(corpus):
    cases = json.loads((HERE / "evaluation.json").read_text(encoding="utf-8"))
    for case in cases:
        passages = []
        for item in case["evidence"]:
            source = item["source"]
            pattern = r"(?<!\S)" + r"\s+".join(re.escape(word) for word in item["quote"].split()) + r"(?!\S)"
            matches = list(re.finditer(pattern, corpus[source]))
            if len(matches) != 1:
                raise ValueError(f"{case['id']}: expected one match in {source} for {item['quote']!r}")
            match = matches[0]
            passages.append(Passage(source, match.start(), match.group()))
        yield Question(case["id"], case["question"], tuple(passages))


def build_indexes(corpus, strategies, window_words):
    from chromadb import EphemeralClient

    client = EphemeralClient()
    run_id = uuid4().hex[:8]
    indexes = {}
    for strategy in strategies:
        chunks = [
            chunk
            for source, text in corpus.items()
            for chunk in split_document(source, text, strategy, window_words)
        ]
        index = client.create_collection(f"rag-lab-{run_id}-{strategy}")
        index.add(
            ids=[f"{chunk.source}:{chunk.start}" for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[{"source": chunk.source, "start": chunk.start} for chunk in chunks],
        )
        indexes[strategy] = index
    return indexes


def pack_context(chunks, budget):
    """Keep ranked passages in order and clip the last one to the word budget."""
    context = []
    for chunk in chunks:
        if budget <= 0:
            break
        words = chunk.word_count
        if words > budget:
            context.append(next(fixed_windows(chunk, budget)))
            break
        context.append(chunk)
        budget -= words
    return context


def retrieve(index, question, budget):
    result = index.query(
        query_texts=[question],
        n_results=min(CANDIDATES, index.count()),
        include=["documents", "metadatas"],
    )
    ranked = [
        Passage(meta["source"], meta["start"], text)
        for text, meta in zip(result["documents"][0], result["metadatas"][0])
    ]
    return pack_context(ranked, budget)


def evidence_hits(context, question):
    visible_words = {position for chunk in context for position in chunk.word_positions()}
    return [item.word_positions() <= visible_words for item in question.evidence]


def compare(indexes, questions, budget, corpus, inspect_id):
    print(f"Context limit: {budget} words from up to {CANDIDATES} ranked chunks")
    print(f"{'Question':<25}" + "".join(f"{strategy:>13}" for strategy in indexes))
    complete = dict.fromkeys(indexes, 0)
    inspected = {}
    for question in questions:
        scores = []
        for strategy, index in indexes.items():
            context = retrieve(index, question.prompt, budget)
            hits = evidence_hits(context, question)
            complete[strategy] += all(hits)
            scores.append(f"{sum(hits)}/{len(hits)}")
            if inspect_id == question.id:
                inspected[strategy] = (question, context, hits)
        print(f"{question.id:<25}" + "".join(f"{score:>13}" for score in scores))
    print(f"{'All evidence present':<25}" + "".join(
        f"{f'{count}/{len(questions)}':>13}" for count in complete.values()
    ))
    for strategy, (question, context, hits) in inspected.items():
        print(f"\n{strategy} | {sum(chunk.word_count for chunk in context)} context words")
        for hit, item in zip(hits, question.evidence):
            status = "found" if hit else "missing"
            print(f"  {status:>7}  [{item.label(corpus)}] {' '.join(item.text.split())}")
        for chunk in context:
            print(f"\n[{chunk.label(corpus)}]\n{chunk.text}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--inspect", metavar="QUESTION_ID", help="show sources for one scored question")
    mode.add_argument("--ask", metavar="QUESTION", help="ask the live ADK analyst")
    parser.add_argument("--strategy", choices=STRATEGIES, help="choose an index for --ask")
    parser.add_argument("--budget", type=int, default=CONTEXT_WORDS, help="retrieved-context word limit")
    parser.add_argument("--window-words", type=int, default=CHUNK_WORDS, help="fixed-window size")
    args = parser.parse_args()
    if (args.ask is None) != (args.strategy is None):
        parser.error("--ask and --strategy must be used together")
    if args.budget < 1 or args.window_words < 1:
        parser.error("--budget and --window-words must be positive")

    corpus = load_corpus()
    if args.ask is None:
        questions = list(load_questions(corpus))
        if args.inspect:
            questions = [question for question in questions if question.id == args.inspect]
            if not questions:
                parser.error(f"Unknown question ID: {args.inspect}")
            print(questions[0].prompt)
        indexes = build_indexes(corpus, STRATEGIES, args.window_words)
        print("Chunks indexed: " + ", ".join(f"{name}={index.count()}" for name, index in indexes.items()))
        compare(indexes, questions, args.budget, corpus, args.inspect)
    else:
        from module_02.rag_lab_agent import run_agent

        index = build_indexes(corpus, (args.strategy,), args.window_words)[args.strategy]

        def search(question):
            return [
                {"source": chunk.label(corpus), "text": chunk.text}
                for chunk in retrieve(index, question, args.budget)
            ]

        print(asyncio.run(run_agent(args.ask, search)))


if __name__ == "__main__":
    main()
