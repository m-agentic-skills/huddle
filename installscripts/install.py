#!/usr/bin/env python3

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


SKILL_NAME = "team-meeting"


@dataclass(frozen=True)
class InstallTarget:
    key: str
    label: str
    cli_names: tuple[str, ...]
    relative_dir: str

    def target(self, home_dir: Path) -> Path:
        return home_dir / self.relative_dir / SKILL_NAME

    def detected(self) -> bool:
        return any(shutil.which(name) for name in self.cli_names)


TARGETS = (
    InstallTarget("agents", "Agent Skills", ("codex",), ".agents/skills"),
    InstallTarget("claude", "Claude Code", ("claude",), ".claude/skills"),
)


def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def home_dir() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("USERPROFILE", str(Path.home())))
    return Path(os.environ.get("HOME", str(Path.home())))


def detected_targets() -> list[InstallTarget]:
    found = [t for t in TARGETS if t.detected()]
    return found if found else [TARGETS[0]]


def install_target(target: InstallTarget, home: Path) -> None:
    destination = target.target(home)
    if destination.is_dir():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        skill_dir(),
        destination,
        ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "installscripts", "*.cmd", "*.sh"),
    )
    print(f"  {target.label} -> {destination}")


def main() -> int:
    home = home_dir()
    targets = detected_targets()

    print()
    print(f"Installing {SKILL_NAME}...")
    print()
    print("Detected install targets:")
    for t in TARGETS:
        detected = "yes" if t in targets else "no"
        existing = "already installed" if t.target(home).is_dir() else "not installed"
        print(f"  {t.label}: detected={detected}, current={existing}")

    print()
    for target in targets:
        install_target(target, home)

    print()
    print(f"Done. {SKILL_NAME} installed to {len(targets)} location(s).")
    print("Restart your agent session to pick up the new skill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
