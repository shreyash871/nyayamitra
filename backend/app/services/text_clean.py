"""Clean raw judgment text before chunking.

ILDC text is PDF-extracted and was scraped with a broken abbreviation
expander. Order matters: line-break repair must precede token correction,
because 'contai ned' would otherwise never rejoin into 'contained'.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

MAP_FILE = Path(__file__).resolve().parent.parent / "data" / "corruption_map.json"

HYPHEN_BREAK = re.compile(r"(\w)-\s+(\w)")
LITERAL_NEWLINE = re.compile(r"\\n")
SIGNATURE_NOISE = re.compile(
    r"Signature Not Verified"
    r"|Digitally signed by\s+[A-Z][\w.\- ]{0,40}"
    r"|Date:\s*\d{4}\.\d{2}\.\d{2}\s*\d{2}:\d{2}:\d{2}\s*(?:IST)?"
    r"|Reason:\s*(?=[A-Z])",
    re.IGNORECASE,
)
PAGE_NUMBER = re.compile(r"\n\s*\d{1,4}\s*\n")
EXCESS_SPACES = re.compile(r"[ \t]{2,}")
EXCESS_BLANKS = re.compile(r"\n{3,}")


@lru_cache(maxsize=1)
def _corruption() -> tuple[re.Pattern, dict[str, str]]:
    mapping = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    # Longest first so 'companystitutional' wins over 'companystitution'
    keys = sorted(mapping, key=len, reverse=True)
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(k) for k in keys) + r")\b", re.IGNORECASE
    )
    return pattern, mapping


def fix_corruption(text: str) -> str:
    pattern, mapping = _corruption()
    return pattern.sub(lambda m: mapping[m.group(0).lower()], text)


def clean(text: str) -> str:
    text = LITERAL_NEWLINE.sub("\n", text)
    text = HYPHEN_BREAK.sub(r"\1\2", text)  # before fix_corruption
    text = SIGNATURE_NOISE.sub(" ", text)
    text = PAGE_NUMBER.sub("\n", text)
    text = fix_corruption(text)
    text = EXCESS_SPACES.sub(" ", text)
    text = EXCESS_BLANKS.sub("\n\n", text)
    return text.strip()
