"""Geographic utilities for team sorting: distance calculations and zip lookups."""
import csv
import math


def load_zips(path):
    """Load zip code centroids from CSV.
    
    Returns: {zip: (lat, lon, city, county)}
    City and county are optional and default to empty strings.
    """
    zips = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            zips[row["zip"]] = (
                float(row["lat"]),
                float(row["lon"]),
                row.get("city", ""),
                row.get("county", "")
            )
    return zips


def miles_straight_line(zip_a, zip_b, zips):
    """Straight-line miles between zip centroids using haversine formula."""
    (lat1, lon1), (lat2, lon2) = zips[zip_a][:2], zips[zip_b][:2]
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = (math.sin((p2 - p1) / 2) ** 2 +
         math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def load_drive_matrix(path):
    """Load pre-computed drive times from CSV.
    
    Returns: {(team_zip, event_zip): (min_ferry_ok, min_no_ferry or None)}
    """
    drive = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            drive[(row["team_zip"], row["event_zip"])] = (
                float(row["min_ferry_ok"]),
                float(row["min_no_ferry"]) if row["min_no_ferry"] else None
            )
    return drive


def drive_minutes(zip_a, zip_b, drive_matrix, ferry_wait=30.0):
    """Drive minutes between zips, charging dock wait to ferry routes.
    
    Args:
        zip_a: Origin zip code
        zip_b: Destination zip code
        drive_matrix: Pre-loaded drive matrix from load_drive_matrix()
        ferry_wait: Minutes to add to routes that use a ferry (default 30)
    
    Returns:
        Drive time in minutes. Same zip = 0.
    """
    if zip_a == zip_b:
        return 0.0
    
    ferry_ok, no_ferry = drive_matrix[(zip_a, zip_b)]
    uses_ferry = no_ferry is None or ferry_ok < no_ferry - 0.5
    
    if uses_ferry and no_ferry is not None:
        return min(no_ferry, ferry_ok + ferry_wait)
    elif uses_ferry:
        return ferry_ok + ferry_wait
    else:
        return ferry_ok
