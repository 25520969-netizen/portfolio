import unittest

import site_parser  # noqa: F401  (puts scripts/ on sys.path)

try:
    import fitz  # noqa: F401
except ImportError:  # CI runs without PyMuPDF
    fitz = None


@unittest.skipIf(fitz is None, "PyMuPDF not installed")
class StripPhoneTest(unittest.TestCase):
    WIDTHS = [500.0] * 128

    @classmethod
    def setUpClass(cls) -> None:
        import redact_cv
        cls.redact = redact_cv

    def test_strip_phone_on_sample(self) -> None:
        stream = (rb"BT 1 0 0 1 0 3 Tm 10.00000 0 Td /F3+0 8 Tf "
                  rb"(City \001 0912 345 678 \001 a@b.c \001 ) Tj T* -10.00000 0 Td ET")
        new, tail_shift = self.redact.strip_phone(stream, self.WIDTHS, 8.0, email=b"a@b.c")
        self.assertIn(rb"(City \001 a@b.c \001 )", new)
        self.assertIn(b" 40.00000 0 Td", new)
        self.assertIn(b"-40.00000 0 Td", new)
        self.assertNotIn(b"10.00000", new)
        self.assertEqual(tail_shift, -30.0)

    def test_strip_phone_rejects_two_matches(self) -> None:
        stream = (rb"BT 1 0 0 1 0 3 Tm 10.00000 0 Td /F3+0 8 Tf "
                  rb"(0912 345 678 \001 +84 912 345 678 \001 a@b.c ) Tj T* -10.00000 0 Td ET")
        with self.assertRaises(ValueError):
            self.redact.strip_phone(stream, self.WIDTHS, 8.0, email=b"a@b.c")


if __name__ == "__main__":
    unittest.main()
