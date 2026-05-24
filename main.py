#!/usr/bin/env python3
"""
type hype — entry point.
Run with: python main.py
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from paths import migrate_legacy_data
from app import App


def main():
    # Copy in-repo `data/` to the user data dir on first run so
    # dev-mode history isn't lost when transitioning to the packaged
    # build. No-op in the packaged bundle.
    migrate_legacy_data()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
