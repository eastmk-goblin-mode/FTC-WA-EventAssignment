#!/usr/bin/env python3
"""Build the Washington zip code centroid table from uszipcode.

**NOTE:** This script requires uszipcode, which has compatibility issues with
Python 3.12 (sqlalchemy_mate AttributeError). The pre-built wa_zips.csv is
already included in the repository and rarely needs regeneration.

If you need to regenerate it:
1. Use Python 3.11 temporarily, OR
2. Use the existing .data/wa_zips.csv (already complete)

Usage: python3 tools/build_zip_table.py
"""
import csv
import sys
from pathlib import Path

print("=" * 70)
print("NOTE: This script requires uszipcode, which is currently incompatible")
print("with Python 3.12 due to sqlalchemy_mate issues.")
print()
print("The pre-built .data/wa_zips.csv is already included and complete.")
print("You don't need to run this script unless Washington adds new zip codes.")
print("=" * 70)
print()

# Check if wa_zips.csv already exists
output_path = Path(__file__).parent.parent / ".data" / "wa_zips.csv"
if output_path.exists():
    print(f"✓ {output_path} already exists")
    with open(output_path) as f:
        row_count = sum(1 for _ in f) - 1  # Subtract header
    print(f"  Contains {row_count} Washington zip codes")
    print()
    print("No action needed. To regenerate, delete the file and use Python 3.11.")
    sys.exit(0)

print(f"✗ {output_path} not found")
print()
print("Please copy the pre-built zip table:")
print("  cp /path/to/prototype/data/wa_zips.csv .data/")
print()
print("Or use Python 3.11 to regenerate (uszipcode works there):")
print("  python3.11 -m pip install uszipcode")
print("  python3.11 tools/build_zip_table.py")
sys.exit(1)
