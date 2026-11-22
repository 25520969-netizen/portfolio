import json
import unittest

from site_parser import SITE, parse_html

I18N_DIR = SITE / "assets/i18n"
HTML_KEYS = {"vr.b2"}


def collapse(text: str) -> str:
    return " ".join(text.split())


def load(lang: str) -> dict:
    return json.loads((I18N_DIR / f"{lang}.json").read_text(encoding="utf-8"))


def attr_pairs(value: str) -> list[tuple[str, str]]:
    return [tuple(part.strip() for part in pair.split(":", 1)) for pair in value.split(";") if pair.strip()]


class I18nTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.en, cls.vi = load("en"), load("vi")
        cls.doc = parse_html()

    def test_same_keys_in_both_languages(self) -> None:
        self.assertEqual(set(self.en), set(self.vi))

    def test_no_empty_values(self) -> None:
        for name, d in (("en", self.en), ("vi", self.vi)):
            for key, value in d.items():
                self.assertTrue(value.strip(), f"{name}:{key}")

    def test_dictionaries_are_flat(self) -> None:
        for d in (self.en, self.vi):
            self.assertTrue(all(isinstance(v, str) for v in d.values()))

    def test_text_keys_have_no_markup(self) -> None:
        for d in (self.en, self.vi):
            for key, value in d.items():
                if key not in HTML_KEYS:
                    self.assertNotIn("<", value, key)

    def _used_keys(self) -> set[str]:
        keys: set[str] = set()
        for node in self.doc.iter():
            for attr in ("data-i18n", "data-i18n-html"):
                if node.attrs.get(attr):
                    keys.add(node.attrs[attr])
            for _, key in attr_pairs(node.attrs.get("data-i18n-attr") or ""):
                keys.add(key)
        return keys

    def test_html_keys_exist_in_dictionaries(self) -> None:
        missing = self._used_keys() - set(self.en)
        self.assertEqual(missing, set())

    def test_html_default_text_equals_en(self) -> None:
        for node in self.doc.iter():
            if node.attrs.get("data-i18n"):
                key = node.attrs["data-i18n"]
                self.assertEqual(node.text(), collapse(self.en[key]), key)
            if node.attrs.get("data-i18n-html"):
                key = node.attrs["data-i18n-html"]
                self.assertEqual(node.inner_html(), collapse(self.en[key]), key)
            for attr, key in attr_pairs(node.attrs.get("data-i18n-attr") or ""):
                self.assertEqual(collapse(node.attrs.get(attr) or ""), collapse(self.en[key]), f"{attr}:{key}")

    def test_i18n_targets_are_leaves(self) -> None:
        for node in self.doc.find_all(data_i18n=True):
            self.assertEqual(node.element_children(), [], node.attrs["data-i18n"])

    def test_title_and_description_match_meta_keys(self) -> None:
        title = self.doc.find_all("title")[0].text()
        self.assertEqual(title, self.en["meta.title"])
        desc = [m for m in self.doc.find_all("meta") if m.attrs.get("name") == "description"]
        self.assertEqual(len(desc), 1)
        self.assertEqual(desc[0].attrs["content"], self.en["meta.desc"])


if __name__ == "__main__":
    unittest.main()
