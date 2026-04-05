#!/bin/sh

SKILL_NAME="huddle"
HOME_DIR="${HOME:-$(cd ~ && pwd)}"

TARGETS="
.claude/skills:Claude Code
.agents/skills:Agent Skills
"

echo ""
echo "Uninstalling $SKILL_NAME..."
echo ""

found=0

echo "$TARGETS" | grep -v '^$' | while IFS=: read -r rel_dir label; do
  dest="$HOME_DIR/$rel_dir/$SKILL_NAME"
  if [ -L "$dest" ]; then
    rm "$dest"
    echo "  Removed $label -> $dest"
    found=$((found + 1))
  elif [ -e "$dest" ]; then
    echo "  $label -> $dest is not a symlink, skipping"
  else
    echo "  $label -> not installed, skipping"
  fi
done

echo ""
echo "Done."
