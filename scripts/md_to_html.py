#!/usr/bin/env python3
"""Stage a huddle review bundle and open the static review page.

Usage:
    python md_to_html.py <file.md> [base_url]

Behavior:
    - Reads the markdown file.
    - Reads `graph-raw.json` next to it.
    - Validates that Elango-owned raw fields exist.
    - Bundles both into one gzip+base64 URL hash.
    - Opens the static review page, which renders the bundle client-side.
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
import webbrowser
from pathlib import Path

DEFAULT_BASE_URL = "https://m-agentic-skills.github.io/huddle/index.html"


def read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_fields(obj: dict, fields: list[str], context: str) -> None:
    missing = [field for field in fields if not obj.get(field)]
    if missing:
        raise ValueError(f"{context} missing required fields: {', '.join(missing)}")


def validate_raw_payload(data: dict) -> None:
    require_fields(data, ["session_id"], "graph-raw.json")
    for index, actor in enumerate(data.get("actors", [])):
        require_fields(actor, ["id", "name", "icon", "meta"], f"graph-raw.json actors[{index}]")
    for index, source in enumerate(data.get("sources", [])):
        require_fields(source, ["id", "kind", "label", "ref"], f"graph-raw.json sources[{index}]")
    for index, event in enumerate(data.get("events", [])):
        require_fields(event, ["ts", "actor_id", "op", "target", "payload"], f"graph-raw.json events[{index}]")
        require_fields(event["target"], ["id", "kind"], f"graph-raw.json events[{index}].target")


def build_bundle(md_path: Path) -> dict:
    raw_path = md_path.with_name("graph-raw.json")

    markdown = md_path.read_text(encoding="utf-8")
    raw = read_json(raw_path)

    validate_raw_payload(raw)

    return {
        "source": md_path.name,
        "markdown": markdown,
        "raw": raw,
    }


def encode_bundle(bundle: dict) -> str:
    raw = json.dumps(bundle, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    compressed = gzip.compress(raw, compresslevel=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def open_review(md_file: str, base_url: str) -> str:
    md_path = Path(md_file).expanduser().resolve()
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")
    bundle = build_bundle(md_path)
    encoded = encode_bundle(bundle)
    url = f"{base_url.rstrip('#')}#{encoded}"
    webbrowser.open(url)
    return url


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.md> [base_url]", file=sys.stderr)
        return 1

    md_file = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) >= 3 else DEFAULT_BASE_URL

    try:
        url = open_review(md_file, base_url)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
