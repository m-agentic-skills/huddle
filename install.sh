#!/bin/sh

SKILL_NAME="huddle"
SKILL_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

HOME_DIR="${HOME:-$(cd ~ && pwd)}"

install_to() {
  target="$1"
  label="$2"
  dest="$HOME_DIR/$target/$SKILL_NAME"

  mkdir -p "$HOME_DIR/$target"

  if [ -L "$dest" ]; then
    rm "$dest"
  elif [ -e "$dest" ]; then
    echo "  $label -> $dest already exists and is not a symlink, skipping"
    return
  fi

  ln -s "$SKILL_DIR" "$dest"
  echo "  $label -> $dest"
}

echo ""
echo "Installing $SKILL_NAME..."
echo ""

installed=0

if command -v claude >/dev/null 2>&1; then
  install_to ".claude/skills" "Claude Code"
  installed=$((installed + 1))
fi

if command -v codex >/dev/null 2>&1; then
  install_to ".agents/skills" "Agent Skills"
  installed=$((installed + 1))
fi

if [ "$installed" -eq 0 ]; then
  echo "No supported agent CLI detected (claude, codex)."
  echo "Installing for Claude Code by default."
  install_to ".claude/skills" "Claude Code"
fi

echo ""
echo "Done. Restart your agent session to pick up the new skill."
