#!/usr/bin/env python3

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


SKILL_NAME = "team-meeting"


@dataclass(frozen=True)
class UninstallTarget:
    label: str
    relative_dir: str

    def target(self, home_dir: Path) -> Path:
        return home_dir / self.relative_dir / SKILL_NAME


TARGETS = (
    UninstallTarget("Agent Skills", ".agents/skills"),
    UninstallTarget("Claude Code", ".claude/skills"),
)


def home_dir() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("USERPROFILE", str(Path.home())))
    return Path(os.environ.get("HOME", str(Path.home())))


def main() -> int:
    home = home_dir()
    found = False

    print()
    print(f"Uninstalling {SKILL_NAME}...")
    print()

    for target in TARGETS:
        destination = target.target(home)
        if destination.is_dir():
            shutil.rmtree(destination)
            print(f"  Removed {target.label} -> {destination}")
            found = True
        else:
            print(f"  {target.label} -> not installed, skipping")

    print()
    if not found:
        print("Nothing to uninstall.")
    else:
        print(f"Done. {SKILL_NAME} removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
