#!/usr/bin/env python3
"""Stage a huddle review bundle and open the static review page.

Usage:
    python md_to_html.py <file.md> [base_url]

Behavior:
    - Reads the markdown file.
    - Reads `graph-view.json` next to it.
    - Validates that Elango-owned view fields exist.
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


def validate_view_payload(data: dict) -> None:
    require_fields(data, ["main_question", "decision", "decision_why"], "graph-view.json")
    for index, item in enumerate(data.get("what_stands_out", [])):
        require_fields(item, ["icon", "text"], f"graph-view.json what_stands_out[{index}]")
    for index, person in enumerate(data.get("people_involved", [])):
        require_fields(person, ["id", "name", "icon", "meta", "influence"], f"graph-view.json people_involved[{index}]")
    for index, item in enumerate(data.get("key_moments", [])):
        require_fields(item, ["id", "icon", "title", "detail"], f"graph-view.json key_moments[{index}]")
    for index, item in enumerate(data.get("evidence", [])):
        require_fields(item, ["id", "icon", "label", "kind", "ref", "note"], f"graph-view.json evidence[{index}]")
    for index, node in enumerate(data.get("nodes", [])):
        require_fields(node, ["id", "kind", "label", "status", "icon", "why_it_matters"], f"graph-view.json nodes[{index}]")
    for index, edge in enumerate(data.get("edges", [])):
        require_fields(edge, ["from", "to", "relation", "label"], f"graph-view.json edges[{index}]")


def build_bundle(md_path: Path) -> dict:
    view_path = md_path.with_name("graph-view.json")

    markdown = md_path.read_text(encoding="utf-8")
    view = read_json(view_path)

    validate_view_payload(view)

    return {
        "source": md_path.name,
        "markdown": markdown,
        "view": view,
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
