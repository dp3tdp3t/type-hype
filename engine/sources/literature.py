"""
Classic Literature source — Project Gutenberg.
Wraps the existing text_fetcher logic.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from engine.sources.base import ContentSource
from engine.text_fetcher import (
    build_corpus, load_corpus, CACHE_FILE, get_passage as _get_passage
)


class LiteratureSource(ContentSource):
    name = "Classic Literature"
    source_key = "literature"

    def fetch(self, status_cb=None) -> bool:
        return build_corpus(status_callback=status_cb)

    def is_ready(self) -> bool:
        return os.path.exists(CACHE_FILE)

    def get_corpus(self) -> list:
        return load_corpus()

    def get_passage(self, duration_seconds: int) -> tuple:
        passage = _get_passage(duration_seconds, load_corpus())
        return (passage, "Classic Literature — Project Gutenberg")
