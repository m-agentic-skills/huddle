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


SAMPLE_STATE = {
    "reponame": "huddle",
    "branch": "main",
    "last_huddle_date": "2026-04-05",
    "current_topic": "Should we simplify Elango's state model?",
    "open_questions": ["How does LLM generate graph view reliably?"],
    "action_items": ["Update elango-specwriter.md"],
    "latest_summary": "Decided to drop graph-raw.json in favour of huddle-state.json",
    "active_personas": ["suren", "babu"],
    "decisions": [
        {
            "id": "d-1",
            "topic": "Simplify Elango state model",
            "status": "closed",
            "decision": "Drop graph-raw.json, derive graph from huddle-state.json",
            "rationale": "Simpler state means Elango reliably captures decisions every round",
            "rejected_paths": ["Keep graph-raw.json as always-on"],
            "personas_involved": [
                {"id": "suren", "name": "Suren", "icon": "🏛️", "meta": "Architect"},
                {"id": "babu", "name": "Babu", "icon": "🎯", "meta": "Demand Reality"},
            ],
            "linked_topics": ["d-2"],
            "evidence": [
                {
                    "ref": "https://github.com/m-agentic-skills/huddle/tree/main",
                    "label": "",
                    "note": "Source branch for this discussion",
                }
            ],
        },
        {
            "id": "d-2",
            "topic": "Evidence tracking",
            "status": "open",
            "decision": "",
            "rationale": "",
            "rejected_paths": [],
            "personas_involved": [],
            "linked_topics": [],
            "evidence": [
                {
                    "ref": "https://github.com/m-agentic-skills/huddle/issues/12",
                    "label": "",
                    "note": "Related issue on evidence schema",
                }
            ],
        },
    ],
    "participants": [
        {"id": "suren", "name": "Suren", "icon": "🏛️", "meta": "Architect", "influence": "Proposed read-before-write rule"},
        {"id": "babu", "name": "Babu", "icon": "🎯", "meta": "Demand Reality", "influence": "Flagged event schema complexity"},
    ],
    "key_moments": [
        {"id": "m-1", "icon": "💬", "title": "graph-raw.json complexity raised", "detail": "Event schema too rigid for LLM"},
        {"id": "m-2", "icon": "✅", "title": "Decision: derive graph from huddle-state.json", "detail": "index.html handles derivation client-side"},
    ],
}


def test_meeting_state_ensure(env: dict) -> None:
    out = run(
        ["python3", "scripts/meeting_state.py", "ensure", "sample-repo", "main", "2026-04-05"],
        cwd=ROOT,
        env=env,
    )
    result = json.loads(out)

    assert "huddle_state_file" in result, "missing huddle_state_file"
    assert "huddle_note_file" in result, "missing huddle_note_file"
    assert "graph_raw_file" not in result, "graph_raw_file should not appear"

    state = json.loads(Path(result["huddle_state_file"]).read_text())
    assert state["decisions"] == [], "decisions should start empty"
    assert state["participants"] == [], "participants should start empty"
    assert state["key_moments"] == [], "key_moments should start empty"

    assert not (Path(result["huddle_state_file"]).parent / "graph-raw.json").exists(), \
        "graph-raw.json should not be created"

    print("  [ok] meeting_state ensure — schema correct, no graph-raw.json")


def test_md_to_html(sample: Path) -> None:
    note = sample / "2026-04-05.md"
    note.write_text("# Huddle\n\n## Topics Discussed\n\nElango state simplification.\n", encoding="utf-8")

    state_path = sample / "huddle-state.json"
    state_path.write_text(json.dumps(SAMPLE_STATE, ensure_ascii=False), encoding="utf-8")

    url = run(
        [
            "python3", "scripts/md_to_html.py", str(note),
            "https://m-agentic-skills.github.io/huddle/index.html",
        ],
        cwd=ROOT,
    )

    assert "#" in url, "URL missing hash fragment"

    bundle = decode_hash(url)
    assert bundle["source"] == "2026-04-05.md", f"wrong source: {bundle['source']}"
    assert "markdown" in bundle, "bundle missing markdown"
    assert "state" in bundle, "bundle missing state"
    assert "view" not in bundle, "bundle should not contain pre-derived view"
    assert "raw" not in bundle, "bundle should not contain raw"

    state = bundle["state"]
    assert len(state["decisions"]) == 2, f"expected 2 decisions, got {len(state['decisions'])}"
    assert state["decisions"][0]["id"] == "d-1"
    assert state["decisions"][0]["status"] == "closed"
    assert state["decisions"][1]["id"] == "d-2"
    assert state["decisions"][1]["status"] == "open"

    d1_evidence = state["decisions"][0]["evidence"]
    assert len(d1_evidence) == 1, f"expected 1 evidence on d-1, got {len(d1_evidence)}"
    assert "github.com" in d1_evidence[0]["ref"], "d-1 evidence ref wrong"

    d2_evidence = state["decisions"][1]["evidence"]
    assert len(d2_evidence) == 1, f"expected 1 evidence on d-2, got {len(d2_evidence)}"
    assert "issues/12" in d2_evidence[0]["ref"], "d-2 evidence ref wrong"

    assert len(state["participants"]) == 2
    assert state["participants"][0]["id"] == "suren"
    assert state["participants"][1]["id"] == "babu"

    assert len(state["key_moments"]) == 2
    assert state["key_moments"][0]["id"] == "m-1"
    assert state["key_moments"][1]["id"] == "m-2"

    print("  [ok] md_to_html — state bundle correct, evidence in decisions, no raw/view")


def test_graph_state_py_removed() -> None:
    assert not (ROOT / "scripts" / "graph_state.py").exists(), "graph_state.py still exists"
    print("  [ok] graph_state.py removed")


def test_bundle_context(home: Path) -> None:
    repo_root = home / ".config" / "muthuishere-agent-skills" / "demo"
    (repo_root / "main" / "huddle").mkdir(parents=True, exist_ok=True)
    (repo_root / "feature-x" / "huddle").mkdir(parents=True, exist_ok=True)
    (repo_root / "main" / "huddle" / "2026-04-10.md").write_text(
        "# Huddle\n\n## Latest Summary\nAgreed to move config path.\n",
        encoding="utf-8",
    )
    (repo_root / "feature-x" / "huddle" / "2026-04-15.md").write_text(
        "# Huddle\n\n## Latest Summary\nSketched bundle script.\n",
        encoding="utf-8",
    )

    out = run(
        ["python3", "scripts/bundle_context.py", "demo", "current-branch"],
        cwd=ROOT,
        env={"HOME": str(home)},
    )
    bundle = json.loads(out)
    assert "<persona-roster" in bundle["persona_roster_xml"], "roster xml missing"
    branches = [e["branch"] for e in bundle["cross_branch_context"]]
    assert branches == ["main", "feature-x"], f"bad branch order: {branches}"
    assert bundle["cross_branch_context"][0]["summary"] == "Agreed to move config path.", \
        "main summary not captured"
    print("  [ok] bundle_context — roster + cross-branch sorted with priority")


def test_migrate_legacy_config(home: Path) -> None:
    old_root = home / "config" / "muthuishere-agent-skills" / "oldrepo" / "main" / "huddle"
    old_root.mkdir(parents=True, exist_ok=True)
    (old_root / "2026-01-01.md").write_text("legacy note", encoding="utf-8")
    (home / "config" / "muthuishere-agent-skills" / "oldrepo" / "config.json").write_text(
        '{"reponame":"oldrepo"}', encoding="utf-8"
    )

    run(["python3", "scripts/migrate.py"], cwd=ROOT, env={"HOME": str(home)})

    new_root = home / ".config" / "muthuishere-agent-skills" / "oldrepo"
    assert (new_root / "config.json").exists(), "config.json not moved"
    assert (new_root / "main" / "huddle" / "2026-01-01.md").exists(), "legacy note not moved"
    assert not (home / "config" / "muthuishere-agent-skills").exists(), \
        "legacy muthuishere-agent-skills dir should be cleaned up"

    run(["python3", "scripts/migrate.py"], cwd=ROOT, env={"HOME": str(home)})
    print("  [ok] migrate.py — legacy ~/config moved to ~/.config, idempotent")


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp(prefix="huddle-e2e-"))
    home = tmp_root / "home"
    sample = tmp_root / "sample"
    home.mkdir(parents=True, exist_ok=True)
    sample.mkdir(parents=True, exist_ok=True)

    env = {"HOME": str(home)}

    migrate_home = tmp_root / "migrate-home"
    migrate_home.mkdir(parents=True, exist_ok=True)
    bundle_home = tmp_root / "bundle-home"
    bundle_home.mkdir(parents=True, exist_ok=True)

    try:
        print("Running e2e tests...")
        test_meeting_state_ensure(env)
        test_md_to_html(sample)
        test_graph_state_py_removed()
        test_bundle_context(bundle_home)
        test_migrate_legacy_config(migrate_home)
        print("\ne2e ok")
        return 0
    except AssertionError as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
