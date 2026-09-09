#!/usr/bin/env sh
# ArchHarness installer (POSIX / macOS / Linux)
#   ./install.sh               # install package + verify
#   ./install.sh --skip-install  # already installed: just verify
set -e

if [ "${1:-}" = "--skip-install" ]; then
  SKIP_INSTALL=1
else
  SKIP_INSTALL=0
fi

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ "$SKIP_INSTALL" = "0" ]; then
  echo "Installing ArchHarness Python package (editable) ..."
  python -m pip install -e .
fi

if [ ! -f ".archharness/workspace.yaml" ]; then
  python -m archharness init-workspace .
fi

python -m archharness doctor

echo
echo "Next steps:"
echo "  1. Edit config.yaml (company name, DC names, platform names)."
echo "  2. Create a project:  python -m archharness init-project <id> --default"
echo "  3. Open your AI tool in this directory (claude . | opencode . | codex)."
echo "  4. Tools are reachable anywhere via:"
echo "       archharness diagram -i arch.yaml"
echo "       archharness req --doc brief.md"
echo "       archharness validate-yaml standards/*.yaml config.yaml"
