"""Command-line interface for team sorting with map output."""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

from . import geo, assign


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
    """Load pre-assignments from CSV: league_name, team_number.
    
    Returns {team_number: event_code}. Lines starting with # are comments.
    """
    if not path or not Path(path).exists():
        return {}
    
    locks = {}
    with open(path) as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0] or row[0].startswith("#"):
                continue
            if len(row) >= 2:
                event_code, team_num = row[0].strip(), row[1].strip()
                locks[team_num] = event_code
    return locks


def write_map_output(output_path, teams, team_names, team_host, assignment, events, zips,
                     distance_fn, mode, program, flag_over=90):
    """Write the map file for visualization.
    
    Required columns (map team):
      team_id, team_name, team_zipCode, team_coordinates, event_id, 
      event_zipCode, event_coordinates, program
    
    Additional columns (operational):
      host_team, miles/drive_minutes, status, flag_reason
    """
    event_zips = {e["code"]: e["zip"] for e in events}
    status_count = Counter()
    
    def wkt(zip_code):
        """Return WKT POINT string for a zip centroid."""
        if zip_code not in zips:
            return ""
        lat, lon = zips[zip_code][:2]
        return f"POINT ({lon} {lat})"
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        
        # Header - required columns first, then operational columns
        distance_col = "drive_minutes" if mode == "drive" else "miles"
        writer.writerow([
            "team_id", "team_name", "team_zipCode", "team_coordinates",
            "event_id", "event_zipCode", "event_coordinates", "program",
            "host_team", distance_col, "status", "flag_reason"
        ])
        
        # Rows
        for team in teams:
            zip_code = team["zip"]
            event_code = assignment.get(team["num"])
            team_wkt = wkt(zip_code)
            
            if not event_code:
                # Unassigned
                event_zip = ""
                event_wkt = ""
                distance = ""
                if zip_code not in zips:
                    status = "unassigned"
                    reason = "zip code not found"
                else:
                    status = "unassigned"
                    reason = "no event with room"
            else:
                # Assigned
                event_zip = event_zips[event_code]
                event_wkt = wkt(event_zip)
                distance = round(distance_fn(zip_code, event_zip), 1)
                
                if distance > flag_over:
                    status = "flagged"
                    reason = f"travel over {flag_over} {distance_col.replace('_', ' ')}"
                else:
                    status = "assigned"
                    reason = ""
            
            status_count[status] += 1
            writer.writerow([
                team["num"],                        # team_id
                team_names.get(team["num"], ""),    # team_name
                zip_code,                           # team_zipCode
                team_wkt,                           # team_coordinates
                event_code or "",                   # event_id
                event_zip,                          # event_zipCode
                event_wkt,                          # event_coordinates
                program,                            # program
                team_host.get(team["num"], ""),     # host_team
                distance,                           # miles or drive_minutes
                status,                             # status
                reason                              # flag_reason
            ])
    
    return status_count


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
                       help="Zip centroids CSV (default: .data/wa_zips.csv, falls back to data/wa_zips.csv)")
    parser.add_argument("--drive-matrix", default=".data/drive_matrix.csv",
                       help="Drive matrix CSV (default: .data/drive_matrix.csv)")
    parser.add_argument("--pre-assignments",
                       help="Pre-assigned teams CSV (event_code,team_number)")
    
    # Output
    parser.add_argument("--out", default=".data/team_assignments.csv",
                       help="Output map CSV (default: .data/team_assignments.csv)")
    
    # Algorithm options
    parser.add_argument("--method", choices=["bump", "largest", "regret"], default="bump",
                       help="Ordering strategy (default: bump)")
    parser.add_argument("--flag-over", type=float, default=90,
                       help="Flag assignments over this travel threshold (default: 90)")
    
    args = parser.parse_args()
    
    # Load data
    try:
        # Resolve zips path with fallback
        if args.zips:
            zips_path = Path(args.zips)
        else:
            # Default: try .data/ first, fall back to data/
            if Path(".data/wa_zips.csv").exists():
                zips_path = Path(".data/wa_zips.csv")
            elif Path("data/wa_zips.csv").exists():
                zips_path = Path("data/wa_zips.csv")
            else:
                print("Error: wa_zips.csv not found. Run setup.sh first.", file=sys.stderr)
                sys.exit(2)
        
        zips = geo.load_zips(zips_path)
        events = load_events(args.events)
        teams, team_names, team_host = load_teams(args.teams)
        locks = load_pre_assignments(args.pre_assignments)
        
        # Determine distance function
        drive_matrix_path = Path(args.drive_matrix)
        if drive_matrix_path.exists():
            print(f"Using drive times from {args.drive_matrix}")
            drive_matrix = geo.load_drive_matrix(args.drive_matrix)
            distance_fn = lambda a, b: geo.drive_minutes(a, b, drive_matrix)
            mode = "drive"
        else:
            print(f"Drive matrix not found at {args.drive_matrix}, using straight-line miles")
            distance_fn = lambda a, b: geo.miles_straight_line(a, b, zips)
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
        status_count = write_map_output(
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
            flag_over=args.flag_over
        )
        
        # Report
        print(f"\nResults: {sum(status_count.values())} teams")
        for status, count in sorted(status_count.items()):
            print(f"  {status}: {count}")
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
