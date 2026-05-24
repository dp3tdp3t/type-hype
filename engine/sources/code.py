"""
Code source — typing practice with real programming snippets.

Currently ships Python only via a curated bundle (see
`engine/sources/data/python_snippets.py`). The structure is
language-agnostic so adding JavaScript / Rust / etc. is a matter of
dropping another `<lang>_snippets.py` next to it and registering the
language here.
"""

import random

from engine.sources.base import ContentSource
from engine.sources.data.python_snippets import PYTHON_SNIPPETS


# Registered languages → list of snippet dicts ({"title", "code"}).
_LANGUAGE_BUNDLES = {
    "python": PYTHON_SNIPPETS,
}


class CodeSource(ContentSource):
    """Programming-language typing source. Default language is Python."""

    source_key = "code"

    def __init__(self, language: str = "python"):
        self.language = language
        # Display name reflects the active language so the UI reads
        # naturally in the dropdown ("python (code)").
        self.name = f"{language} (code)"

    # ── Source protocol ──────────────────────────────────────────────

    def fetch(self, status_cb=None) -> bool:
        """Snippets are bundled — `fetch` is a no-op that always succeeds.

        Future enhancement: pull additional snippets from a public
        repo here and merge them into the bundle, gated by network
        availability."""
        if status_cb:
            status_cb(f"{self.language} snippets are bundled — nothing to fetch")
        return True

    def is_ready(self) -> bool:
        return bool(_LANGUAGE_BUNDLES.get(self.language))

    def get_corpus(self) -> list:
        return [s["code"] for s in _LANGUAGE_BUNDLES.get(self.language, [])]

    def get_passage(self, duration_seconds: int) -> tuple:
        """Pick one snippet whose length is a reasonable fit for the
        chosen duration. We pick a single snippet rather than
        concatenating multiple because mid-test boundaries between
        unrelated snippets break the typing flow for code."""
        snippets = _LANGUAGE_BUNDLES.get(self.language, [])
        if not snippets:
            return (f"# No {self.language} snippets bundled.", "")

        # Roughly: 250 keys/min * 1.5x slack at typical typing speed.
        target_chars = max(int((duration_seconds / 60) * 250 * 1.5), 200)

        # Sort by closeness to target length; pick randomly from the
        # top-5 closest so we don't always get the same one for a
        # given duration.
        ranked = sorted(snippets, key=lambda s: abs(len(s["code"]) - target_chars))
        pick_pool = ranked[:5] if len(ranked) >= 5 else ranked
        chosen = random.choice(pick_pool)

        meta = f"{self.language} — {chosen['title']}"
        return (chosen["code"], meta)
