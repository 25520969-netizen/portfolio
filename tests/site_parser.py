"""Tiny DOM built on html.parser, used by the structure/i18n tests."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterator

ROOT: Path = Path(__file__).resolve().parent.parent
SITE: Path = ROOT / "site"
INDEX: Path = SITE / "index.html"
sys.path.insert(0, str(ROOT / "scripts"))

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "source", "track", "wbr"}


def _collapse(text: str) -> str:
    return " ".join(text.split())


@dataclass(eq=False)
class Node:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list["Node | str"] = field(default_factory=list)
    parent: "Node | None" = None

    def text(self) -> str:
        parts: list[str] = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.text())
        return _collapse(" ".join(parts)) if self.tag == "#root" else _collapse("".join(parts))

    def inner_html(self) -> str:
        out: list[str] = []
        for child in self.children:
            if isinstance(child, str):
                out.append(escape(child, quote=False))
            else:
                out.append(child._outer_html())
        return _collapse("".join(out))

    def _outer_html(self) -> str:
        attrs = "".join(
            f" {k}" if v is None else f' {k}="{escape(v)}"' for k, v in self.attrs.items()
        )
        if self.tag in VOID_TAGS:
            return f"<{self.tag}{attrs}>"
        return f"<{self.tag}{attrs}>{self.inner_html()}</{self.tag}>"

    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())

    def element_children(self) -> list["Node"]:
        return [c for c in self.children if isinstance(c, Node)]

    def iter(self) -> Iterator["Node"]:
        yield self
        for child in self.element_children():
            yield from child.iter()

    def find_all(self, tag: str | None = None, cls: str | None = None,
                 **attrs: str | bool) -> list["Node"]:
        wanted = {k.replace("_", "-"): v for k, v in attrs.items()}
        found: list[Node] = []
        for node in self.iter():
            if node is self or (tag and node.tag != tag):
                continue
            if cls and cls not in node.classes():
                continue
            if all((name in node.attrs) if val is True else node.attrs.get(name) == val
                   for name, val in wanted.items()):
                found.append(node)
        return found


class _Builder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.stack: list[Node] = [self.root]

    def _make(self, tag: str, attrs: list[tuple[str, str | None]]) -> Node:
        node = Node(tag, dict(attrs), [], self.stack[-1])
        self.stack[-1].children.append(node)
        return node

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = self._make(tag, attrs)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._make(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def parse_html(path: Path = INDEX) -> Node:
    builder = _Builder()
    builder.feed(path.read_text(encoding="utf-8"))
    builder.close()
    return builder.root
