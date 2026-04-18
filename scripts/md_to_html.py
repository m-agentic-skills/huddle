#!/usr/bin/env python3
"""Bundle a huddle note + huddle-state.json and open the review page.

Usage:
    python md_to_html.py <file.md> [base_url]

Resolution order for base_url (first wins):
  1. CLI arg (sys.argv[2]) if provided
  2. `graph_review_url` field in ~/config/muthuishere-agent-skills/userconfig.json
  3. DEFAULT_BASE_URL constant below

Reads huddle-state.json from the same directory as the markdown file.
The graph view is derived client-side in index.html from decisions[].
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
import webbrowser
from pathlib import Path

DEFAULT_BASE_URL = "https://muthuishere-agent-skills.github.io/huddle/index.html"
USER_CONFIG_PATH = Path.home() / "config" / "muthuishere-agent-skills" / "userconfig.json"


def resolve_base_url(cli_arg: str | None) -> str:
    if cli_arg:
        return cli_arg
    if USER_CONFIG_PATH.exists():
        try:
            cfg = json.loads(USER_CONFIG_PATH.read_text(encoding="utf-8"))
            url = cfg.get("graph_review_url")
            if url:
                return url
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_BASE_URL


def encode_bundle(bundle: dict) -> str:
    raw = json.dumps(bundle, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    compressed = gzip.compress(raw, compresslevel=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.md> [base_url]", file=sys.stderr)
        return 1

    md_path = Path(sys.argv[1]).expanduser().resolve()
    cli_arg = sys.argv[2] if len(sys.argv) >= 3 else None
    base_url = resolve_base_url(cli_arg)

    if not md_path.exists():
        print(f"Error: Markdown file not found: {md_path}", file=sys.stderr)
        return 1

    state_path = md_path.with_name("huddle-state.json")
    if not state_path.exists():
        print(f"Error: huddle-state.json not found next to {md_path.name}", file=sys.stderr)
        return 1

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid huddle-state.json — {exc}", file=sys.stderr)
        return 1

    bundle = {
        "source": md_path.name,
        "markdown": md_path.read_text(encoding="utf-8"),
        "state": state,
    }

    encoded = encode_bundle(bundle)
    url = f"{base_url.rstrip('#')}#{encoded}"
    webbrowser.open(url)
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
