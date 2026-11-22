"""Single source for phone-number detection (no real digits are stored here)."""
from __future__ import annotations

import re

# Generic Vietnamese mobile number: 10 digits, prefixes 03/05/07/08/09, optional separators.
PHONE_RE: re.Pattern[str] = re.compile(
    r"(?<![\d.])(?:\+?84[\s.\-]?|0)[35789]\d(?:[\s.\-]?\d){7}(?!\d)"
)


def find_phones(text: str) -> list[str]:
    """Return every phone-like match in ``text``."""
    return [m.group(0) for m in PHONE_RE.finditer(text)]
