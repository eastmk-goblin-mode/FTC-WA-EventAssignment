#!/usr/bin/env bash
# Basic setup: create .data/ and copy the Washington zip table.
# This runs automatically on fresh Codespaces (devcontainer postCreateCommand).
# For drive-time mode, run tools/enable_drive_times.sh after this.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "=== Setting up team sorter ==="

# Create .data directory
mkdir -p .data

# Copy reference zip table to .data/
if [ -f reference/wa_zips.csv ]; then
    cp reference/wa_zips.csv .data/wa_zips.csv
    ZIP_COUNT=$(tail -n +2 .data/wa_zips.csv | wc -l | tr -d ' ')
    echo "✓ Copied Washington zip table: ${ZIP_COUNT} zip codes"
else
    echo "✗ reference/wa_zips.csv not found in repository"
    echo ""
    echo "This reference file should be committed to git."
    echo "Something is wrong with the repository checkout."
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
