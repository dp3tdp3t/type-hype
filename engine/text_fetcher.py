"""
Fetches and caches text from Project Gutenberg for typing practice.
Falls back to a built-in corpus if the network is unavailable.
"""

import os
import re
import random
import ssl
import urllib.request
import urllib.error

# macOS Python installs often lack system SSL certs. This context bypasses
# certificate verification for our read-only public-domain text fetching.
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

from paths import data_file
CACHE_FILE = data_file("corpus_cache.txt")

# A handful of short, well-known Gutenberg plain-text URLs
GUTENBERG_URLS = [
    "https://www.gutenberg.org/files/1342/1342-0.txt",   # Pride and Prejudice
    "https://www.gutenberg.org/files/11/11-0.txt",       # Alice in Wonderland
    "https://www.gutenberg.org/files/84/84-0.txt",       # Frankenstein
    "https://www.gutenberg.org/files/1661/1661-0.txt",   # Sherlock Holmes
    "https://www.gutenberg.org/files/98/98-0.txt",       # A Tale of Two Cities
]

FALLBACK_SENTENCES = [
    "The quick brown fox jumps over the lazy dog near the riverbank.",
    "She opened the old wooden door and stepped into the dimly lit room.",
    "The sun set slowly behind the mountains, painting the sky in shades of orange and red.",
    "He picked up the worn leather book and began to read the first chapter.",
    "A gentle breeze stirred the leaves on the trees as the afternoon faded.",
    "The cat sat quietly on the windowsill, watching the rain fall on the cobblestones.",
    "They walked along the narrow path that wound through the ancient forest.",
    "The old clock on the mantelpiece ticked steadily through the silent evening.",
    "She wrote a long letter by candlelight and sealed it with red wax.",
    "The market was crowded with people buying bread, fish, and fresh vegetables.",
    "He found the key beneath the loose floorboard, just as he had been told.",
    "The children ran through the tall grass, laughing and calling to each other.",
    "A thin layer of frost covered the meadow in the early morning light.",
    "The captain stood at the bow of the ship, scanning the horizon for land.",
    "Every evening she would sit by the fire and listen to the wind outside.",
    "The letter arrived on a Tuesday, bearing a stamp from a distant country.",
    "He had not expected to find the library open at such a late hour.",
    "The mountains rose sharply from the valley floor, their peaks lost in cloud.",
    "She tasted the soup and added a little salt before calling everyone to dinner.",
    "The old man told stories of the sea that none of the younger men believed.",
    "A crow landed on the fence post and regarded them with a sharp black eye.",
    "The path through the woods was narrow and overgrown with twisted roots.",
    "He placed the envelope on the table and sat down to wait for an answer.",
    "The museum was quiet except for the soft footsteps of a few late visitors.",
    "She had always believed that hard work would eventually bring its own reward.",
    "The train slowed as it entered the valley, and passengers pressed to the windows.",
    "A single candle burned in the window of the stone house at the edge of town.",
    "The fisherman cast his line and settled in to wait with practiced patience.",
    "They discovered the hidden room behind the bookshelf on the second floor.",
    "The melody drifted through the open window from somewhere down the street.",
]


def _clean_text(raw: str) -> str:
    """Strip Gutenberg headers/footers and normalize whitespace."""
    # Remove everything before the actual text start markers
    for marker in ["*** START OF", "***START OF", "* START OF"]:
        idx = raw.find(marker)
        if idx != -1:
            raw = raw[idx:]
            raw = raw[raw.find("\n") + 1:]
            break

    # Remove everything after the end marker
    for marker in ["*** END OF", "***END OF", "* END OF"]:
        idx = raw.find(marker)
        if idx != -1:
            raw = raw[:idx]
            break

    # Collapse multiple newlines / whitespace
    raw = re.sub(r'\r\n', '\n', raw)
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    return raw.strip()


def _extract_sentences(text: str) -> list:
    """Split text into clean, typable sentences."""
    # Split on sentence-ending punctuation followed by whitespace
    chunks = re.split(r'(?<=[.!?])\s+', text)
    sentences = []
    for chunk in chunks:
        # Remove newlines within a sentence and strip
        line = re.sub(r'\s+', ' ', chunk).strip()
        # Keep sentences that are reasonable length and have no weird chars
        if 40 <= len(line) <= 300:
            if re.match(r'^[A-Za-z]', line):  # starts with a letter
                if not re.search(r'[^\x20-\x7E]', line):  # only printable ASCII
                    sentences.append(line)
    return sentences


def _fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
        raw_bytes = resp.read()
    # Try UTF-8 first, fall back to latin-1
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return raw_bytes.decode("latin-1")


def build_corpus(status_callback=None) -> bool:
    """
    Download books from Gutenberg and cache sentences locally.
    Returns True on success, False if network unavailable.
    """
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    all_sentences = []
    fetched = 0
    for url in GUTENBERG_URLS:
        try:
            if status_callback:
                status_callback(f"Fetching: {url.split('/')[-1]}...")
            print(f"[Literature] Trying: {url}")
            raw = _fetch_url(url)
            text = _clean_text(raw)
            sents = _extract_sentences(text)
            all_sentences.extend(sents)
            fetched += 1
            print(f"[Literature] OK: {len(sents)} sentences")
            if status_callback:
                status_callback(f"  Got {len(sents)} sentences.")
        except Exception as e:
            print(f"[Literature] FAIL: {e}")
            if status_callback:
                status_callback(f"  Skipped ({e})")
            continue

    if all_sentences:
        random.shuffle(all_sentences)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(all_sentences))
        return True
    return False


def load_corpus() -> list:
    """Load cached sentences, falling back to built-in list."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if lines:
            return lines
    return FALLBACK_SENTENCES[:]


def get_passage(duration_seconds: int, corpus: list = None) -> str:
    """
    Return a passage long enough to fill roughly `duration_seconds` of typing
    at ~50 WPM (comfortable average).  Joins random sentences until target length.
    """
    if corpus is None:
        corpus = load_corpus()

    # ~50 WPM = 250 chars/min; add 50% buffer so fast typists don't run out
    target_chars = int((duration_seconds / 60) * 250 * 1.5)
    target_chars = max(target_chars, 200)

    pool = corpus[:]
    random.shuffle(pool)

    passage_parts = []
    total = 0
    for sent in pool:
        passage_parts.append(sent)
        total += len(sent) + 1
        if total >= target_chars:
            break

    return " ".join(passage_parts)
