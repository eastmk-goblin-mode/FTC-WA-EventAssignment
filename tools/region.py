#!/usr/bin/env python3
"""The configured region: the STATES list in region.env, shared by every setup tool.

Shell scripts call it to get the same answer the Python tools use:
  python3 tools/region.py states   ->  WA,OR
  python3 tools/region.py tag      ->  or-wa         (names the OSRM build and container)
  python3 tools/region.py urls     ->  one Geofabrik extract URL per state, one per line
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGION_FILE = ROOT / "region.env"
GEOFABRIK = "https://download.geofabrik.de/north-america/us/{}-latest.osm.pbf"

# Geofabrik's file name for each state. All 51 were checked to resolve on 2026-10-15.
GEOFABRIK_NAMES = {
    "AL": "alabama", "AK": "alaska", "AZ": "arizona", "AR": "arkansas", "CA": "california",
    "CO": "colorado", "CT": "connecticut", "DE": "delaware", "DC": "district-of-columbia",
    "FL": "florida", "GA": "georgia", "HI": "hawaii", "ID": "idaho", "IL": "illinois",
    "IN": "indiana", "IA": "iowa", "KS": "kansas", "KY": "kentucky", "LA": "louisiana",
    "ME": "maine", "MD": "maryland", "MA": "massachusetts", "MI": "michigan", "MN": "minnesota",
    "MS": "mississippi", "MO": "missouri", "MT": "montana", "NE": "nebraska", "NV": "nevada",
    "NH": "new-hampshire", "NJ": "new-jersey", "NM": "new-mexico", "NY": "new-york",
    "NC": "north-carolina", "ND": "north-dakota", "OH": "ohio", "OK": "oklahoma", "OR": "oregon",
    "PA": "pennsylvania", "RI": "rhode-island", "SC": "south-carolina", "SD": "south-dakota",
    "TN": "tennessee", "TX": "texas", "UT": "utah", "VT": "vermont", "VA": "virginia",
    "WA": "washington", "WV": "west-virginia", "WI": "wisconsin", "WY": "wyoming",
}


def parse_states(text):
    states = [s.strip().upper() for s in text.split(",") if s.strip()]
    bad = [s for s in states if s not in GEOFABRIK_NAMES]
    if not states or bad:
        raise SystemExit(f"States must be comma-separated USPS codes like WA,OR (got {text!r})")
    return states


def region_states(path=REGION_FILE):
    for line in path.read_text().splitlines():
        if line.strip().startswith("STATES="):
            return parse_states(line.split("=", 1)[1])
    raise SystemExit(f"{path} has no STATES= line")


def tag(states):
    return "-".join(sorted(s.lower() for s in states))


def extract_urls(states):
    return [GEOFABRIK.format(GEOFABRIK_NAMES[s]) for s in states]


def main(argv):
    states = region_states()
    commands = {"states": lambda: ",".join(states), "tag": lambda: tag(states),
                "urls": lambda: "\n".join(extract_urls(states))}
    if len(argv) != 1 or argv[0] not in commands:
        sys.exit(f"usage: python3 tools/region.py {{{'|'.join(commands)}}}")
    print(commands[argv[0]]())


if __name__ == "__main__":
    main(sys.argv[1:])
