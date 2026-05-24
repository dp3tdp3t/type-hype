"""
Poetry source — public domain poems via PoetryDB (poetrydb.org).
Stanza-aware: keeps stanza breaks as visual separators using ⏎
"""

import os
import json
import random
import re
import ssl
import urllib.request
import urllib.error

from engine.sources.base import ContentSource

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

from paths import data_file
CACHE_FILE = data_file("poetry_cache.json")
FETCH_COUNT = 20   # number of random poems to cache
API_URL = "https://poetrydb.org/random"

# Poets whose work is firmly public domain
PREFERRED_AUTHORS = [
    "Walt Whitman",
    "Emily Dickinson",
    "Edgar Allan Poe",
    "Robert Frost",
    "William Blake",
    "Lord Byron",
    "John Keats",
    "Percy Bysshe Shelley",
    "Alfred Lord Tennyson",
    "Rudyard Kipling",
    "William Wordsworth",
    "Henry Wadsworth Longfellow",
    "Ralph Waldo Emerson",
    "Christina Rossetti",
    "Gerard Manley Hopkins",
]


def _is_clean(line: str) -> bool:
    """True if the line contains only printable ASCII."""
    return bool(line) and not re.search(r'[^\x20-\x7E]', line)


def _fetch_poems(count: int) -> list:
    url = f"{API_URL}/{count}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TypeHype/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
            print(f"[Poetry] PoetryDB responded: {resp.status}")
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Poetry] PoetryDB FAIL: {e}")
        return []


def _parse_poem(poem: dict) -> dict | None:
    """
    Parse a PoetryDB poem into our internal format.
    Returns a dict with title, author, stanzas (list of list of str),
    or None if the poem is unsuitable.
    """
    title = poem.get("title", "").strip()
    author = poem.get("author", "").strip()
    lines = poem.get("lines", [])

    if not lines or not title or not author:
        return None

    # Split into stanzas (blank lines separate stanzas)
    stanzas = []
    current = []
    for line in lines:
        line = line.strip()
        if line == "":
            if current:
                stanzas.append(current)
                current = []
        else:
            if _is_clean(line) and len(line) >= 5:
                current.append(line)
    if current:
        stanzas.append(current)

    # Filter out poems with too many non-ASCII chars
    all_lines = [l for s in stanzas for l in s]
    if not all_lines:
        return None

    return {
        "title": title,
        "author": author,
        "stanzas": stanzas,
    }


class PoetrySource(ContentSource):
    name = "Poetry"
    source_key = "poetry"

    def fetch(self, status_cb=None) -> bool:
        if status_cb:
            status_cb(f"Poetry: fetching {FETCH_COUNT} poems from PoetryDB…")

        # Fetch a larger batch and filter
        raw_poems = _fetch_poems(FETCH_COUNT * 3)
        if not raw_poems:
            if status_cb:
                status_cb("Poetry: PoetryDB unreachable.")
            return False

        poems = []
        for raw in raw_poems:
            parsed = _parse_poem(raw)
            if parsed and parsed["stanzas"]:
                poems.append(parsed)

        # Also try to get some preferred-author poems specifically
        for author in random.sample(PREFERRED_AUTHORS, min(5, len(PREFERRED_AUTHORS))):
            author_url = f"https://poetrydb.org/author/{urllib.parse.quote(author)}/title,author,lines"
            try:
                req = urllib.request.Request(
                    author_url,
                    headers={"User-Agent": "TypeHype/1.0"}
                )
                with urllib.request.urlopen(req, timeout=8, context=_SSL_CTX) as resp:
                    author_poems = json.loads(resp.read().decode("utf-8"))
                if isinstance(author_poems, list):
                    for raw in random.sample(author_poems, min(3, len(author_poems))):
                        parsed = _parse_poem(raw)
                        if parsed and parsed["stanzas"]:
                            poems.append(parsed)
            except Exception:
                continue

        if not poems:
            return False

        # Deduplicate by title
        seen = set()
        unique = []
        for p in poems:
            if p["title"] not in seen:
                seen.add(p["title"])
                unique.append(p)

        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(unique, f)

        if status_cb:
            status_cb(f"Poetry: cached {len(unique)} poems.")
        return True

    def is_ready(self) -> bool:
        return os.path.exists(CACHE_FILE)

    def _load_poems(self) -> list:
        if not os.path.exists(CACHE_FILE):
            return []
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_corpus(self) -> list:
        """Return individual stanzas as flat strings."""
        poems = self._load_poems()
        corpus = []
        for poem in poems:
            for stanza in poem.get("stanzas", []):
                corpus.append(" / ".join(stanza))
        return corpus

    def get_passage(self, duration_seconds: int) -> tuple:
        poems = self._load_poems()
        if not poems:
            return ("No poetry cached. Please fetch first.", "")

        # Pick a random poem
        poem = random.choice(poems)
        stanzas = poem.get("stanzas", [])
        title = poem["title"]
        author = poem["author"]

        if not stanzas:
            return ("", f"{title} — {author}")

        # For short tests pick 1 stanza, longer tests get more
        if duration_seconds <= 30:
            selected = stanzas[:1]
        elif duration_seconds <= 60:
            selected = stanzas[:2]
        elif duration_seconds <= 120:
            selected = stanzas[:4]
        else:
            selected = stanzas  # whole poem

        # Join lines within a stanza with spaces; join stanzas with ⏎ marker
        stanza_strings = []
        for stanza in selected:
            stanza_strings.append(" ".join(stanza))

        passage = "  ⏎  ".join(stanza_strings)
        meta = f'"{title}" — {author}'
        return (passage, meta)


# Need to import urllib.parse for the author URL building
import urllib.parse
