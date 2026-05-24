"""
Wikipedia source — article intros from a curated, high-quality title list.

Two problems with the old implementation we fix here:

  1. **Rate limiting.** Each refresh used to fire 20 separate
     /random/summary requests with 0.5s delays. Slow, and Wikipedia's
     etiquette guide asks apps to be more frugal. We now make ONE
     batched call to the action API (?action=query&titles=A|B|C...)
     which returns up to 20 article intros in a single round trip.

  2. **Content quality.** /random pulls from all ~6M English articles,
     most of which are obscure village stubs or niche taxonomy entries.
     We instead pick from a curated list (see data/wiki_titles.py) of
     well-known notable topics with substantial articles — better
     typing material across the board.
"""

import os
import json
import random
import re
import ssl
import urllib.parse
import urllib.request

from engine.sources.base import ContentSource
from engine.sources.data.wiki_titles import WIKI_TITLES

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

from paths import data_file
CACHE_FILE = data_file("wiki_cache.json")
API_URL = "https://en.wikipedia.org/w/api.php"

# How many titles to request per refresh. The action API accepts up
# to 50 in one call; 20 gives plenty of variety per fetch without
# bloating the cache.
TITLES_PER_FETCH = 20

# How many sentences of each article's intro to pull. The extracts
# endpoint truncates the lead section at this count.
SENTENCES_PER_ARTICLE = 8

# User-Agent following Wikipedia's policy: app name + contact-style
# identifier. They explicitly ask projects to identify themselves.
USER_AGENT = "TypeHype/1.0 (typing practice; personal project)"


def _clean(text: str) -> str:
    """Remove parenthetical pronunciations and extra whitespace."""
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _batched_fetch(titles: list, status_cb=None) -> dict:
    """Fetch extracts for up to 50 titles in a single API call.

    Returns {title: extract_text} for whichever titles came back with
    usable content. Missing / unknown titles are silently omitted.
    """
    params = {
        "action": "query",
        "format": "json",
        "titles": "|".join(titles),
        "prop": "extracts",
        "explaintext": "1",
        "exintro": "1",
        "exsentences": str(SENTENCES_PER_ARTICLE),
        "redirects": "1",
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Wikipedia] batched fetch FAIL: {e}")
        if status_cb:
            status_cb(f"Wikipedia: fetch failed — {e}")
        return {}

    pages = data.get("query", {}).get("pages", {})
    out = {}
    for page in pages.values():
        title = page.get("title", "")
        extract = page.get("extract", "").strip()
        # "missing" key flags pages the API couldn't find
        if not extract or page.get("missing") is not None:
            continue
        out[title] = extract
    return out


class WikipediaSource(ContentSource):
    name = "Wikipedia"
    source_key = "wikipedia"

    def fetch(self, status_cb=None) -> bool:
        # Pick a random sample of titles. We pick slightly more than
        # we need so a few API misses (typos in the curated list,
        # disambiguation pages, etc.) don't leave us short.
        sample_size = min(len(WIKI_TITLES), TITLES_PER_FETCH + 5)
        sample = random.sample(WIKI_TITLES, sample_size)

        if status_cb:
            status_cb(f"Wikipedia: fetching {sample_size} article intros…")
        results = _batched_fetch(sample, status_cb=status_cb)

        articles = []
        for title, extract in results.items():
            sentences = re.split(r'(?<=[.!?])\s+', extract)
            clean_sents = []
            for s in sentences:
                s = _clean(s)
                if 40 <= len(s) <= 300 and re.match(r'^[A-Za-z]', s):
                    # ASCII only, so foreign-language names don't bog
                    # the typing test down with diacritics the user
                    # would have to remember how to enter.
                    if not re.search(r'[^\x20-\x7E]', s):
                        clean_sents.append(s)
            if clean_sents:
                articles.append({"title": title, "sentences": clean_sents})

        if not articles:
            if status_cb:
                status_cb("Wikipedia: no usable content fetched.")
            return False

        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(articles, f)

        if status_cb:
            status_cb(f"Wikipedia: cached {len(articles)} articles.")
        return True

    def is_ready(self) -> bool:
        return os.path.exists(CACHE_FILE)

    def _load_articles(self) -> list:
        if not os.path.exists(CACHE_FILE):
            return []
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_corpus(self) -> list:
        articles = self._load_articles()
        sentences = []
        for a in articles:
            sentences.extend(a.get("sentences", []))
        return sentences

    def get_passage(self, duration_seconds: int) -> tuple:
        articles = self._load_articles()
        if not articles:
            return ("No Wikipedia content cached. Please fetch first.", "")

        target_chars = int((duration_seconds / 60) * 250 * 1.5)
        target_chars = max(target_chars, 200)

        random.shuffle(articles)
        parts = []
        total = 0
        meta_titles = []

        for article in articles:
            sents = article.get("sentences", [])
            if not sents:
                continue
            meta_titles.append(article["title"])
            for s in sents:
                parts.append(s)
                total += len(s) + 1
                if total >= target_chars:
                    break
            if total >= target_chars:
                break

        passage = " ".join(parts)
        meta = "Wikipedia — " + ", ".join(meta_titles[:2])
        return (passage, meta)
