"""Command-line interface for team sorting with map output."""
import argparse
import csv
import math
import sys
from collections import Counter
from pathlib import Path

from . import geo, assign, review


def load_events(path):
    """Load events from CSV: code, zip, capacity."""
    events = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0]:  # Skip empty rows and header if present
                events.append({
                    "code": row[0],
                    "zip": row[1],
                    "cap": int(row[2])
                })
    return events


def load_teams(path):
    """Load teams from CSV: number, name, zip, [optional_host_team]."""
    teams = []
    team_names = {}
    team_host = {}
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                teams.append({
                    "num": row[0],
                    "zip": row[2]
                })
                if len(row) > 1:
                    team_names[row[0]] = row[1]
                if len(row) > 3:
                    team_host[row[0]] = row[3]
    return teams, team_names, team_host


def load_pre_assignments(path):
    """Load pre-assignments from CSV: event_code, team_number[, notes].
    
    Returns ({team_number: event_code}, {team_number: notes}). Lines starting with # are comments.
    """
    if not path or not Path(path).exists():
        return {}, {}
    
    locks, notes = {}, {}
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0] or row[0].startswith("#"):
                continue
            if len(row) >= 2:
                event_code, team_num = row[0].strip(), row[1].strip()
                locks[team_num] = event_code
                if len(row) > 2 and row[2].strip():
                    notes[team_num] = ",".join(row[2:]).strip()
    return locks, notes


def unassigned_reason(zip_code, zips, zip_states, region, mode, missing_drive_time):
    """Why a team was left unassigned, phrased as what the operator should do next.

    missing_drive_time: in drive mode, at least one event has no drive time for this zip.
    That is checked before capacity because a complete matrix might have placed the team.
    """
    if zip_code not in zips:
        state = zip_states.get(zip_code)
        if state and state not in region:
            return f"zip is in {state}, which region.env does not include"
        return "zip code not found"
    if mode == "drive" and missing_drive_time:
        return "missing drive times; rebuild the drive matrix"
    return "no event with room"


OUTPUT_COLUMNS = [
    # Required by the map team
    "team_id", "team_name", "team_zipCode", "team_coordinates",
    "event_id", "event_zipCode", "event_coordinates", "program",
    # Sorting team columns (the map team ignores these)
    "is_host_team", "from_manual_override", "manual_override_notes",
    "drive_minutes", "drive_distance", "flagged_for_manual_review", "flagged_reason",
]


def write_map_output(output_path, teams, team_names, team_host, assignment, events, zips,
                     distance_fn, mode, program, rules, miles_fn, overrides=None, override_notes=None,
                     zip_states=None, region=()):
    """Write one row per input team, in OUTPUT_COLUMNS order.

    distance_fn is the travel cost the sorter used (drive minutes, or straight-line miles);
    miles_fn gives the distance in miles for the same route (drive miles, or straight-line).
    Returns (counts, unassigned_zips, reason_counts).
    """
    event_zips = {e["code"]: e["zip"] for e in events}
    overrides = overrides or {}
    override_notes = override_notes or {}
    zip_counts = Counter(t["zip"] for t in teams)
    unit = "drive" if mode == "drive" else "straight-line"
    counts = Counter()
    unassigned_zips = {}  # reason -> set of zips
    reason_counts = Counter()
    
    def wkt(zip_code):
        """Return WKT POINT string for a zip centroid."""
        if zip_code not in zips:
            return ""
        lat, lon = zips[zip_code][:2]
        return f"POINT ({lon} {lat})"

    def finite(value):
        return round(value, 1) if value is not None and math.isfinite(value) else None

    def blank(value):
        return "" if value is None else value

    def boolean(value):
        return "true" if value else "false"
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(OUTPUT_COLUMNS)
        
        for team in teams:
            zip_code = team["zip"]
            event_code = assignment.get(team["num"])
            reachable = [miles_fn(zip_code, e["zip"]) for e in events]
            nearest_miles = finite(min((m for m in reachable if math.isfinite(m)), default=None))
            
            if not event_code:
                event_zip = event_wkt = ""
                travel = assigned_miles = None
                missing_drive_time = any(not math.isfinite(distance_fn(zip_code, e["zip"])) for e in events)
                why = unassigned_reason(zip_code, zips, zip_states or {}, set(region), mode,
                                        missing_drive_time)
                unassigned_zips.setdefault(why, set()).add(zip_code)
                counts["unassigned"] += 1
            else:
                event_zip = event_zips[event_code]
                event_wkt = wkt(event_zip)
                travel = finite(distance_fn(zip_code, event_zip))
                assigned_miles = finite(miles_fn(zip_code, event_zip))
                why = None

            reasons = review.review_reasons(zip_counts[zip_code], assigned_miles, nearest_miles, travel,
                                            why, unit, rules)
            if event_code:
                counts["flagged" if reasons else "assigned"] += 1
            for r in reasons:
                reason_counts[r.split(" (")[0]] += 1

            writer.writerow([
                team["num"],
                team_names.get(team["num"], ""),
                zip_code,
                wkt(zip_code),
                event_code or "",
                event_zip,
                event_wkt,
                program,
                boolean(review.truthy(team_host.get(team["num"], ""))),
                boolean(team["num"] in overrides),
                override_notes.get(team["num"], ""),
                blank(travel) if mode == "drive" else "",
                blank(assigned_miles) if mode == "drive" else "",
                boolean(reasons),
                "; ".join(reasons),
            ])
    
    return counts, unassigned_zips, reason_counts


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Assign teams to events using zip-bucket greedy algorithm"
    )
    
    # Required inputs
    parser.add_argument("--teams", required=True, help="Teams CSV (number,name,zip)")
    parser.add_argument("--events", required=True, help="Events CSV (code,zip,capacity)")
    parser.add_argument("--program", required=True, choices=["FLL", "FTC", "FRC"],
                       help="Competition program (FLL, FTC, or FRC)")
    
    # Optional inputs
    parser.add_argument("--zips", 
                       help="Zip centroids CSV (default: .data/zips.csv, falls back to reference/wa_zips.csv)")
    parser.add_argument("--drive-matrix", default=".data/drive_matrix.csv",
                       help="Drive matrix CSV (default: .data/drive_matrix.csv)")
    parser.add_argument("--zip-states", default=".data/zip_states.csv",
                       help="Zip-to-state index for out-of-region flags (default: .data/zip_states.csv)")
    parser.add_argument("--pre-assignments",
                       help="Pre-assigned teams CSV (event_code,team_number)")
    
    # Output
    parser.add_argument("--out", default=".data/team_assignments.csv",
                       help="Output map CSV (default: .data/team_assignments.csv)")
    
    # Algorithm options
    parser.add_argument("--method", choices=["bump", "largest", "regret"], default="bump",
                       help="Ordering strategy (default: bump)")
    parser.add_argument("--flag-over", type=float, default=90,
                       help="Flag travel over this: drive minutes, or straight-line miles without a matrix (default: 90)")
    parser.add_argument("--flag-miles", type=float, default=40,
                       help="Flag teams whose assigned event is farther than this many miles (default: 40)")
    parser.add_argument("--flag-nearest-miles", type=float, default=75,
                       help="Flag teams whose nearest event is farther than this many miles (default: 75)")
    parser.add_argument("--small-zip", type=int, default=3,
                       help="Flag zips with this many teams or fewer (default: 3)")
    parser.add_argument("--large-zip", type=int, default=30,
                       help="Flag zips with this many teams or more (default: 30)")
    
    args = parser.parse_args()
    
    # Load data
    try:
        # Resolve zips path with fallback
        if args.zips:
            zips_path = Path(args.zips)
        else:
            # Default: the generated table, then the committed Washington-only table
            if Path(".data/zips.csv").exists():
                zips_path = Path(".data/zips.csv")
            elif Path("reference/wa_zips.csv").exists():
                zips_path = Path("reference/wa_zips.csv")
                print("Warning: .data/zips.csv not found; using reference/wa_zips.csv (Washington only). "
                      "Run setup.sh to build the table for region.env.", file=sys.stderr)
            else:
                print("Error: no zip table in .data/zips.csv or reference/wa_zips.csv. Run setup.sh first.", file=sys.stderr)
                sys.exit(2)
        
        zips = geo.load_zips(zips_path)
        zip_states = geo.load_zip_states(args.zip_states)
        region = geo.table_states(zips_path) or {"WA"}  # reference/wa_zips.csv has no state column
        events = load_events(args.events)
        teams, team_names, team_host = load_teams(args.teams)
        locks, override_notes = load_pre_assignments(args.pre_assignments)
        rules = review.Rules(small_zip=args.small_zip, large_zip=args.large_zip,
                             assigned_miles=args.flag_miles, nearest_miles=args.flag_nearest_miles,
                             travel=args.flag_over)
        
        # Determine distance function
        drive_matrix_path = Path(args.drive_matrix)
        if drive_matrix_path.exists():
            print(f"Using drive times from {args.drive_matrix}")
            drive_matrix = geo.load_drive_matrix(args.drive_matrix)
            miles_matrix = geo.load_drive_miles(args.drive_matrix)
            distance_fn = lambda a, b: geo.drive_minutes(a, b, drive_matrix)
            miles_fn = lambda a, b: geo.drive_miles(a, b, drive_matrix, miles_matrix)
            mode = "drive"
        else:
            print(f"Drive matrix not found at {args.drive_matrix}, using straight-line miles")
            distance_fn = lambda a, b: geo.miles_straight_line(a, b, zips)
            miles_fn = distance_fn
            mode = "miles"
        
        # Run assignment
        print(f"Assigning {len(teams)} teams to {len(events)} events using '{args.method}' method...")
        if locks:
            print(f"Pre-assigned {len(locks)} teams")
        
        assignment = assign.greedy(
            events=events,
            teams=teams,
            zips=zips,
            distance_fn=distance_fn,
            order=args.method,
            locks=locks
        )
        
        # Write output
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        status_count, unassigned_zips, reason_counts = write_map_output(
            output_path=args.out,
            teams=teams,
            team_names=team_names,
            team_host=team_host,
            assignment=assignment,
            events=events,
            zips=zips,
            distance_fn=distance_fn,
            mode=mode,
            program=args.program,
            rules=rules,
            miles_fn=miles_fn,
            overrides=locks,
            override_notes=override_notes,
            zip_states=zip_states,
            region=region
        )
        
        # Report
        print(f"\nResults: {sum(status_count.values())} teams")
        for status, count in sorted(status_count.items()):
            print(f"  {status}: {count}")
        if reason_counts:
            print("\nFlagged for manual review, by reason (teams):")
            for reason, count in reason_counts.most_common():
                print(f"  {reason}: {count}")
        if unassigned_zips:
            print("\nUnassigned, by reason (zips):")
            for reason, zip_set in sorted(unassigned_zips.items()):
                print(f"  {reason}: {', '.join(sorted(zip_set))}")
            if "missing drive times; rebuild the drive matrix" in unassigned_zips:
                print("\nThese zips are in the zip table but not the drive matrix. With OSRM running, rebuild it:")
                print(f"  python3 tools/build_drive_matrix.py --source osrm --teams {args.teams} --events {args.events}")
            if any(r.startswith("zip is in ") for r in unassigned_zips):
                print("\nTo cover another state, add it to STATES in region.env, then rerun setup.sh "
                      "and tools/enable_drive_times.sh.")
        print(f"\nWrote {args.out}")
        
        # Exit with error if any teams are unassigned
        if status_count.get("unassigned", 0) > 0:
            sys.exit(1)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
