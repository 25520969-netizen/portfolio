"""Make a copy of the CV with the phone number removed from the page content stream.

Usage: .venv-tools/bin/python scripts/redact_cv.py SRC DST [--preview PNG]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phone_pattern import PHONE_RE  # noqa: E402

CONTACT_LINE = "Thu Duc, Ho Chi Minh City · vohoangkim3103@gmail.com · github.com/25520969-netizen"
EMAIL = b"vohoangkim3103@gmail.com"
FONT_NAME = "F3+0"
FONT_SIZE_PT = 8.0
GITHUB_URI_PART = "github.com/25520969-netizen"
CONTACT_LINE_Y = (70.0, 86.0)  # fitz top-left coordinates
PREVIEW_DPI = 150
SEPARATOR_CODE = 1  # the "·" glyph is code \001 in the subset font
SPACE_CODE = 32

_ESCAPES = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12,
            ord("("): 40, ord(")"): 41, ord("\\"): 92}
_TJ_RE = re.compile(rb"\((?:[^()\\]|\\.)*\)\s*Tj")
_NUM = rb"-?\d+(?:\.\d+)?"


def subset_widths(doc: "fitz.Document", font_xref: int) -> list[float]:
    """Return the /Widths array of a font (indexed from /FirstChar, assumed 0)."""
    _, first = doc.xref_get_key(font_xref, "FirstChar")
    if int(first) != 0:
        raise ValueError(f"unsupported /FirstChar {first}")
    _, raw = doc.xref_get_key(font_xref, "Widths")
    return [float(v) for v in raw.strip("[] ").split()]


def _decode(literal: bytes) -> list[int]:
    """Decode the body of a PDF literal string (without parentheses) into codes."""
    codes: list[int] = []
    i = 0
    while i < len(literal):
        ch = literal[i]
        if ch != 0x5C:
            codes.append(ch)
            i += 1
            continue
        nxt = literal[i + 1]
        octal = re.match(rb"[0-7]{1,3}", literal[i + 1:])
        if octal:
            codes.append(int(octal.group(0), 8))
            i += 1 + len(octal.group(0))
        else:
            codes.append(_ESCAPES.get(nxt, nxt))
            i += 2
    return codes


def _encode(codes: list[int]) -> bytes:
    out = bytearray()
    for code in codes:
        if code in (40, 41, 92):
            out += b"\\" + bytes([code])
        elif code < 32 or code > 126:
            out += b"\\%03o" % code
        else:
            out.append(code)
    return bytes(out)


def _find_block(content: bytes, email: bytes) -> tuple[int, int]:
    pos = content.find(email)
    if pos < 0:
        raise ValueError("contact line (email) not found in content stream")
    start = content.rfind(b"BT", 0, pos)
    end = content.find(b"ET", pos)
    if start < 0 or end < 0:
        raise ValueError("BT…ET block around the contact line not found")
    return start, end + 2


def strip_phone(content: bytes, widths: list[float], font_size: float,
                email: bytes = EMAIL) -> tuple[bytes, float]:
    """Delete the phone segment from the contact line and re-centre it.

    Returns (new_content, tail_shift): the signed horizontal shift in points of the
    text that follows the phone (negative = left).
    """
    start, end = _find_block(content, email)
    block = content[start:end]
    tj = next((m for m in _TJ_RE.finditer(block) if email in m.group(0)), None)
    if tj is None:
        raise ValueError("Tj string with the email not found")
    codes = _decode(tj.group(0)[1:tj.group(0).rindex(b")")])
    text = "".join(chr(c) if c != SEPARATOR_CODE else "·" for c in codes)
    matches = list(PHONE_RE.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one phone match, found {len(matches)}")
    m = matches[0]
    tail = text[m.end():m.end() + 3]
    if tail != " · ":
        raise ValueError("phone is not followed by ' · '")
    removed = codes[m.start():m.end() + 3]
    new_codes = codes[:m.start()] + codes[m.end() + 3:]
    removed_w = sum(widths[c] for c in removed) * font_size / 1000
    td = re.search(rb"(?<![\d.\-])(" + _NUM + rb") 0 Td", block)
    neg = re.search(rb"(-" + _NUM + rb") 0 Td", block)
    if td is None or neg is None:
        raise ValueError("Td operators not found in the contact block")
    x = float(td.group(1))
    new_block = block[:tj.start()] + b"(" + _encode(new_codes) + b") Tj" + block[tj.end():]
    shifted = x + removed_w / 2
    new_block = re.sub(rb"(?<![\d.\-])" + re.escape(td.group(1)) + rb" 0 Td",
                       b"%.5f 0 Td" % shifted, new_block, count=1)
    new_block = re.sub(re.escape(neg.group(1)) + rb" 0 Td", b"-%.5f 0 Td" % shifted,
                       new_block, count=1)
    return content[:start] + new_block + content[end:], -removed_w / 2


def shift_contact_link(page: "fitz.Page", tail_shift: float, line_y: tuple[float, float]) -> None:
    """Move the GitHub link on the contact line horizontally by ``tail_shift``."""
    matches = [lk for lk in page.get_links()
               if GITHUB_URI_PART in lk.get("uri", "")
               and line_y[0] <= lk["from"].y0 and lk["from"].y1 <= line_y[1]]
    if len(matches) != 1:
        raise ValueError(f"expected one GitHub link on the contact line, found {len(matches)}")
    link = matches[0]
    rect = link["from"]
    new = {"kind": fitz.LINK_URI, "uri": link["uri"],
           "from": fitz.Rect(rect.x0 + tail_shift, rect.y0, rect.x1 + tail_shift, rect.y1)}
    page.delete_link(link)
    page.insert_link(new)


def _font_xref(page: "fitz.Page") -> int:
    for row in page.get_fonts():
        if row[4] == FONT_NAME:
            return row[0]
    raise ValueError(f"font {FONT_NAME} not found on page")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path)
    parser.add_argument("dst", type=Path)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args(argv)

    doc = fitz.open(args.src)
    page = doc[0]
    xref = page.get_contents()[0]
    widths = subset_widths(doc, _font_xref(page))
    new, tail_shift = strip_phone(doc.xref_stream(xref), widths, FONT_SIZE_PT)
    doc.update_stream(xref, new)
    shift_contact_link(page, tail_shift, CONTACT_LINE_Y)
    args.dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.dst, garbage=4, deflate=True, clean=True)
    doc.close()
    if args.preview:
        with fitz.open(args.dst) as out:
            out[0].get_pixmap(dpi=PREVIEW_DPI).save(args.preview)
    print(f"wrote {args.dst} ({args.dst.stat().st_size} bytes), tail shift {tail_shift:.3f} pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
