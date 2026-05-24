"""
Reddit source — top comments from user-selected subreddits.
Uses the public .json API — no API key needed.
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
CACHE_FILE = data_file("reddit_cache.json")
DEFAULT_SUBS = ["AskReddit", "todayilearned", "explainlikeimfive"]
COMMENTS_PER_SUB = 30


def _strip_markdown(text: str) -> str:
    """Remove Reddit markdown formatting."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)         # italic
    text = re.sub(r'~~(.+?)~~', r'\1', text)         # strikethrough
    text = re.sub(r'`(.+?)`', r'\1', text)           # inline code
    text = re.sub(r'^>.*$', '', text, flags=re.M)    # blockquotes
    text = re.sub(r'^#+\s+', '', text, flags=re.M)   # headers
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # links
    text = re.sub(r'\n{2,}', ' ', text)              # paragraph breaks
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _fetch_comments(subreddit: str, status_cb=None) -> list:
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=50&t=month"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TypeHype/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
            print(f"[Reddit] r/{subreddit} responded: {resp.status}")
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Reddit] r/{subreddit} FAIL: {e}")
        if status_cb:
            status_cb(f"Reddit: failed to fetch r/{subreddit} — {e}")
        return []

    comments = []
    posts = data.get("data", {}).get("children", [])
    for post in posts:
        pd = post.get("data", {})
        # Use the post selftext if it exists and is long enough
        selftext = pd.get("selftext", "").strip()
        if selftext and selftext not in ("[removed]", "[deleted]"):
            cleaned = _strip_markdown(selftext)
            if 60 <= len(cleaned) <= 500:
                if not re.search(r'[^\x20-\x7E]', cleaned):
                    comments.append({"sub": subreddit, "text": cleaned})

        # Also use post title if it's a good sentence
        title = pd.get("title", "").strip()
        if 40 <= len(title) <= 200 and not re.search(r'[^\x20-\x7E]', title):
            comments.append({"sub": subreddit, "text": title})

    return comments[:COMMENTS_PER_SUB]


class RedditSource(ContentSource):
    name = "Reddit"
    source_key = "reddit"

    def __init__(self, subreddits: list = None):
        self.subreddits = subreddits or list(DEFAULT_SUBS)

    def set_subreddits(self, subs: list):
        # If the list changed, delete the old cache so stale content isn't served
        if subs != self.subreddits and os.path.exists(CACHE_FILE):
            try:
                os.remove(CACHE_FILE)
                print(f"[Reddit] Subreddit list changed — cleared stale cache")
            except Exception:
                pass
        self.subreddits = list(subs)

    def clear_cache(self):
        """Delete the cache file so the source becomes 'not ready'.

        Called when the subreddit list changes mid-session — without
        this, residual passages from removed subs keep showing up in
        tests until the next successful refresh."""
        if os.path.exists(CACHE_FILE):
            try:
                os.remove(CACHE_FILE)
                print(f"[Reddit] Cache cleared")
            except Exception:
                pass

    def fetch(self, status_cb=None) -> bool:
        # Always re-read subreddits from config at fetch time so restarts pick up changes
        import config as cfg
        saved_subs = cfg.get("subreddits")
        if saved_subs:
            self.subreddits = saved_subs

        # Clear the cache before fetching so a partial / failed refresh
        # doesn't leave stale content behind. Refresh = always start fresh.
        self.clear_cache()

        all_comments = []
        for sub in self.subreddits:
            if status_cb:
                status_cb(f"Reddit: fetching r/{sub}…")
            comments = _fetch_comments(sub, status_cb)
            all_comments.extend(comments)
            if status_cb:
                status_cb(f"Reddit: got {len(comments)} items from r/{sub}")

        if not all_comments:
            return False

        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"subreddits": self.subreddits, "comments": all_comments}, f)

        return True

    def is_ready(self) -> bool:
        return os.path.exists(CACHE_FILE)

    def _load(self) -> list:
        if not os.path.exists(CACHE_FILE):
            return []
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("comments", [])

    def get_corpus(self) -> list:
        return [c["text"] for c in self._load()]

    def get_passage(self, duration_seconds: int) -> tuple:
        comments = self._load()
        if not comments:
            return ("No Reddit content cached. Please fetch first.", "")

        target_chars = int((duration_seconds / 60) * 250 * 1.5)
        target_chars = max(target_chars, 200)

        random.shuffle(comments)
        parts = []
        total = 0
        subs_used = set()

        for c in comments:
            parts.append(c["text"])
            subs_used.add(c["sub"])
            total += len(c["text"]) + 1
            if total >= target_chars:
                break

        passage = " ".join(parts)
        meta = "Reddit — " + ", ".join(f"r/{s}" for s in sorted(subs_used))
        return (passage, meta)
