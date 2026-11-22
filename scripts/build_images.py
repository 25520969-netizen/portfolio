"""Render the share image and the touch icon from SVG sources with PyMuPDF.

Usage: .venv-tools/bin/python scripts/build_images.py
"""
from __future__ import annotations

from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
JOBS = [
    (ROOT / "scripts/image_src/og.svg", ROOT / "site/assets/og.png", 1200, 630),
    (ROOT / "site/assets/img/favicon.svg", ROOT / "site/assets/img/apple-touch-icon.png", 180, 180),
]


def render_svg(src: Path, dst: Path, width: int, height: int) -> None:
    """Render ``src`` to a PNG of exactly ``width`` x ``height`` pixels."""
    with fitz.open(src) as svg:
        page = svg[0]
        matrix = fitz.Matrix(width / page.rect.width, height / page.rect.height)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    if (pixmap.width, pixmap.height) != (width, height):
        raise ValueError(f"{src.name}: rendered {pixmap.width}x{pixmap.height}, wanted {width}x{height}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(dst)


def main() -> None:
    for src, dst, width, height in JOBS:
        render_svg(src, dst, width, height)
        print(f"wrote {dst.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
