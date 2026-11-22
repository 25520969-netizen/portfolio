import re
import struct
import unittest

from site_parser import SITE, parse_html

CV = SITE / "assets/cv/VoHoangKim_CV.pdf"
BUDGET_BYTES = 300 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_size(path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == PNG_SIGNATURE, path
    return struct.unpack(">II", data[16:24])


class AssetsTest(unittest.TestCase):
    def test_cv_size_label_matches_file(self) -> None:
        labels = parse_html().find_all(data_cv_size=True)
        self.assertGreaterEqual(len(labels), 2)
        for label in labels:
            match = re.fullmatch(r"PDF · ~(\d+) KB", label.text())
            self.assertIsNotNone(match, label.text())
            self.assertLessEqual(abs(int(match.group(1)) - CV.stat().st_size / 1024), 5)

    def test_og_image_size(self) -> None:
        self.assertEqual(png_size(SITE / "assets/og.png"), (1200, 630))

    def test_touch_icon_size(self) -> None:
        self.assertEqual(png_size(SITE / "assets/img/apple-touch-icon.png"), (180, 180))

    def test_page_weight_budget(self) -> None:
        files = [SITE / "index.html", SITE / "assets/i18n/vi.json", SITE / "assets/img/favicon.svg"]
        files += sorted((SITE / "assets/css").glob("*.css")) + sorted((SITE / "assets/js").glob("*.js"))
        files += sorted((SITE / "assets/img").glob("kim.*"))
        self.assertEqual(len(list((SITE / "assets/css").glob("*.css"))), 3)
        self.assertEqual(len(list((SITE / "assets/js").glob("*.js"))), 9)
        total = sum(f.stat().st_size for f in files)
        self.assertLess(total, BUDGET_BYTES, total)


if __name__ == "__main__":
    unittest.main()
