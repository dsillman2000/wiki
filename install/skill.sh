#!/bin/bash

# Wikipedia CLI skill installer
# Installs Wikipedia skill for various AI agents

set -e

REPO="dsillman2000/wiki-client"
SKILL_PATH="skills/wikipedia/SKILL.md"
BASE_URL="https://raw.githubusercontent.com/$REPO"
AGENT=""

# Agent directory mappings
declare -A AGENT_DIRS=(
  ["opencode"]="$HOME/.opencode/skills/wikipedia"
  ["copilot"]="$HOME/.copilot/skills/wikipedia"
  ["claude"]="$HOME/.claude/skills/wikipedia"
  ["codex"]="$HOME/.codex/skills/wikipedia"
  ["windsurf"]="$HOME/.codeium/windsurf/skills/wikipedia"
  ["aider"]="$HOME/.agents/skills/wikipedia"
  ["cursor"]="$HOME/.cursor/skills/wikipedia"
)

# Agent display names
declare -A AGENT_NAMES=(
  ["opencode"]="OpenCode"
  ["copilot"]="GitHub Copilot"
  ["claude"]="Claude"
  ["codex"]="Codex"
  ["windsurf"]="Windsurf (Codeium)"
  ["aider"]="Aider"
  ["cursor"]="Cursor"
)

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -a|--agent)
      AGENT="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [-a AGENT]"
      echo "Install Wikipedia skill for AI agents"
      echo ""
      echo "Options:"
      echo "  -a, --agent AGENT     Agent to install for (required)"
      echo "  -h, --help            Show this help message"
      echo ""
      echo "Available agents:"
      echo "  opencode    - OpenCode"
      echo "  copilot     - GitHub Copilot"
      echo "  claude      - Claude"
      echo "  codex       - Codex"
      echo "  windsurf    - Windsurf (Codeium)"
      echo "  aider       - Aider"
      echo "  cursor      - Cursor"
      echo ""
      echo "Examples:"
      echo "  $0 -a opencode          # Install for OpenCode"
      echo "  $0 -a copilot           # Install for Copilot"
      echo ""
      echo "Remote installation:"
      echo "  curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki-client/main/install/skill.sh | sh -s -- -a opencode"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h for help"
      exit 1
      ;;
  esac
done

# Validate agent
if [[ -z "$AGENT" ]]; then
  echo "Error: Agent must be specified with -a or --agent"
  echo "Use -h for help"
  exit 1
fi

if [[ -z "${AGENT_DIRS[$AGENT]}" ]]; then
  echo "Error: Unknown agent '$AGENT'"
  echo "Available agents: opencode, copilot, claude, codex, windsurf, aider, cursor"
  exit 1
fi

TARGET_DIR="${AGENT_DIRS[$AGENT]}"
AGENT_NAME="${AGENT_NAMES[$AGENT]}"

echo "Installing Wikipedia skill for $AGENT_NAME..."
echo "Repository: $REPO"
echo "Target: $TARGET_DIR"

# Create target directory
mkdir -p "$TARGET_DIR"

# Download the skill file (always latest version)
SKILL_URL="$BASE_URL/main/$SKILL_PATH"
echo "Downloading from: $SKILL_URL"

if curl -s -f -L "$SKILL_URL" -o "$TARGET_DIR/SKILL.md"; then
  echo "✓ Skill installed successfully to $TARGET_DIR/SKILL.md"
  
  # Display skill information
  echo ""
  echo "Skill Information:"
  echo "------------------"
  if head -20 "$TARGET_DIR/SKILL.md" | grep -E "^#|^---" > /dev/null; then
    # Extract frontmatter if present
    if grep -q "^---" "$TARGET_DIR/SKILL.md"; then
      echo "Frontmatter found:"
      sed -n '/^---/,/^---/p' "$TARGET_DIR/SKILL.md" | head -20
    fi
  fi
  
  echo ""
  echo "To use this skill in $AGENT_NAME:"
  echo "1. The skill should be automatically detected"
  echo "2. Reference it as 'wikipedia' skill in your prompts"
  echo "3. Check $(dirname "$TARGET_DIR")/ for other installed skills"
else
  echo "✗ Failed to download skill file"
  echo "Check that:"
  echo "1. The repository exists: https://github.com/$REPO"
  echo "2. The file exists: $SKILL_PATH"
  exit 1
fi