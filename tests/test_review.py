import unittest

from sorter import review

RULES = review.Rules()


def flags(zip_count=10, assigned_miles=10.0, nearest_miles=10.0, travel=10.0,
          unassigned_reason=None, unit="drive", rules=RULES):
    return review.review_reasons(zip_count, assigned_miles, nearest_miles, travel,
                                 unassigned_reason, unit, rules)


class ReviewReasonsTest(unittest.TestCase):
    def test_ordinary_team_has_no_flags(self):
        self.assertEqual(flags(), [])

    def test_small_zip_group(self):
        self.assertEqual(flags(zip_count=3), ["3 or fewer teams in zip (3)"])
        self.assertEqual(flags(zip_count=4), [])

    def test_large_zip_group(self):
        self.assertEqual(flags(zip_count=30), ["30 or more teams in zip (30)"])
        self.assertEqual(flags(zip_count=29), [])

    def test_assigned_event_over_40_miles(self):
        self.assertEqual(flags(assigned_miles=40.1), ["assigned event over 40 drive miles (40.1)"])
        self.assertEqual(flags(assigned_miles=40.0), [])

    def test_nearest_event_over_75_miles(self):
        self.assertEqual(flags(assigned_miles=30, nearest_miles=76.0),
                         ["nearest event over 75 drive miles (76.0)"])
        self.assertEqual(flags(nearest_miles=75.0), [])

    def test_long_travel_time(self):
        self.assertEqual(flags(travel=95.0), ["travel over 90 drive minutes (95.0)"])

    def test_straight_line_unit_labels(self):
        self.assertEqual(flags(assigned_miles=50.0, travel=95.0, unit="straight-line"),
                         ["assigned event over 40 straight-line miles (50.0)",
                          "travel over 90 straight-line miles (95.0)"])

    def test_reasons_combine_in_a_fixed_order(self):
        self.assertEqual(flags(zip_count=1, assigned_miles=80.0, nearest_miles=80.0, travel=100.0), [
            "3 or fewer teams in zip (1)",
            "assigned event over 40 drive miles (80.0)",
            "nearest event over 75 drive miles (80.0)",
            "travel over 90 drive minutes (100.0)",
        ])

    def test_unassigned_team_is_flagged_with_its_reason_first(self):
        self.assertEqual(flags(zip_count=1, assigned_miles=None, travel=None, nearest_miles=None,
                               unassigned_reason="zip code not found"),
                         ["unassigned: zip code not found", "3 or fewer teams in zip (1)"])

    def test_missing_distances_do_not_flag(self):
        self.assertEqual(flags(assigned_miles=None, nearest_miles=None, travel=None), [])

    def test_thresholds_are_configurable(self):
        rules = review.Rules(small_zip=1, large_zip=5, assigned_miles=10, nearest_miles=20, travel=30)
        self.assertEqual(flags(zip_count=5, assigned_miles=11, nearest_miles=11, travel=11, rules=rules),
                         ["5 or more teams in zip (5)", "assigned event over 10 drive miles (11)"])


class LooksCloserTest(unittest.TestCase):
    def test_reason_names_the_event_and_both_figures(self):
        reasons = review.review_reasons(10, 10.0, 10.0, 10.0, None, "drive", RULES,
                                        looks_closer=("OHH-SAT", 18.2, 41.0))
        self.assertEqual(reasons, ["looks closer on the map: OHH-SAT is 18.2 mi straight-line "
                                   "but 41.0 min farther by road"])

    def test_no_candidate_means_no_flag(self):
        self.assertEqual(review.review_reasons(10, 10.0, 10.0, 10.0, None, "drive", RULES,
                                               looks_closer=None), [])

    def test_order_puts_it_after_distance_rules(self):
        reasons = review.review_reasons(10, 50.0, 10.0, 95.0, None, "drive", RULES,
                                        looks_closer=("X", 5.0, 40.0))
        self.assertEqual([r.split(" (")[0].split(":")[0] for r in reasons],
                         ["assigned event over 40 drive miles", "looks closer on the map",
                          "travel over 90 drive minutes"])


class LooksCloserEventTest(unittest.TestCase):
    """Picks the event that looks nearer than the assigned one but is far longer by road."""
    EVENTS = [{"code": "ACROSS", "zip": "A"}, {"code": "ASSIGNED", "zip": "B"},
              {"code": "ASSIGNED-SUN", "zip": "B"}, {"code": "NEARBY", "zip": "C"}]
    STRAIGHT = {"A": 10.0, "B": 30.0, "C": 25.0}   # miles from the team
    MINUTES = {"A": 95.0, "B": 40.0, "C": 50.0}    # drive minutes from the team

    def find(self, threshold=30):
        return review.looks_closer_event(
            "ASSIGNED", "B", self.EVENTS, lambda z: self.STRAIGHT[z], lambda z: self.MINUTES[z], threshold)

    def test_finds_the_water_crossing(self):
        self.assertEqual(self.find(), ("ACROSS", 10.0, 55.0))

    def test_threshold_filters_small_detours(self):
        self.assertIsNone(self.find(threshold=60))

    def test_same_venue_and_farther_events_are_ignored(self):
        self.STRAIGHT = {"A": 40.0, "B": 30.0, "C": 35.0}
        self.assertIsNone(self.find())

    def test_unroutable_event_is_ignored(self):
        self.MINUTES = {"A": float("inf"), "B": 40.0, "C": 50.0}
        self.assertIsNone(self.find())


class TruthyTest(unittest.TestCase):
    def test_host_values(self):
        for value in ("true", "TRUE", "yes", "Y", "1", "x", "T2-HOSTVENUE"):
            with self.subTest(value=value):
                self.assertTrue(review.truthy(value))
        for value in ("", " ", "false", "FALSE", "no", "N", "0"):
            with self.subTest(value=value):
                self.assertFalse(review.truthy(value))


if __name__ == "__main__":
    unittest.main()
