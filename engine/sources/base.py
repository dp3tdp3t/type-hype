"""
Abstract base class for all content sources.
"""

import random


class ContentSource:
    name = "Unknown"          # shown in dropdown
    source_key = "unknown"    # used in config / CSV logging

    def fetch(self, status_cb=None) -> bool:
        """Download and cache content. Return True on success."""
        raise NotImplementedError

    def is_ready(self) -> bool:
        """Return True if cached content is available."""
        raise NotImplementedError

    def get_corpus(self) -> list:
        """Return list of passage strings."""
        raise NotImplementedError

    def get_passage(self, duration_seconds: int) -> tuple:
        """
        Return (passage_text, metadata_string).
        passage_text  — the string the user will type
        metadata_string — e.g. 'The Raven — Edgar Allan Poe'
        """
        corpus = self.get_corpus()
        if not corpus:
            return ("The quick brown fox jumps over the lazy dog.", "")

        target_chars = int((duration_seconds / 60) * 250 * 1.5)
        target_chars = max(target_chars, 200)

        pool = corpus[:]
        random.shuffle(pool)

        parts = []
        total = 0
        for item in pool:
            parts.append(item)
            total += len(item) + 1
            if total >= target_chars:
                break

        return (" ".join(parts), "")
