"""Loads settings from config.json so buyers can customise the bot without editing code."""

import json
import sys
from pathlib import Path

# config.json lives in the project root (one folder above this file).
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config() -> dict:
    """Read config.json and return it as a dictionary.

    Exits with a friendly message if the file is missing or has a JSON typo,
    instead of showing a long confusing traceback.
    """
    if not CONFIG_PATH.exists():
        sys.exit(f"[config] Could not find {CONFIG_PATH}. Did you delete or rename it?")

    try:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(
            f"[config] config.json has a formatting error on line {e.lineno}, column {e.colno}: {e.msg}\n"
            "         Tip: check for a missing comma, a trailing comma, or a missing quote."
        )


def to_id(value) -> int:
    """Turn a channel/guild ID from the config into an int.

    Accepts both numbers (123) and strings ("123"), because buyers often paste
    IDs with quotes. Returns 0 if the value is empty or invalid.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
