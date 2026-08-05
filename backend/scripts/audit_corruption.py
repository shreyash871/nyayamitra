"""Find tokens that look like abbreviation-expansion corruption."""

import re
from collections import Counter

from app.db.session import SessionLocal
from app.models import Judgment

SUSPECT = re.compile(r"\b(company|number)([a-z]{2,})", re.IGNORECASE)

session = SessionLocal()
counter = Counter()

for (text,) in session.query(Judgment.full_text).filter(Judgment.source == "ildc"):
    if text:
        for match in SUSPECT.finditer(text):
            counter[match.group(0).lower()] += 1

session.close()

print(f"{len(counter)} distinct suspect tokens\n")
for token, n in counter.most_common(60):
    print(f"{n:>5}  {token}")
