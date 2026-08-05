"""Isolate which cleaning step is eating the text."""

from app.db.session import SessionLocal
from app.models import Judgment
from app.services import text_clean as tc

s = SessionLocal()
text = s.query(Judgment).filter_by(id=8).first().full_text
s.close()

print(f"{'start':<22}{len(text):>8,}")
print(f"{'newlines in raw':<22}{text.count(chr(10)):>8,}")

steps = [
    ("LITERAL_NEWLINE", lambda t: tc.LITERAL_NEWLINE.sub("\n", t)),
    ("HYPHEN_BREAK", lambda t: tc.HYPHEN_BREAK.sub(r"\1\2", t)),
    ("SIGNATURE_NOISE", lambda t: tc.SIGNATURE_NOISE.sub(" ", t)),
    ("PAGE_NUMBER", lambda t: tc.PAGE_NUMBER.sub("\n", t)),
    ("fix_corruption", tc.fix_corruption),
    ("EXCESS_SPACES", lambda t: tc.EXCESS_SPACES.sub(" ", t)),
    ("EXCESS_BLANKS", lambda t: tc.EXCESS_BLANKS.sub("\n\n", t)),
]

for name, fn in steps:
    before = len(text)
    text = fn(text)
    lost = before - len(text)
    flag = "  <-- CULPRIT" if lost > before * 0.1 else ""
    print(f"{name:<22}{len(text):>8,}   lost {lost:>7,}{flag}")
