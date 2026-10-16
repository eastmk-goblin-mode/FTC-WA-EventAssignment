#!/usr/bin/env python3
"""Build the zip centroid tables for the states in region.env.

Reads the uszipcode project's public zip database (US Census / USPS centroids,
MIT-licensed) with the standard-library sqlite3 module. The uszipcode Python
package itself is not used: its sqlalchemy_mate dependency breaks on Python 3.12.

Writes:
  .data/zips.csv        zip,lat,lon,city,county,state,type for the configured states
  .data/zip_states.csv  zip,state for every US zip, so the sorter can tell a zip in
                        an unconfigured state (add it to region.env) from a zip that
                        does not exist (likely a typo)

The 10.7 MB database is downloaded once to ~/.cache/uszipcode/ and checked
against a pinned SHA-256.

Usage: python3 tools/build_zip_table.py [--states WA,OR] [--db PATH]
"""
import argparse
import csv
import hashlib
import sqlite3
import sys
import urllib.request
from pathlib import Path

if __package__:
    from .region import parse_states, region_states
else:
    from region import parse_states, region_states

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / ".data"
DB_URL = "https://github.com/MacHu-GWU/uszipcode-project/releases/download/1.0.1.db/simple_db.sqlite"
DB_SHA256 = "43383f108ef14dccd925107bc77705f622b1014111ad5c9e5e2a6837bb7f64ff"
DB_CACHE = Path.home() / ".cache" / "uszipcode" / "simple_db.sqlite"
COLS = ["zip", "lat", "lon", "city", "county", "state", "type"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch_db(dest=DB_CACHE):
    if dest.exists() and sha256(dest) == DB_SHA256:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    print(f"Downloading the zip database (10.7 MB) from {DB_URL} ...")
    urllib.request.urlretrieve(DB_URL, tmp)
    if sha256(tmp) != DB_SHA256:
        tmp.unlink()
        raise SystemExit("Downloaded zip database failed its SHA-256 check; not using it.")
    tmp.replace(dest)
    return dest


def export(db_path, states, out_dir=DATA_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        marks = ",".join("?" * len(states))
        rows = con.execute(
            f"SELECT zipcode, lat, lng, major_city, county, state, zipcode_type FROM simple_zipcode "
            f"WHERE state IN ({marks}) AND lat IS NOT NULL AND lng IS NOT NULL ORDER BY zipcode",
            states).fetchall()
        everywhere = con.execute(
            "SELECT zipcode, state FROM simple_zipcode WHERE state IS NOT NULL ORDER BY zipcode").fetchall()
    finally:
        con.close()

    found = {r[5] for r in rows}
    missing = [s for s in states if s not in found]
    if missing:
        raise SystemExit(f"No zips found for {', '.join(missing)}. Check region.env.")

    with open(out_dir / "zips.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerows(rows)
    with open(out_dir / "zip_states.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["zip", "state"])
        w.writerows(everywhere)
    counts = {s: sum(1 for r in rows if r[5] == s) for s in states}
    return counts


def main():
    ap = argparse.ArgumentParser(description="Build .data/zips.csv for the states in region.env")
    ap.add_argument("--states", help="Comma-separated USPS codes (default: STATES in region.env)")
    ap.add_argument("--db", type=Path, help="Use a local copy of simple_db.sqlite instead of downloading")
    a = ap.parse_args()
    states = parse_states(a.states) if a.states else region_states()
    try:
        db = a.db or fetch_db()
    except OSError as e:
        sys.exit(f"Could not download the zip database: {e}")
    counts = export(db, states)
    detail = ", ".join(f"{s} {n}" for s, n in counts.items())
    print(f"Wrote .data/zips.csv: {sum(counts.values())} zips ({detail}).")


if __name__ == "__main__":
    main()
