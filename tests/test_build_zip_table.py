import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools import build_zip_table as bzt

ROWS = [
    ("98101", 47.61, -122.33, "Seattle", "King County", "WA", "STANDARD"),
    ("97201", 45.51, -122.69, "Portland", "Multnomah County", "OR", "STANDARD"),
    ("83702", 43.63, -116.21, "Boise", "Ada County", "ID", "STANDARD"),
    ("98999", None, None, "", "", "WA", "PO BOX"),
]


def make_db(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE simple_zipcode (zipcode TEXT, lat REAL, lng REAL, major_city TEXT, "
                "county TEXT, state TEXT, zipcode_type TEXT)")
    con.executemany("INSERT INTO simple_zipcode VALUES (?,?,?,?,?,?,?)", ROWS)
    con.commit()
    con.close()


class BuildZipTableTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db = self.tmp / "db.sqlite"
        make_db(self.db)

    def read(self, name):
        with open(self.tmp / "out" / name) as f:
            return list(csv.DictReader(f))

    def test_exports_only_configured_states_with_coordinates(self):
        counts = bzt.export(self.db, ["WA", "OR"], self.tmp / "out")
        self.assertEqual(counts, {"WA": 1, "OR": 1})
        self.assertEqual([r["zip"] for r in self.read("zips.csv")], ["97201", "98101"])

    def test_state_index_covers_every_state(self):
        bzt.export(self.db, ["WA"], self.tmp / "out")
        states = {r["zip"]: r["state"] for r in self.read("zip_states.csv")}
        self.assertEqual(states["83702"], "ID")

    def test_state_with_no_zips_stops(self):
        with self.assertRaises(SystemExit):
            bzt.export(self.db, ["WA", "ZZ"], self.tmp / "out")

    def test_parse_states(self):
        self.assertEqual(bzt.parse_states(" wa, or "), ["WA", "OR"])
        for bad in ("", "Washington", "W1"):
            with self.subTest(bad=bad), self.assertRaises(SystemExit):
                bzt.parse_states(bad)

    def test_region_file_is_read(self):
        env = self.tmp / "region.env"
        env.write_text("# comment\nSTATES=WA,ID\n")
        self.assertEqual(bzt.region_states(env), ["WA", "ID"])


@unittest.skipUnless(bzt.DB_CACHE.exists(), "zip database not downloaded")
class RealDatabaseTest(unittest.TestCase):
    def test_washington_export_matches_the_committed_reference_table(self):
        out = Path(tempfile.mkdtemp())
        bzt.export(bzt.DB_CACHE, ["WA"], out)
        with open(out / "zips.csv") as f:
            got = [(r["zip"], r["lat"], r["lon"]) for r in csv.DictReader(f)]
        with open(bzt.ROOT / "reference" / "wa_zips.csv") as f:
            want = [(r["zip"], r["lat"], r["lon"]) for r in csv.DictReader(f)]
        self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()
