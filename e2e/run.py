#!/usr/bin/env python3
"""Smoke-test huddle state and review scripts end to end."""

from __future__ import annotations

import base64
import gzip
import json
import shutil
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> str:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True, check=True, env=merged_env)
    return result.stdout.strip()


def decode_hash(url: str) -> dict:
    hash_value = url.split("#", 1)[1]
    padding = "=" * ((4 - len(hash_value) % 4) % 4)
    raw = base64.urlsafe_b64decode(hash_value + padding)
    return json.loads(gzip.decompress(raw).decode("utf-8"))


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp(prefix="huddle-e2e-"))
    home = tmp_root / "home"
    sample = tmp_root / "sample"
    home.mkdir(parents=True, exist_ok=True)
    sample.mkdir(parents=True, exist_ok=True)

    try:
        note = sample / "2026-04-05.md"
        note.write_text("# Huddle\n\nE2E raw-only viewer test.\n", encoding="utf-8")

        raw = {
            "session_id": "2026-04-05-main",
            "actors": [
                {"id": "user", "name": "Muthukumaran", "icon": "🎼", "meta": "You"},
                {"id": "elango", "name": "Elango", "icon": "📐", "meta": "Background State Worker"},
            ],
            "sources": [
                {
                    "id": "src1",
                    "kind": "github",
                    "label": "Hosted viewer",
                    "ref": "https://m-agentic-skills.github.io/huddle/index.html",
                }
            ],
            "events": [
                {
                    "ts": "2026-04-05T10:00:00Z",
                    "actor_id": "user",
                    "op": "node_added",
                    "target": {"id": "n1", "kind": "issue"},
                    "payload": {
                        "label": "Viewer should derive graph from raw on request",
                        "status": "active",
                        "source_refs": ["src1"],
                        "note": "This is the central viewer requirement.",
                    },
                },
                {
                    "ts": "2026-04-05T10:05:00Z",
                    "actor_id": "user",
                    "op": "decision_recorded",
                    "target": {"id": "n2", "kind": "decision"},
                    "payload": {
                        "label": "Persist only graph-raw.json",
                        "status": "agreed",
                        "source_refs": ["src1"],
                        "note": "Readable graph is derived only at review time.",
                    },
                },
                {
                    "ts": "2026-04-05T10:06:00Z",
                    "actor_id": "elango",
                    "op": "edge_added",
                    "target": {"id": "e1", "kind": "relation"},
                    "payload": {
                        "from": "n1",
                        "to": "n2",
                        "relation": "led_to",
                        "label": "led to",
                        "source_refs": ["src1"],
                    },
                },
            ],
        }
        (sample / "graph-raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

        env = {"HOME": str(home)}

        ensure_out = run(
            ["python3", "scripts/meeting_state.py", "ensure", "sample-repo", "main", "2026-04-05"],
            cwd=ROOT,
            env=env,
        )
        ensure_json = json.loads(ensure_out)
        assert ensure_json["graph_raw_file"].endswith("graph-raw.json")

        append_out = run(
            [
                "python3",
                "scripts/graph_state.py",
                "append-raw",
                "sample-repo",
                "main",
                json.dumps(
                    {
                        "ts": "2026-04-05T11:00:00Z",
                        "actor_id": "user",
                        "op": "question_missing",
                        "target": {"id": "n3", "kind": "missing-question"},
                        "payload": {"label": "What should the raw schema capture?", "status": "open"},
                    }
                ),
            ],
            cwd=ROOT,
            env=env,
        )
        append_json = json.loads(append_out)
        assert append_json["events_count"] >= 1

        url = run(
            [
                "python3",
                "scripts/md_to_html.py",
                str(note),
                "https://m-agentic-skills.github.io/huddle/index.html",
            ],
            cwd=ROOT,
        )
        bundle = decode_hash(url)
        assert bundle["source"] == "2026-04-05.md"
        assert "markdown" in bundle
        assert "raw" in bundle
        assert bundle["raw"]["session_id"] == "2026-04-05-main"

        print("e2e ok")
        return 0
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
