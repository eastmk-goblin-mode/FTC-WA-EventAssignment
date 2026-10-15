#!/usr/bin/env python3
"""Build the Washington zip code centroid table from uszipcode.

Writes .data/wa_zips.csv with columns: zip, lat, lon, city, county, type.
Only standard zip types are included (excludes PO boxes, military bases).

Usage: python3 tools/build_zip_table.py
"""
import csv
import sys
from pathlib import Path

try:
    from uszipcode import SearchEngine
except ImportError:
    print("Error: uszipcode package not found", file=sys.stderr)
    print("Install it with: pip install uszipcode", file=sys.stderr)
    sys.exit(1)


def main():
    """Build Washington zip table."""
    output_path = Path(__file__).parent.parent / ".data" / "wa_zips.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Loading Washington zip codes from uszipcode database...")
    search = SearchEngine()
    
    # Query all Washington zips
    zips = search.by_state("WA", returns=None)
    
    # Filter to standard zip codes only
    standard_zips = []
    for z in zips:
        if z.zipcode and z.lat and z.lng and z.zipcode_type in ("Standard", "PO Box"):
            # Include PO Box types if they have coordinates (some rural areas)
            if z.zipcode_type == "Standard" or (z.zipcode_type == "PO Box" and z.lat and z.lng):
                standard_zips.append({
                    "zip": z.zipcode,
                    "lat": z.lat,
                    "lon": z.lng,
                    "city": z.major_city or "",
                    "county": z.county or "",
                    "type": z.zipcode_type
                })
    
    print(f"Found {len(standard_zips)} Washington zip codes with coordinates")
    
    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["zip", "lat", "lon", "city", "county", "type"])
        writer.writeheader()
        writer.writerows(sorted(standard_zips, key=lambda x: x["zip"]))
    
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
