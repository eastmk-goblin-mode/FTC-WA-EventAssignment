#!/usr/bin/env bash
# Basic setup: create .data/ and build the Washington zip table.
# This runs automatically on fresh Codespaces (devcontainer postCreateCommand).
# For drive-time mode, run tools/enable_drive_times.sh after this.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "=== Setting up team sorter ==="

# Create .data directory
mkdir -p .data

# Build zip table
echo "Building Washington zip table..."
if ! python3 tools/build_zip_table.py; then
    echo "Error: Failed to build zip table" >&2
    echo "Make sure uszipcode is installed: pip install uszipcode" >&2
    exit 1
fi

echo ""
echo "✓ Setup complete! The sorter is ready in straight-line mode."
echo ""
echo "Quick start:"
echo "  python3 -m sorter.cli --teams .data/teams.csv --events .data/events.csv"
echo ""
echo "To enable drive-time mode (optional, requires OSRM):"
echo "  bash tools/enable_drive_times.sh"
