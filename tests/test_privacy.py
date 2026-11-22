import json
import os
import subprocess
import unittest
from pathlib import Path

from site_parser import ROOT, SITE, parse_html
from phone_pattern import find_phones  # noqa: E402  (scripts/ is put on sys.path by site_parser)

CV_PATH = Path(os.environ.get("CV_PATH", SITE / "assets/cv/VoHoangKim_CV.pdf"))
ORIGINAL_CV = ROOT / "VoHoangKim_CV_AI-Backend.pdf"
EMAIL = "vohoangkim3103@gmail.com"
CONTACT_LINE = "Thu Duc, Ho Chi Minh City · vohoangkim3103@gmail.com · github.com/25520969-netizen"
TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".svg", ".txt", ".xml"}
PDFTOTEXT_TIMEOUT_S = 30
ALLOWED_SAMPLES = {"0912 345 678", "+84 912 345 678"}


def pdf_text(path: Path, mode: str) -> str:
    result = subprocess.run(
        ["pdftotext", mode, str(path), "-"],
        capture_output=True, text=True, check=True, timeout=PDFTOTEXT_TIMEOUT_S,
    )
    return result.stdout


def collapse(text: str) -> str:
    return " ".join(text.split())


def without_contact_line(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if EMAIL not in line)


class PrivacyTest(unittest.TestCase):
    def test_phone_re_samples(self) -> None:
        self.assertTrue(find_phones("0912 345 678"))
        self.assertTrue(find_phones("+84 912 345 678"))
        for sample in ("0 100 200 300", "25520969-netizen", "2025 – 2029"):
            self.assertEqual(find_phones(sample), [], sample)

    def test_cv_copy_exists(self) -> None:
        self.assertTrue(CV_PATH.is_file(), CV_PATH)

    def test_cv_text_has_no_phone(self) -> None:
        for mode in ("-layout", "-raw"):
            self.assertEqual(find_phones(pdf_text(CV_PATH, mode)), [], mode)

    def test_cv_contact_line_exact(self) -> None:
        lines = [collapse(line) for line in pdf_text(CV_PATH, "-raw").splitlines() if EMAIL in line]
        self.assertEqual(lines, [CONTACT_LINE])

    @unittest.skipUnless(ORIGINAL_CV.is_file(), "original CV not present (e.g. in CI)")
    def test_cv_keeps_rest_of_text(self) -> None:
        copy = collapse(without_contact_line(pdf_text(CV_PATH, "-raw")))
        original = collapse(without_contact_line(pdf_text(ORIGINAL_CV, "-raw")))
        self.assertEqual(copy, original)

    def test_no_phone_in_site_text_files(self) -> None:
        for path in SITE.rglob("*"):
            if path.suffix in TEXT_SUFFIXES:
                found = find_phones(path.read_text(encoding="utf-8"))
                self.assertEqual(found, [], str(path))

    def test_original_cv_not_in_site(self) -> None:
        self.assertEqual([p for p in SITE.rglob("*") if "AI-Backend" in p.name], [])

    def test_gitignore_rules(self) -> None:
        lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("VoHoangKim_CV_AI-Backend.pdf", lines)
        self.assertIn("docs/", lines)

    def test_no_tel_links(self) -> None:
        for link in parse_html().find_all("a"):
            self.assertFalse((link.attrs.get("href") or "").startswith("tel:"))

    def test_no_form_elements(self) -> None:
        doc = parse_html()
        for tag in ("form", "input", "textarea"):
            self.assertEqual(doc.find_all(tag), [], tag)

    def test_jsonld_has_no_telephone(self) -> None:
        script = parse_html().find_all("script", type="application/ld+json")[0]
        data = json.loads("".join(c for c in script.children if isinstance(c, str)))
        self.assertNotIn("telephone", data)

    def test_no_phone_in_tracked_files(self) -> None:
        inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT,
                                capture_output=True, text=True)
        if inside.returncode != 0:
            self.skipTest("not a git work tree")
        listing = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                                 cwd=ROOT, capture_output=True, text=True, check=True,
                                 timeout=PDFTOTEXT_TIMEOUT_S).stdout.splitlines()
        sample_files = {"tests/test_privacy.py", "tests/test_redact_cv.py"}
        for name in listing:
            if name.endswith((".pdf", ".png")) or not (ROOT / name).is_file():
                continue
            try:
                text = (ROOT / name).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            found = find_phones(text)
            if name in sample_files:
                found = [m for m in found if m not in ALLOWED_SAMPLES]
            self.assertEqual(found, [], name)


if __name__ == "__main__":
    unittest.main()
