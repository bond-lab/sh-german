#!/usr/bin/env python3
"""Download the Projekt Gutenberg-DE pages named in sources.toml into raw/.

For each book this fetches the book page (``raw/SLUG/book.html``, which
lists the chapter titles) and every chapter used (``raw/SLUG/N.html``).
Files already present are kept.

Usage::

    uv run scripts/fetch.py [--force]
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
import tomllib
import urllib.request
from pathlib import Path

logger = logging.getLogger("fetch")

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "raw"
BASE = "https://projekt-gutenberg.org/authors/arthur-conan-doyle/books/"
HEADERS = {"User-Agent": "Mozilla/5.0 (sh-german corpus builder)"}


def fetch(url: str, dest: Path, force: bool = False) -> bool:
    """Save ``url`` to ``dest`` unless it is already there.

    Args:
        url: Page to download
        dest: Where to save it
        force: Download even if dest exists

    Returns:
        True if a download happened
    """
    if dest.exists() and not force:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as resp:
        dest.write_bytes(resp.read())
    logger.info("fetched %s", dest.relative_to(REPO))
    time.sleep(1)
    return True


def main(argv: list[str] | None = None) -> int:
    """Fetch every page listed in sources.toml."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    with open(REPO / "sources.toml", "rb") as f:
        books = tomllib.load(f)["book"]
    count = 0
    for book in books:
        slug = book["slug"]
        count += fetch(f"{BASE}{slug}/", RAW / slug / "book.html", args.force)
        chapters = sorted({c for d in book["documents"] for c in d["chapters"]})
        for n in chapters:
            url = f"{BASE}{slug}/chapter/{n}/"
            count += fetch(url, RAW / slug / f"{n}.html", args.force)
    logger.info("%d files downloaded", count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
