"""
Persistent config — font size offset, last source, subreddit list.
Saved to the user data dir (see paths.py).
"""

import json
import os

from paths import data_file

CONFIG_FILE = data_file("config.json")

DEFAULTS = {
    "font_size_offset": 0,       # -4, -2, 0, +2, +4, +6
    "last_source": "literature",
    "subreddits": ["AskReddit", "todayilearned", "explainlikeimfive"],
}


def load() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Fill in any missing keys with defaults
            for k, v in DEFAULTS.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            pass
    return dict(DEFAULTS)


def save(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get(key: str):
    return load().get(key, DEFAULTS.get(key))


def set_value(key: str, value):
    cfg = load()
    cfg[key] = value
    save(cfg)
