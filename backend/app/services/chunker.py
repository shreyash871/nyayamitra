"""Split cleaned judgment text into overlapping chunks for embedding."""

import re

CHUNK_CHARS = 1500  # ~375 tokens, comfortably under InLegal-SBERT's 512
OVERLAP_CHARS = 200  # carry-over so meaning isn't cut at a boundary
MIN_CHUNK_CHARS = 100  # discard fragments too short to be meaningful

# Split on sentence enders, but not on common legal abbreviations
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")

ABBREVIATIONS = (
    "No.",
    "Nos.",
    "Sec.",
    "Art.",
    "v.",
    "Vs.",
    "Ltd.",
    "Pvt.",
    "Hon.",
    "Mr.",
    "Mrs.",
    "Dr.",
    "J.",
    "JJ.",
    "Anr.",
    "Ors.",
)


def split_sentences(text: str) -> list[str]:
    parts = SENTENCE_END.split(text)
    merged: list[str] = []
    for part in parts:
        if merged and merged[-1].rstrip().endswith(ABBREVIATIONS):
            merged[-1] = merged[-1] + " " + part
        else:
            merged.append(part)
    return [p.strip() for p in merged if p.strip()]


def chunk(
    text: str, size: int = CHUNK_CHARS, overlap: int = OVERLAP_CHARS
) -> list[str]:
    """Sentence-aware chunking with character overlap between neighbours."""
    sentences = split_sentences(text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        # A single oversized sentence becomes its own chunk
        if len(sentence) > size:
            if current:
                chunks.append(" ".join(current))
                current, current_len = [], 0
            chunks.append(sentence[:size])
            continue

        if current_len + len(sentence) + 1 > size:
            chunks.append(" ".join(current))
            # Rebuild the tail of the previous chunk as overlap
            # Rebuild the tail of the previous chunk as overlap
            tail, tail_len = [], 0
            for prev in reversed(current):
                tail.insert(0, prev)
                tail_len += len(prev) + 1
                if tail_len >= overlap:  # add first, then stop
                    break
            current, current_len = tail, tail_len

        current.append(sentence)
        current_len += len(sentence) + 1

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if len(c) >= MIN_CHUNK_CHARS]
