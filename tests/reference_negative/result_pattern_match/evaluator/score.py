"""Synthetic negative: semantic-content validation."""

from __future__ import annotations

import json
from html.parser import HTMLParser


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        style = (attrs_d.get("style") or "").lower()
        if "display:none" in style.replace(" ", "") or tag in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag):
        if self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def score(rendered_html: str, expected_answer: str) -> float:
    parser = _VisibleText()
    parser.feed(rendered_html)
    visible = " ".join(parser.parts).strip()
    return 1.0 if visible == expected_answer else 0.0


def parse_structured(agent_output: str):
    return json.loads(agent_output)
