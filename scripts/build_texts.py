#!/usr/bin/env python3
"""Build the text of every document in sources.toml from raw/.

Each document goes to ``texts/ABBR.txt``.  A text file holds the story
title on its first line as ``# Title``, then paragraphs separated by blank
lines; part and chapter headings are ``## `` and ``### `` lines.  Text
that is not Doyle's (the frame narrative of the Franckh reissues,
prefaces, publisher's and translator's front matter) is kept but marked
with a leading ``> `` as the manifest says (``front_until``, ``front``,
``frame_prefix``, ``frame_from``).  ``*`` separators and the site's
advertisements are dropped.  For a novel, the chapter titles listed on
the book page are inserted as ``### `` headings.

Usage::

    uv run scripts/build_texts.py
"""

from __future__ import annotations

import html
import logging
import re
import sys
import tomllib
from pathlib import Path

from pg_extract import extract

logger = logging.getLogger("build_texts")

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "raw"
TEXTS = REPO / "texts"
EDITORIAL = "> "
ADVERT = re.compile(
    r"Neubüch|Neubuch|ISBN|Taschenbüch|Je Band|in unserem Shop|Projekt Gutenberg lebt"
)
CHAPTER_WORD = re.compile(r"\bKapitel\b|\bTeil\b|^Schluß")
SEPARATORS = {"*", "* * *", "***"}


def chapter_titles(book_page: Path) -> dict[int, str]:
    """Read the chapter titles from a saved Gutenberg-DE book page.

    Args:
        book_page: ``raw/SLUG/book.html``

    Returns:
        Chapter number to title, as the reader's table of contents shows
    """
    page = book_page.read_text(encoding="utf-8")
    titles: dict[int, str] = {}
    for m in re.finditer(
        r'href="[^"]*/chapter/(\d+)/?"[^>]*>(.*?)</a>', page, re.DOTALL
    ):
        n = int(m.group(1))
        text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).split())
        text = re.sub(rf"^{n}\s+", "", text)
        titles.setdefault(n, text)
    return titles


def generic_title(listed: str, doc_title: str) -> bool:
    """Return True if a listed chapter title adds nothing worth a heading.

    That is a title page, a bare ``Kapitel N`` or the document's own title.
    """

    def letters(text: str) -> str:
        return re.sub(r"[^\w]", "", text).lower()

    return (
        not listed
        or listed == "Titelseite"
        or re.fullmatch(r"(Kapitel\s*)?\d+", listed) is not None
        or letters(listed) == letters(doc_title)
    )


def chapter_heading(listed: str, inline: str | None) -> str:
    """Combine the table-of-contents title with a heading found in the text.

    The part that names the chapter number (``Erstes Kapitel``) goes first.

    Args:
        listed: Title from the book page
        inline: ``### `` heading at the top of the chapter text, if any

    Returns:
        The heading text without prefix
    """
    if not inline or inline == listed:
        return listed
    parts = sorted([listed, inline], key=lambda s: not CHAPTER_WORD.search(s))
    return " ".join(parts)


def mark(paras: list[str]) -> list[str]:
    """Prefix paragraphs with the editorial marker (headings keep theirs)."""
    return [EDITORIAL + p for p in paras]


def find_paragraph(paras: list[str], start: str, what: str) -> int:
    """Return the index of the first paragraph starting with ``start``.

    Raises:
        ValueError: If no paragraph starts that way
    """
    for i, p in enumerate(paras):
        if p.startswith(start):
            return i
    raise ValueError(f"{what}: no paragraph starts with {start!r}")


def document_paragraphs(book: dict, doc: dict) -> list[str]:
    """Assemble the paragraphs of one document from its chapters.

    Args:
        book: A ``[[book]]`` table from sources.toml
        doc: One of its documents

    Returns:
        Paragraphs including headings, editorial ones marked

    Raises:
        ValueError: If a marker from the manifest is not found
    """
    slug = book["slug"]
    multi = len(doc["chapters"]) > 1
    titles = chapter_titles(RAW / slug / "book.html") if multi else {}
    paras: list[str] = []
    for n in doc["chapters"]:
        chapter = extract(RAW / slug / f"{n}.html")
        if multi and not generic_title(titles.get(n, ""), doc["title"]):
            part = chapter.pop(0) if chapter and chapter[0].startswith("## ") else None
            inline = (
                chapter.pop(0)[4:]
                if chapter and chapter[0].startswith("### ")
                else None
            )
            if part:
                paras.append(part)
            paras.append("### " + chapter_heading(titles[n], inline))
        paras += chapter
    paras = [p for p in paras if p not in SEPARATORS and not ADVERT.search(p)]
    abbr = doc["abbr"]
    front = doc.get("front", 0)
    if "front_until" in doc:
        front = find_paragraph(paras, doc["front_until"], f"{abbr} front_until")
    body = paras[front:]
    tail: list[str] = []
    if "frame_from" in doc:
        cut = find_paragraph(body, doc["frame_from"], f"{abbr} frame_from")
        body, tail = body[:cut], body[cut:]
    lead: list[str] = []
    if "frame_prefix" in doc:
        if not body[0].startswith(doc["frame_prefix"]):
            raise ValueError(f"{abbr}: frame_prefix not found")
        lead = [doc["frame_prefix"].strip()]
        body[0] = body[0][len(doc["frame_prefix"]) :]
    return mark(paras[:front]) + mark(lead) + body + mark(tail)


def main() -> int:
    """Write every document's text file."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    with open(REPO / "sources.toml", "rb") as f:
        books = tomllib.load(f)["book"]
    TEXTS.mkdir(exist_ok=True)
    for book in books:
        for doc in book["documents"]:
            paras = ["# " + doc["title"]] + document_paragraphs(book, doc)
            out = TEXTS / f"{doc['abbr']}.txt"
            out.write_text("\n\n".join(paras) + "\n", encoding="utf-8")
            words = sum(len(p.split()) for p in paras)
            marked = sum(p.startswith(EDITORIAL) for p in paras)
            logger.info(
                "%s: %d paragraphs (%d editorial), %d words",
                out.name,
                len(paras),
                marked,
                words,
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
