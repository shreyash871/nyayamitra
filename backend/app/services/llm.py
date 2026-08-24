"""Llama 3 via Ollama - query reformulation and grounded answer generation."""

import re

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
TIMEOUT = 300

REFORMULATE_PROMPT = """You are an Indian legal research assistant. Rewrite the user's informal description into formal Indian legal terminology suitable for searching a database of Supreme Court judgments.

Rules:
- Output ONLY the rewritten query. No preamble, no explanation.
- Use formal legal vocabulary (e.g. "dishonestly induced delivery of property" not "tricked into paying").
- Include the applicable IPC section number ONLY if you are confident. Never guess a section number.
- Keep it under 40 words.

User description: {query}

Rewritten query:"""

ANSWER_PROMPT = """You are an Indian legal research assistant. Answer the question using ONLY the retrieved judgment excerpts below.

Rules:
- If the excerpts do not contain enough information to answer, say so plainly. Do not fill gaps from general knowledge.
- Cite excerpts by their number, e.g. [1], [2].
- Do not state a legal conclusion the excerpts do not support.
- Be concise.

RETRIEVED EXCERPTS:
{context}

QUESTION: {question}

ANSWER:"""


def _generate(prompt: str, temperature: float = 0.2) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def reformulate(query: str) -> str:
    """Informal description -> formal legal query. Falls back to the original."""
    try:
        out = _generate(REFORMULATE_PROMPT.format(query=query))
        out = re.sub(r'^["\']|["\']$', "", out.strip())
        return out if 5 < len(out) < 400 else query
    except Exception:
        return query


def answer(question: str, excerpts: list[dict]) -> str:
    """Generate an answer grounded strictly in the supplied excerpts."""
    context = "\n\n".join(
        f"[{i + 1}] (Judgment {e['judgment_id']}, {e.get('year')}, "
        f"similarity {e['similarity']:.2f})\n{e['snippet']}"
        for i, e in enumerate(excerpts)
    )
    return _generate(ANSWER_PROMPT.format(context=context, question=question))
