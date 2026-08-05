"""Derive a verified correction map for expansion-corrupted tokens.

The ILDC source text was scraped with a broken abbreviation expander that
replaced short strings beginning 'co'/'no' with 'company'/'number' *inside*
words: conspiracy -> companyspiracy, nothing -> numberhing.

This script proposes corrections, auto-accepts only unambiguous ones, and
writes everything else to a review file for human adjudication.
"""

import json
import re
from collections import Counter
from pathlib import Path

from spellchecker import SpellChecker

from app.db.session import SessionLocal
from app.models import Judgment

SUSPECT = re.compile(r"\b(company|number)([a-z]{2,})", re.IGNORECASE)

# The prefix that was overwritten varies: cou-ld, col-lege, cor-rect, cog-nizance
PREFIXES = {
    "company": ["co", "cog", "col", "com", "con", "cop", "cor", "cou", "cov"],
    "number": ["no", "nob", "nom", "non", "nor", "not", "num"],
}

# Used only for the "space was eaten" case: numberreason -> "no reason"
BASE_PREFIX = {"company": "co", "number": "no"}

# Verified by reading context. Overrides the automatic resolver.
# A token mapped to itself is explicitly left untouched.
MANUAL = {
    "companyld": "could",
    "companyrse": "course",
    "companyies": "copies",
    "companyes": "comes",
    "companying": "coming",
    "companyent": "cogent",
    "companyaccused": "co-accused",
    "numbered": "noted",  # "as already noted hereinabove" - NOT 'numbered'
    "numbering": "noting",
    "numberes": "notes",
    "numberwithstanding": "notwithstanding",
    "companytai": "companytai",
    "companyour": "colour",
    "companynselling": "counselling",
    "companyer": "cover",
    "companyjested": "congested",
    "companyting": "coating",
    "numbericed": "noticed",
    "numbersuch": "no such",
    "numberdefence": "no defence",
    "numbereye": "no eye",
    "numbercompliance": "non-compliance",
    "numberinterference": "non-interference",
    "numberperson": "no person",
    "numberoffence": "no offence",  # proper noun: Contai, West Bengal - leave alone
}

MIN_REST = 4  # shortest remainder eligible for space-reinsertion

OUT = Path("app/data/corruption_map.json")
REVIEW = Path("app/data/corruption_review.txt")


def collect() -> tuple[Counter, dict[str, str]]:
    """Count suspect tokens across the corpus and keep one context per token."""
    session = SessionLocal()
    counter: Counter = Counter()
    contexts: dict[str, str] = {}
    try:
        rows = session.query(Judgment.full_text).filter(Judgment.source == "ildc")
        for (text,) in rows:
            if not text:
                continue
            for match in SUSPECT.finditer(text):
                token = match.group(0).lower()
                counter[token] += 1
                if token not in contexts:
                    start, end = max(0, match.start() - 60), match.end() + 60
                    contexts[token] = text[start:end].replace("\n", " ")
    finally:
        session.close()
    return counter, contexts


def candidates_for(token: str, spell: SpellChecker) -> list[str]:
    bad = "company" if token.startswith("company") else "number"
    rest = token[len(bad) :]

    found: list[str] = []

    # Case 1: prefix was overwritten -> companylege = col + lege
    for prefix in PREFIXES[bad]:
        joined = prefix + rest
        if joined in spell:
            found.append(joined)

    # Case 2: a space was eaten too -> numberreason = "no reason"
    # Only for 'number'. There is no "co X" construction in English, and
    # allowing it produces junk ("co text") that swamps the review file.
    if bad == "number" and len(rest) >= MIN_REST and rest in spell:
        found.append(f"no {rest}")

    return list(dict.fromkeys(found))


def main() -> None:
    spell = SpellChecker()
    counter, contexts = collect()

    resolved: dict[str, str] = {}
    review: list[str] = []

    for token, freq in counter.most_common():
        if token in MANUAL:
            target = MANUAL[token]
            if target != token:
                resolved[token] = target
            continue

        options = candidates_for(token, spell)

        if len(options) == 1:
            resolved[token] = options[0]
        else:
            shown = options if options else "NO MATCH"
            review.append(
                f"{freq:>5}  {token:22} -> {shown}\n"
                f"         ...{contexts[token]}..."
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(resolved, indent=2, sort_keys=True), encoding="utf-8")
    REVIEW.write_text("\n".join(review), encoding="utf-8")

    total = sum(counter.values())
    covered = sum(counter[t] for t in resolved)
    print(f"distinct suspect tokens : {len(counter)}")
    print(f"auto-resolved           : {len(resolved)}")
    print(f"needs review            : {len(review)}")
    print(f"occurrence coverage     : {covered}/{total} ({covered / total:.1%})")
    print(f"\n  {OUT}\n  {REVIEW}")


if __name__ == "__main__":
    main()
