#!/usr/bin/env python3
"""Convert the text files to NTU-MC corpus XML, one file per document.

``texts/ABBR.txt`` becomes ``ntumc/ABBR.xml``.  The output follows
``ntumc.dtd`` from github.com/bond-lab/NTUMC (ids ``deu-dN``, ``deu-sN``,
``deu-sNwN``).  spaCy (de_core_news_sm) splits sentences and tokens and
supplies lemma, STTS and universal POS tags.  The N-th document of the
manifest is numbered ``docnum_offset + N`` (``[corpus]`` in sources.toml)
and its sentences ``10000 * docnum + i``, so all the files can be loaded
into one database, next to those of a sister corpus with another offset.
Sentences of editorial paragraphs (``> `` in the text) carry a comment.

Usage::

    uv run scripts/ntumc_xml.py [ABBR ...]
"""

from __future__ import annotations

import argparse
import logging
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import quoteattr

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span

logger = logging.getLogger("ntumc_xml")

REPO = Path(__file__).resolve().parent.parent
TEXTS = REPO / "texts"
OUT = REPO / "ntumc"
LANG = "deu"
EDITORIAL = "> "
EDITORIAL_COMMENT = (
    "editorial: not in Doyle's text (frame narrative, preface or front matter)"
)
AUTHOR = "Arthur Conan Doyle"
BASE_URL = "https://projekt-gutenberg.org/authors/arthur-conan-doyle/books/"
UPOS = {
    "ADJ",
    "ADP",
    "ADV",
    "AUX",
    "CCONJ",
    "DET",
    "INTJ",
    "NOUN",
    "NUM",
    "PART",
    "PRON",
    "PROPN",
    "PUNCT",
    "SCONJ",
    "SYM",
    "VERB",
    "X",
}
NO_BREAK_AFTER = {";", ":", ","}
HEADINGS = {"# ": "h1", "## ": "h2", "### ": "h3"}


@dataclass(frozen=True)
class DocMeta:
    """What the XML needs to know about one document."""

    number: int
    abbr: str
    title: str
    english: str
    url: str
    translator_line: str


def translator_line(book: dict) -> str:
    """Describe the translation in one line for the front matter."""
    year = f", {book['year']}" if book.get("year") else ""
    where = f"{book['publisher']}{year}"
    if book.get("translator"):
        return f"Übersetzt von {book['translator']} ({where})"
    return f"Übersetzung: {where} (Übersetzer nicht genannt)"


def load_manifest() -> tuple[dict, list[DocMeta]]:
    """Read sources.toml into the corpus table and document metadata.

    Returns:
        The ``[corpus]`` table (name, docnum_offset, license) and the
        documents in manifest order
    """
    with open(REPO / "sources.toml", "rb") as f:
        manifest = tomllib.load(f)
    corpus = manifest["corpus"]
    docs = []
    for book in manifest["book"]:
        for doc in book["documents"]:
            docs.append(
                DocMeta(
                    number=corpus["docnum_offset"] + len(docs) + 1,
                    abbr=doc["abbr"],
                    title=doc["title"],
                    english=doc["english"],
                    url=f"{BASE_URL}{book['slug']}/chapter/{doc['chapters'][0]}/",
                    translator_line=translator_line(book),
                )
            )
    return corpus, docs


def starts_lowercase(span: Span) -> bool:
    """Return True if the first alphabetic token of ``span`` is lowercase."""
    first = next((tok for tok in span if tok.is_alpha), None)
    return first is not None and first.text[:1].islower()


def ends_in_ellipsis(span: Span) -> bool:
    """Return True if ``span`` ends in a spaced ellipsis such as ``. .``."""
    return len(span) > 1 and span[-1].text == "." and span[-2].text == "."


def sentences(doc: Doc) -> list[Span]:
    """Split a paragraph into sentences, keeping clauses together.

    spaCy's parser starts a new sentence after ';', ':' and ',' and inside
    spaced ellipses; the English side of the corpus keeps these in one
    sentence, and a German sentence never starts with a lowercase word or
    consists of punctuation alone.  Such sentences are merged into the one
    before.

    Args:
        doc: A parsed paragraph

    Returns:
        The sentence spans, in order
    """
    merged: list[Span] = []
    for span in doc.sents:
        if merged and (
            merged[-1][-1].text in NO_BREAK_AFTER
            or ends_in_ellipsis(merged[-1])
            or starts_lowercase(span)
            or not any(tok.is_alpha for tok in span)
        ):
            merged[-1] = doc[merged[-1].start : span.end]
        else:
            merged.append(span)
    return merged


def attrs(**kw: object) -> str:
    """Render keyword arguments as XML attributes, skipping None and ''."""
    return " ".join(
        f"{k}={quoteattr(str(v))}" for k, v in kw.items() if v not in (None, "")
    )


def word_elements(sid: int, span: Span) -> list[str]:
    """Render the tokens of one sentence as ``<Word/>`` elements."""
    lines = []
    for i, tok in enumerate(span):
        lemma = tok.lemma_ if tok.lemma_ and tok.lemma_ != "--" else tok.text
        cfrom = tok.idx - span.start_char
        lines.append(
            "      <Word "
            + attrs(
                wid=f"{LANG}-s{sid}w{i}",
                lemma=lemma,
                surface_form=tok.text,
                upos=tok.pos_ if tok.pos_ in UPOS else None,
                pos=tok.tag_,
                cfrom=cfrom,
                cto=cfrom + len(tok.text),
            )
            + "/>"
        )
    return lines


def sentence_element(
    sid: int,
    span: Span,
    pid: str | None = None,
    stype: str | None = None,
    comment: str | None = None,
) -> list[str]:
    """Render one sentence with its words, structural tag and comment."""
    lines = [
        "    <Sentence "
        + attrs(sid=f"{LANG}-s{sid}", sent=span.text, pid=pid, comment=comment)
        + ">"
    ]
    lines += word_elements(sid, span)
    if stype:
        lines.append(f'      <Tag category="stype" value="{stype}"/>')
    lines.append("    </Sentence>")
    return lines


def read_text(path: Path) -> list[tuple[str | None, bool, str]]:
    """Read a text file into (heading level or None, editorial, text) blocks.

    Args:
        path: ``texts/ABBR.txt``

    Returns:
        One tuple per paragraph or heading; level is ``h1``..``h3`` and
        editorial is True for ``> `` paragraphs
    """
    blocks = []
    for chunk in path.read_text(encoding="utf-8").split("\n\n"):
        text = " ".join(chunk.split())
        if not text:
            continue
        editorial = text.startswith(EDITORIAL)
        if editorial:
            text = text[len(EDITORIAL) :]
        for prefix, level in HEADINGS.items():
            if text.startswith(prefix):
                blocks.append((level, editorial, text[len(prefix) :]))
                break
        else:
            blocks.append((None, editorial, text))
    return blocks


def document_xml(nlp: Language, corpus: dict, meta: DocMeta) -> str:
    """Render one document as a complete ``<Corpus>`` file.

    The front matter after the title is the author (``author``), the
    English title in parentheses and the translator line (``translator``);
    then each paragraph with ``pid`` and ``p`` on its first sentence.

    Args:
        nlp: Loaded spaCy pipeline
        corpus: The ``[corpus]`` table of the manifest
        meta: The document's metadata

    Returns:
        The XML text
    """
    blocks = read_text(TEXTS / f"{meta.abbr}.txt")
    sid = meta.number * 10000
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE Corpus SYSTEM "ntumc.dtd">',
        "<Corpus "
        + attrs(
            corpusID=f"{corpus['name']}-{meta.abbr}",
            title="Sherlock Holmes in German translation",
            linguality="monolingual",
            license=corpus["license"],
        )
        + ">",
        "  <Document "
        + attrs(
            docID=f"{LANG}-d{meta.number}",
            doc=meta.abbr,
            language=LANG,
            title=meta.title,
            subtitle=meta.english,
            url=meta.url,
            collection="story",
            collection_title="Kurzgeschichten",
            genre="fiction",
        )
        + ">",
    ]
    front = [
        (AUTHOR, "author"),
        (f"({meta.english})", None),
        (meta.translator_line, "translator"),
    ]
    pnum = 0
    for i, (level, editorial, text) in enumerate(blocks):
        comment = EDITORIAL_COMMENT if editorial else None
        if level:
            lines += sentence_element(sid, nlp(text)[:], stype=level, comment=comment)
            sid += 1
            if i == 0:
                for ftext, stype in front:
                    lines += sentence_element(sid, nlp(ftext)[:], stype=stype)
                    sid += 1
            continue
        pnum += 1
        for j, span in enumerate(sentences(nlp(text))):
            lines += sentence_element(
                sid,
                span,
                pid=f"p{pnum}",
                stype="p" if j == 0 else None,
                comment=comment,
            )
            sid += 1
    lines += ["  </Document>", "</Corpus>"]
    logger.info("%s: %d sentences", meta.abbr, sid - meta.number * 10000)
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write ntumc/ABBR.xml for the documents named, or all of them."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("abbr", nargs="*", help="documents to convert (default: all)")
    ap.add_argument("--model", default="de_core_news_sm", help="spaCy model name")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    nlp = spacy.load(args.model)
    corpus, docs = load_manifest()
    OUT.mkdir(exist_ok=True)
    for meta in docs:
        if args.abbr and meta.abbr not in args.abbr:
            continue
        (OUT / f"{meta.abbr}.xml").write_text(
            document_xml(nlp, corpus, meta), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
