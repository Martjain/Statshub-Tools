import csv
import json
import os
import tempfile
import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot_sh.outputs import derive_alt_output_path, save_results


class TestOutputs(unittest.TestCase):
    def test_derive_alt_output_path(self):
        self.assertEqual(derive_alt_output_path("out.json"), "out.csv")
        self.assertEqual(derive_alt_output_path("out.csv"), "out.json")
        self.assertEqual(derive_alt_output_path("out"), "out.csv")

    def test_save_results_json(self):
        data = {
            "Team A": {
                "Tackles": [
                    {
                        "position": "RB",
                        "total": "10",
                        "average": "1.2",
                        "highest": "3",
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "results.json")
            save_results(data, path)
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertIn("Team A", loaded)
            self.assertIn("Tackles", loaded["Team A"])

    def test_save_results_csv(self):
        data = {
            "Team A": {
                "Tackles": [
                    {
                        "position": "RB",
                        "total": "10",
                        "average": "1.2",
                        "highest": "3",
                        "no_data": False,
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "results.csv")
            save_results(data, path)
            with open(path, "r", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            self.assertEqual(
                rows[0],
                ["team", "stat", "position", "total", "average", "highest", "no_data"],
            )
            self.assertEqual(rows[1][0], "Team A")
            self.assertEqual(rows[1][1], "Tackles")


if __name__ == "__main__":
    unittest.main()
