import json
import re
import unittest
from pathlib import PurePosixPath

from site_parser import SITE, Node, parse_html

SKIP_PREFIXES = ("http", "mailto:", "#", "data:")


def local_refs(doc) -> list[str]:
    refs: list[str] = []
    for node in doc.iter():
        for attr in ("href", "src", "srcset"):
            value = node.attrs.get(attr)
            if value and not value.startswith(SKIP_PREFIXES):
                refs.append(value)
    return refs


class StructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = parse_html()

    def test_local_urls_are_relative(self) -> None:
        for ref in local_refs(self.doc):
            self.assertFalse(ref.startswith("/"), ref)

    def test_local_references_exist(self) -> None:
        for ref in local_refs(self.doc):
            path = ref.split("#")[0].split("?")[0]
            self.assertTrue((SITE / PurePosixPath(path)).exists(), ref)

    def test_ids_unique(self) -> None:
        ids = [n.attrs["id"] for n in self.doc.iter() if n.attrs.get("id")]
        self.assertEqual(len(ids), len(set(ids)))

    def _body(self) -> Node:
        return self.doc.find_all("body")[0]

    def test_skip_link_is_first_focusable(self) -> None:
        first = [n for n in self._body().iter() if n.tag in ("a", "button")][0]
        self.assertEqual(first.attrs.get("href"), "#main")

    def test_nav_targets_exist(self) -> None:
        ids = {n.attrs["id"] for n in self.doc.iter() if n.attrs.get("id")}
        nav_links = self.doc.find_all("a", cls="nav-link")
        self.assertEqual(len(nav_links), 5)
        for link in nav_links:
            self.assertIn(link.attrs["href"].lstrip("#"), ids)

    def test_icon_svgs_hidden(self) -> None:
        for svg in self.doc.find_all("svg"):
            if svg.find_all("use"):
                self.assertEqual(svg.attrs.get("aria-hidden"), "true")

    def test_buttons_have_names(self) -> None:
        for button in self.doc.find_all("button"):
            name = button.text() or (button.attrs.get("aria-label") or "").strip()
            self.assertTrue(name, button.attrs)
        for ident in ("theme-toggle", "menu-toggle"):
            btn = self.doc.find_all("button", id=ident)[0]
            self.assertTrue((btn.attrs.get("aria-label") or "").strip(), ident)

    def test_single_h1(self) -> None:
        self.assertEqual(len(self.doc.find_all("h1")), 1)

    def test_trace_has_four_nodes_and_label(self) -> None:
        trace = self.doc.find_all(cls="trace")[0]
        self.assertEqual(trace.attrs.get("role"), "img")
        self.assertTrue((trace.attrs.get("aria-label") or "").strip())
        track = trace.find_all(cls="trace-track")[0]
        self.assertEqual(len([c for c in track.element_children() if c.tag == "li"]), 4)

    def test_cv_links_point_to_copy(self) -> None:
        links = self.doc.find_all("a", download=True)
        self.assertGreaterEqual(len(links), 2)
        for link in links:
            self.assertEqual(link.attrs["href"], "assets/cv/VoHoangKim_CV.pdf")

    def test_four_cases_in_order(self) -> None:
        ids = [a.attrs["id"] for a in self.doc.find_all("article", cls="case")]
        self.assertEqual(ids, ["work-pnkk", "work-datamate", "work-retrieval", "work-gym"])

    def test_pnkk_has_no_links(self) -> None:
        pnkk = self.doc.find_all("article", id="work-pnkk")[0]
        self.assertEqual(pnkk.find_all("a"), [])
        self.assertTrue(pnkk.find_all(data_i18n="work.private"))

    def test_external_links_safe(self) -> None:
        links = self.doc.find_all("a", target="_blank")
        self.assertGreaterEqual(len(links), 4)
        for link in links:
            self.assertIn("noopener", link.attrs.get("rel") or "")
            self.assertTrue(link.find_all(cls="sr-only", data_i18n="a11y.newTab"))

    def test_github_links(self) -> None:
        hrefs = {a.attrs["href"] for a in self.doc.find_all("a") if a.attrs.get("href")}
        for repo in ("Datamate", "AIC2026", "Gym-Coach"):
            self.assertIn(f"https://github.com/25520969-netizen/{repo}", hrefs)
        self.assertNotIn("ZaloAi-Datamate", (SITE / "index.html").read_text(encoding="utf-8"))

    def test_decision_nodes_have_icon_and_word(self) -> None:
        nodes = self.doc.find_all(cls="node--success") + self.doc.find_all(cls="node--warn")
        self.assertGreaterEqual(len(nodes), 5)
        for node in nodes:
            self.assertTrue(node.find_all("use"))
            self.assertTrue(node.text())

    def test_sections_labelled(self) -> None:
        ids = {n.attrs["id"] for n in self.doc.iter() if n.attrs.get("id")}
        sections = self.doc.find_all("section", id=True)
        self.assertEqual(len(sections), 6)
        for section in sections:
            self.assertIn(section.attrs.get("aria-labelledby"), ids)

    def test_skill_rows(self) -> None:
        rows = self.doc.find_all(cls="skill-row")
        self.assertEqual(len(rows), 5)
        allowed = {"#work-pnkk", "#work-datamate", "#work-retrieval", "#work-gym", "#honors"}
        for row in rows:
            for link in row.find_all("a"):
                self.assertIn(link.attrs["href"], allowed)
        vision = [r for r in rows if r.find_all(data_i18n="skills.g.vision")]
        self.assertEqual(len(vision), 1)
        self.assertEqual(vision[0].find_all(cls="proven"), [])

    def test_timeline_years(self) -> None:
        years = [t.text() for t in self.doc.find_all("ol", cls="timeline")[0].find_all("time")]
        self.assertEqual(years, ["2025", "2025", "2025", "2024", "2024"])

    def test_no_absolute_self_urls(self) -> None:
        host = "25520969-netizen.github.io"
        for node in self.doc.iter():
            allowed = (
                (node.tag == "link" and node.attrs.get("rel") == "alternate")
                or (node.tag == "meta" and (node.attrs.get("property") or "").startswith("og:"))
            )
            for value in node.attrs.values():
                if value and host in value:
                    self.assertTrue(allowed, f"{node.tag} {value}")
            if node.tag != "script":
                for child in node.children:
                    if isinstance(child, str):
                        self.assertNotIn(host, child)

    def test_seo_head(self) -> None:
        self.assertEqual(self.doc.find_all("link", rel="canonical"), [])
        base = "https://25520969-netizen.github.io/portfolio/"
        alt = {l.attrs["hreflang"]: l.attrs["href"] for l in self.doc.find_all("link", rel="alternate")}
        self.assertEqual(alt, {"en": base, "vi": base + "?lang=vi", "x-default": base})
        props = {m.attrs.get("property"): m.attrs.get("content") for m in self.doc.find_all("meta")}
        for prop in ("og:url", "og:image", "og:title", "og:description"):
            self.assertTrue(props.get(prop), prop)
        self.assertEqual(props["og:url"], base)

    def test_canonical_constants_match_hreflang(self) -> None:
        js = (SITE / "assets/js/i18n.js").read_text(encoding="utf-8")
        base = re.search(r"BASE_URL = '([^']+)'", js).group(1)
        self.assertEqual(base, "https://25520969-netizen.github.io/portfolio/")
        self.assertIn("vi: BASE_URL + '?lang=vi'", js)

    def test_images_have_alt_and_size(self) -> None:
        for img in self.doc.find_all("img"):
            for attr in ("alt", "width", "height"):
                self.assertIn(attr, img.attrs)
            self.assertEqual(img.attrs.get("loading"), "lazy")

    def test_no_js_defaults(self) -> None:
        html = self.doc.find_all("html")[0]
        self.assertIn("no-js", html.classes())
        for selector in (dict(id="theme-toggle"), dict(id="menu-toggle"), dict(data_copy=True),
                         dict(cls="trace-replay")):
            for node in self.doc.find_all("button", **selector):
                self.assertIn("js-only", node.classes(), selector)
        self.assertIn("js-only", self.doc.find_all("div", role="group")[0].classes())
        trace = self.doc.find_all(cls="trace")[0]
        self.assertNotIn("is-done", trace.classes())
        self.assertTrue(all("is-done" not in n.classes() for n in trace.iter()))

    def test_jsonld_is_valid_person(self) -> None:
        scripts = self.doc.find_all("script", type="application/ld+json")
        self.assertEqual(len(scripts), 1)
        data = json.loads("".join(c for c in scripts[0].children if isinstance(c, str)))
        self.assertEqual(data["@type"], "Person")


if __name__ == "__main__":
    unittest.main()
