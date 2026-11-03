import unittest

from electrical import analyze_dc


class TestAnalyzeDC(unittest.TestCase):
    def test_calculates_current_and_power(self):
        result = analyze_dc(12, 6)

        self.assertEqual(result["current_a"], 2.0)
        self.assertEqual(result["power_w"], 24.0)

    def test_rejects_zero_resistance(self):
        with self.assertRaises(ValueError):
            analyze_dc(12, 0)

    def test_rejects_negative_resistance(self):
        with self.assertRaises(ValueError):
            analyze_dc(12, -6)


if __name__ == "__main__":
    unittest.main()
