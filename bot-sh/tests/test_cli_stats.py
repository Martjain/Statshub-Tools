import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot_sh.cli import stats_from_args_lenient, stats_from_args_strict


class TestCliStats(unittest.TestCase):
    def test_stats_from_args_strict_all(self):
        self.assertIsNone(stats_from_args_strict("tackles", all_stats=True))

    def test_stats_from_args_strict_valid(self):
        stats = stats_from_args_strict("tackles,shots", all_stats=False)
        self.assertEqual(stats, ["totalTackle", "shots"])

    def test_stats_from_args_strict_invalid(self):
        with self.assertRaises(SystemExit):
            stats_from_args_strict("unknownstat", all_stats=False)

    def test_stats_from_args_lenient(self):
        stats = stats_from_args_lenient("tackles,unknownstat")
        self.assertEqual(stats, ["totalTackle"])


if __name__ == "__main__":
    unittest.main()
