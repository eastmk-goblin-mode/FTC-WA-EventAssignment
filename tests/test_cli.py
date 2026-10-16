import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sorter import cli

ROOT = Path(__file__).resolve().parent.parent

ZIPS = {
    "98101": (47.61, -122.33, "Seattle", "King County"),
    "98402": (47.25, -122.44, "Tacoma", "Pierce County"),
    "97201": (45.51, -122.69, "Portland", "Multnomah County"),
}
ZIP_STATES = {"98101": "WA", "98402": "WA", "97201": "OR", "83702": "ID"}


class UnassignedReasonTest(unittest.TestCase):
    def reason(self, zip_code, mode="drive", missing_drive_time=True):
        return cli.unassigned_reason(zip_code, ZIPS, ZIP_STATES, {"WA", "OR"}, mode, missing_drive_time)

    def test_zip_in_an_unconfigured_state(self):
        self.assertEqual(self.reason("83702"), "zip is in ID, which region.env does not include")

    def test_zip_that_does_not_exist(self):
        self.assertEqual(self.reason("98705"), "zip code not found")

    def test_drive_mode_zip_missing_from_matrix(self):
        self.assertEqual(self.reason("97201"), "missing drive times; rebuild the drive matrix")

    def test_zip_with_every_drive_time_but_every_event_full(self):
        self.assertEqual(self.reason("98101", missing_drive_time=False), "no event with room")

    def test_straight_line_mode_known_zip_is_capacity(self):
        self.assertEqual(self.reason("98101", mode="miles", missing_drive_time=False), "no event with room")


def write_csv(path, rows, header=None):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        if header:
            w.writerow(header)
        w.writerows(rows)


class CliEndToEndTest(unittest.TestCase):
    """Runs the CLI as a subprocess on a tiny region with one team of every kind."""

    def setUp(self):
        d = self.d = Path(tempfile.mkdtemp())
        write_csv(d / "zips.csv", [
            ("98101", 47.61, -122.33, "Seattle", "King County", "WA", "STANDARD"),
            ("98402", 47.25, -122.44, "Tacoma", "Pierce County", "WA", "STANDARD"),
            ("97201", 45.51, -122.69, "Portland", "Multnomah County", "OR", "STANDARD"),
        ], ["zip", "lat", "lon", "city", "county", "state", "type"])
        write_csv(d / "zip_states.csv", [(z, s) for z, s in ZIP_STATES.items()], ["zip", "state"])
        write_csv(d / "events.csv", [("SEA", "98101", 2), ("TAC", "98402", 1)])
        write_csv(d / "teams.csv", [
            ("1", "Near", "98101"),
            ("2", "Portland", "97201"),
            ("3", "Boise", "83702"),
            ("4", "Typo", "98705"),
            ("5", "Tacoma A", "98402"),
            ("6", "Tacoma B", "98402"),
        ])
        write_csv(d / "drive.csv", [
            ("98101", "98402", 35, 30, 35, 30, 10),
            ("98402", "98402", 0, 0, 0, 0, 10),
        ], ["team_zip", "event_zip", "min_ferry_ok", "mi_ferry_ok", "min_no_ferry", "mi_no_ferry", "snap_m"])

    def run_cli(self, *extra):
        d = self.d
        cmd = [sys.executable, "-m", "sorter.cli", "--program", "FLL", "--teams", d / "teams.csv",
               "--events", d / "events.csv", "--zips", d / "zips.csv", "--zip-states", d / "zip_states.csv",
               "--out", d / "out.csv", *extra]
        result = subprocess.run([str(c) for c in cmd], cwd=ROOT, capture_output=True, text=True)
        with open(d / "out.csv") as f:
            rows = {r["team_id"]: r for r in csv.DictReader(f)}
        return result, rows

    def test_drive_mode_reasons_and_rebuild_hint(self):
        result, rows = self.run_cli("--drive-matrix", self.d / "drive.csv")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(rows["1"]["status"], "assigned")
        self.assertEqual(rows["2"]["flag_reason"], "missing drive times; rebuild the drive matrix")
        self.assertEqual(rows["3"]["flag_reason"], "zip is in ID, which region.env does not include")
        self.assertEqual(rows["4"]["flag_reason"], "zip code not found")
        # 98402 has a drive time only to TAC (1 seat); the 2-team zip group fits nowhere it
        # can be routed, and the missing 98402->SEA time is the real cause.
        self.assertEqual(rows["5"]["flag_reason"], "missing drive times; rebuild the drive matrix")
        self.assertIn("python3 tools/build_drive_matrix.py", result.stdout)
        self.assertIn("83702", result.stdout)

    def test_straight_line_mode_places_every_in_region_team(self):
        write_csv(self.d / "events.csv", [("SEA", "98101", 10), ("TAC", "98402", 10)])
        result, rows = self.run_cli("--drive-matrix", self.d / "missing.csv")
        self.assertEqual(rows["2"]["status"], "flagged")  # Portland is over 90 miles from both events
        self.assertEqual({rows[t]["status"] for t in ("1", "5", "6")}, {"assigned"})
        self.assertEqual(rows["3"]["status"], "unassigned")
        self.assertEqual(rows["4"]["status"], "unassigned")

    def test_every_input_team_is_in_the_output(self):
        _, rows = self.run_cli("--drive-matrix", self.d / "drive.csv")
        self.assertEqual(sorted(rows), ["1", "2", "3", "4", "5", "6"])


if __name__ == "__main__":
    unittest.main()
