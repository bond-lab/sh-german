#!/usr/bin/env python3
"""Extract chapter text from Projekt Gutenberg-DE book-reader pages.

The text of a page is the first ``book-reader__chapter-content-wrapper``
div.  Each paragraph becomes one line; ``<h2>`` headings become ``## ``
lines and ``<h3>``/``<h4>`` headings ``### `` lines.  Figures (``<div
class="figure">`` with a book image) are dropped; when the paragraph
before a figure stops mid-sentence, as the dancing-men cipher pictures
do, the paragraphs on either side are joined.

Usage::

    python3 -I scripts/pg_extract.py raw/SLUG/N.html ...

writes ``N.txt`` beside each page.  ``build_texts.py`` imports
:func:`extract` instead.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

FIGURE = "[FIGURE]"
INLINE = "[INLINE]"
PARA_END = ".!?:«»‹›'\"…"
BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "br", "div", "li"}
HEADING_PREFIX = {"h2": "## ", "h3": "### ", "h4": "### ", "h5": "### "}


class Extractor(HTMLParser):
    """Collect the text of the first chapter-content wrapper on a page."""

    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.inside = False
        self.done = False
        self.skip = 0
        self.in_heading = False
        self.out: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        cls = dict(attrs).get("class") or ""
        if (
            not self.inside
            and not self.done
            and tag == "div"
            and "chapter-content-wrapper" in cls
        ):
            self.inside = True
            self.depth = 1
            return
        if not self.inside:
            return
        if tag == "div":
            self.depth += 1
        if tag in ("script", "style"):
            self.skip += 1
        if tag == "br" and self.in_heading:
            self.out.append(" ")
        elif tag in BLOCK_TAGS:
            self.out.append("\n")
        if tag in HEADING_PREFIX:
            self.in_heading = True
            self.out.append(HEADING_PREFIX[tag])
        elif tag == "h1":
            # a word set as a display heading inside the text (RACHE on the wall)
            self.out.append(INLINE)
        if tag == "img" and "book-image" in cls:
            self.out.append(f"\n{FIGURE}\n")

    def handle_endtag(self, tag: str) -> None:
        if not self.inside:
            return
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag in BLOCK_TAGS and not (tag == "br" and self.in_heading):
            self.out.append("\n")
        if tag in HEADING_PREFIX:
            self.in_heading = False
        if tag == "div":
            self.depth -= 1
            if self.depth == 0:
                self.inside = False
                self.done = True

    def handle_data(self, data: str) -> None:
        if self.inside and not self.skip:
            self.out.append(data)


def paragraphs(text: str) -> list[str]:
    """Turn extracted text into paragraphs, resolving figure markers.

    Args:
        text: Raw text with one block per line and FIGURE markers

    Returns:
        Paragraphs (headings keep their ``## `` prefix), with each figure
        dropped and the paragraphs around it joined when the one before
        it does not end a sentence; a display word inside a sentence
        (``<h1>`` in the text) is joined to its neighbours the same way
    """
    lines = [" ".join(line.split()) for line in text.split("\n")]
    paras: list[str] = []
    join_next = False
    for line in lines:
        if not line or line in ("#", "##", "###"):
            continue
        if line == FIGURE:
            join_next = bool(paras) and paras[-1][-1] not in PARA_END
            continue
        if line.startswith(INLINE):
            line = line[len(INLINE) :]
            join_next = join_next or (bool(paras) and paras[-1][-1] not in PARA_END)
            if join_next:
                paras[-1] += " " + line
            else:
                paras.append(line)
            join_next = line[-1] not in PARA_END
            continue
        if join_next:
            paras[-1] += " " + line
            join_next = False
        else:
            paras.append(line)
    return paras


def extract(path: Path) -> list[str]:
    """Return the paragraphs of a saved Gutenberg-DE chapter page.

    Args:
        path: The HTML file

    Returns:
        The chapter's paragraphs, see :func:`paragraphs`
    """
    parser = Extractor()
    parser.feed(path.read_text(encoding="utf-8"))
    return paragraphs("".join(parser.out))


def main(paths: list[str]) -> None:
    """Extract each HTML file named in ``paths`` to a text file beside it."""
    for name in paths:
        path = Path(name)
        paras = extract(path)
        out = path.with_suffix(".txt")
        out.write_text("\n\n".join(paras) + "\n", encoding="utf-8")
        print(out, len(paras), "paragraphs")


if __name__ == "__main__":
    main(sys.argv[1:])
