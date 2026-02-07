import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot_sh.models import get_lineup_positions


class TestLineups(unittest.TestCase):
    def test_get_lineup_positions_includes_gk(self):
        positions = get_lineup_positions("4-3-3")
        self.assertIsNotNone(positions)
        self.assertEqual(positions[0], "GK")
        self.assertEqual(len(positions), 11)

    def test_get_lineup_positions_3421(self):
        positions = get_lineup_positions("3-4-2-1")
        self.assertIsNotNone(positions)
        self.assertIn("RF", positions)
        self.assertIn("LF", positions)

    def test_get_lineup_positions_3412(self):
        positions = get_lineup_positions("3-4-1-2")
        self.assertIsNotNone(positions)
        self.assertIn("CAM", positions)
        self.assertIn("RST", positions)
        self.assertIn("LST", positions)

    def test_get_lineup_positions_unknown(self):
        self.assertIsNone(get_lineup_positions("2-3-5"))


if __name__ == "__main__":
    unittest.main()
