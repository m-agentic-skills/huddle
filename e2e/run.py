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


def test_global_state(home: Path) -> None:
    out = run(["python3", "scripts/global_state.py"], cwd=ROOT, env={"HOME": str(home)})
    first = json.loads(out)
    assert first["python_bin"], "python_bin not detected"
    assert first["git_user"], "git_user not resolved"
    assert "gh_available" in first, "gh_available missing"
    assert "<persona-roster" in first["persona_roster_xml"], "persona roster missing"

    uc = home / ".config" / "muthuishere-agent-skills" / "userconfig.json"
    assert uc.exists(), "userconfig.json not written"
    cached = json.loads(uc.read_text())
    assert cached["python_bin"] == first["python_bin"], "python_bin not cached"
    assert cached["git_user"] == first["git_user"], "git_user not cached"

    uc.write_text(json.dumps({**cached, "git_user": "Sentinel"}), encoding="utf-8")
    out2 = run(["python3", "scripts/global_state.py"], cwd=ROOT, env={"HOME": str(home)})
    second = json.loads(out2)
    assert second["git_user"] == "Sentinel", "cached git_user not honored on second call"

    print("  [ok] global_state — detects, caches, honors cache on repeat")


def test_project_state_snapshot(home: Path, tmp: Path) -> None:
    project = tmp / "sample-proj"
    project.mkdir(parents=True, exist_ok=True)
    (project / "README.md").write_text("hi", encoding="utf-8")
    for i in range(25):
        (project / f"f{i}.txt").write_text("x", encoding="utf-8")

    repo_root = home / ".config" / "muthuishere-agent-skills" / "sample-proj"
    (repo_root / "main" / "huddle" / "raw").mkdir(parents=True, exist_ok=True)
    (repo_root / "main" / "huddle" / "raw" / "20260401T000000_decision.json").write_text(
        json.dumps({"kind": "decision", "ts": "2026-04-01T00:00:00Z"}),
        encoding="utf-8",
    )
    (repo_root / "feature-x" / "huddle").mkdir(parents=True, exist_ok=True)
    (repo_root / "feature-x" / "huddle" / "2026-04-15.md").write_text(
        "# Huddle\n\n## Latest Summary\nSketched new script.\n",
        encoding="utf-8",
    )

    out = run(
        ["python3", "scripts/project_state.py", "snapshot", str(project)],
        cwd=ROOT,
        env={"HOME": str(home)},
    )
    snap = json.loads(out)
    assert snap["reponame"] == "sample-proj", f"wrong reponame: {snap['reponame']}"
    assert "huddle_state_file" in snap, "missing huddle_state_file"
    assert snap["project_scan"]["scan"] is False, "no git repo → scan should be False"
    assert snap["saved_state"]["decisions"] == [], "saved_state should default empty"
    raw = snap["raw_events"]
    assert len(raw) == 1 and raw[0]["kind"] == "decision", f"raw_events wrong: {raw}"
    branches = [e["branch"] for e in snap["cross_branch_context"]]
    assert branches == ["feature-x"], f"unexpected cross-branch list: {branches}"
    assert snap["project_docs_found"] == [], "no docs were added, list should be empty"
    print("  [ok] project_state snapshot — identity, raw events, cross-branch, saved_state")


def test_project_state_doc_detection(home: Path, tmp: Path) -> None:
    bare = tmp / "bare-proj"
    bare.mkdir(parents=True, exist_ok=True)
    for i in range(25):
        (bare / f"src{i}.py").write_text("pass\n", encoding="utf-8")
    out = run(
        ["python3", "scripts/project_state.py", "snapshot", str(bare)],
        cwd=ROOT, env={"HOME": str(home)},
    )
    snap = json.loads(out)
    assert snap["project_docs_found"] == [], f"bare repo should have no docs: {snap['project_docs_found']}"

    documented = tmp / "documented-proj"
    documented.mkdir(parents=True, exist_ok=True)
    for i in range(25):
        (documented / f"src{i}.py").write_text("pass\n", encoding="utf-8")
    (documented / "README.md").write_text("# Project\n\n" + ("Real content. " * 50), encoding="utf-8")
    (documented / "CLAUDE.md").write_text("# Guide\n\n" + ("More context. " * 50), encoding="utf-8")
    (documented / "docs").mkdir()
    (documented / "docs" / "overview.md").write_text("# Overview\n\n" + ("Details. " * 50), encoding="utf-8")

    out = run(
        ["python3", "scripts/project_state.py", "snapshot", str(documented)],
        cwd=ROOT, env={"HOME": str(home)},
    )
    snap = json.loads(out)
    found = set(snap["project_docs_found"])
    assert "README.md" in found, f"README.md not detected: {found}"
    assert "CLAUDE.md" in found, f"CLAUDE.md not detected: {found}"
    assert any(p.startswith("docs/") for p in found), f"docs/*.md not detected: {found}"
    assert snap["project_doc_missing"] is False, \
        "project_doc_missing should flip false once real docs are present"

    tiny = tmp / "tiny-readme-proj"
    tiny.mkdir(parents=True, exist_ok=True)
    for i in range(25):
        (tiny / f"src{i}.py").write_text("pass\n", encoding="utf-8")
    (tiny / "README.md").write_text("# x\n", encoding="utf-8")
    out = run(
        ["python3", "scripts/project_state.py", "snapshot", str(tiny)],
        cwd=ROOT, env={"HOME": str(home)},
    )
    snap = json.loads(out)
    assert snap["project_docs_found"] == [], \
        f"tiny README should not count as docs: {snap['project_docs_found']}"

    print("  [ok] project_state doc detection — README/CLAUDE.md/docs trigger, tiny stubs don't")


def test_session_state(home: Path, tmp: Path) -> None:
    project = tmp / "sess-proj"
    project.mkdir(parents=True, exist_ok=True)
    out = run(
        ["python3", "scripts/session_state.py", str(project), "2026-04-21"],
        cwd=ROOT,
        env={"HOME": str(home)},
    )
    sess = json.loads(out)
    assert sess["reponame"] == "sess-proj", f"wrong reponame: {sess['reponame']}"
    assert sess["is_resume"] is False, "fresh note should not be resume"
    assert sess["git_status"] == [], "expected empty git_status in non-repo dir"
    assert Path(sess["huddle_note_file"]).exists(), "note file not created"
    print("  [ok] session_state — live probes + note ensured")


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
    home_global = tmp_root / "home-global"
    home_project = tmp_root / "home-project"
    home_session = tmp_root / "home-session"
    migrate_home = tmp_root / "migrate-home"
    sample = tmp_root / "sample"
    tmp_projects = tmp_root / "projects"
    for p in (home_global, home_project, home_session, migrate_home, sample, tmp_projects):
        p.mkdir(parents=True, exist_ok=True)

    try:
        print("Running e2e tests...")
        test_global_state(home_global)
        test_project_state_snapshot(home_project, tmp_projects)
        test_project_state_doc_detection(home_project, tmp_projects)
        test_session_state(home_session, tmp_projects)
        test_md_to_html(sample)
        test_graph_state_py_removed()
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
