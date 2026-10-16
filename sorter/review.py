"""Manual-review rules: which output rows a person should look at, and why."""
from dataclasses import dataclass

FALSE_WORDS = {"", "false", "no", "n", "0"}


@dataclass(frozen=True)
class Rules:
    small_zip: int = 3            # flag zips with this many teams or fewer
    large_zip: int = 30           # flag zips with this many teams or more
    assigned_miles: float = 40    # flag teams whose assigned event is farther than this
    nearest_miles: float = 75     # flag teams whose NEAREST event is farther than this
    travel: float = 90            # flag travel over this, in drive minutes (or straight-line miles)


def truthy(value):
    """Spreadsheet-style boolean: blank, false, no, n and 0 are false; anything else is true."""
    return value.strip().lower() not in FALSE_WORDS


def review_reasons(zip_count, assigned_miles, nearest_miles, travel, unassigned_reason, unit, rules):
    """Reasons a team row needs manual review, in a fixed order. Empty list = no review needed.

    Distances that are None (not computed) never trigger a rule; the unassigned reason covers them.
    unit is "drive" or "straight-line" and only changes the wording.
    """
    miles_label = "drive miles" if unit == "drive" else "straight-line miles"
    travel_label = "drive minutes" if unit == "drive" else "straight-line miles"
    reasons = []
    if unassigned_reason:
        reasons.append(f"unassigned: {unassigned_reason}")
    if zip_count <= rules.small_zip:
        reasons.append(f"{rules.small_zip:g} or fewer teams in zip ({zip_count})")
    if zip_count >= rules.large_zip:
        reasons.append(f"{rules.large_zip:g} or more teams in zip ({zip_count})")
    if assigned_miles is not None and assigned_miles > rules.assigned_miles:
        reasons.append(f"assigned event over {rules.assigned_miles:g} {miles_label} ({assigned_miles})")
    if nearest_miles is not None and nearest_miles > rules.nearest_miles:
        reasons.append(f"nearest event over {rules.nearest_miles:g} {miles_label} ({nearest_miles})")
    if travel is not None and travel > rules.travel:
        reasons.append(f"travel over {rules.travel:g} {travel_label} ({travel})")
    return reasons
