import unittest

from bjt_bias import calculate_dc_bias, validate_inputs


class TestValidation(unittest.TestCase):
    def test_valid_inputs_pass(self):
        validate_inputs(12, 47000, 10000, 2200, 1000, 150, 0.7)

    def test_non_positive_vcc_raises(self):
        with self.assertRaises(ValueError):
            validate_inputs(0, 47000, 10000, 2200, 1000, 150, 0.7)

    def test_non_positive_resistance_raises(self):
        for index in range(1, 5):
            args = [12, 47000, 10000, 2200, 1000, 150, 0.7]
            args[index] = 0
            with self.assertRaises(ValueError):
                validate_inputs(*args)

    def test_non_positive_beta_raises(self):
        with self.assertRaises(ValueError):
            validate_inputs(12, 47000, 10000, 2200, 1000, 0, 0.7)

    def test_vbe_must_be_below_vcc(self):
        with self.assertRaises(ValueError):
            validate_inputs(12, 47000, 10000, 2200, 1000, 150, 12)

    def test_negative_vbe_raises(self):
        with self.assertRaises(ValueError):
            validate_inputs(12, 47000, 10000, 2200, 1000, 150, -0.1)


DEFAULT = dict(vcc=12, r1=47000, r2=10000, rc=2200, re=1000, beta=150, vbe=0.7)


class TestExactOperatingPoint(unittest.TestCase):
    def test_default_case_is_active(self):
        result = calculate_dc_bias(**DEFAULT)
        exact = result["exact"]
        self.assertEqual(result["region"], "active")
        self.assertEqual(result["warnings"], [])
        self.assertAlmostEqual(exact["vth"], 2.1052631579, places=6)
        self.assertAlmostEqual(exact["rth"], 8245.614035, places=3)
        self.assertAlmostEqual(exact["ib"], 8.824501487e-06, delta=1e-9)
        self.assertAlmostEqual(exact["ic"], 0.001323675223, delta=1e-9)
        self.assertAlmostEqual(exact["ie"], 0.001332499725, delta=1e-9)
        self.assertAlmostEqual(exact["ve"], 1.332499725, delta=1e-6)
        self.assertAlmostEqual(exact["vb"], 2.032499725, delta=1e-6)
        self.assertAlmostEqual(exact["vc"], 9.087914509, delta=1e-6)
        self.assertAlmostEqual(exact["vce"], 7.755414785, delta=1e-6)

    def test_cutoff_when_vth_below_vbe(self):
        args = dict(DEFAULT, r2=1000)
        result = calculate_dc_bias(**args)
        exact = result["exact"]
        self.assertEqual(result["region"], "cutoff")
        self.assertAlmostEqual(exact["ib"], 0.0)
        self.assertAlmostEqual(exact["ic"], 0.0)
        self.assertAlmostEqual(exact["ie"], 0.0)
        self.assertAlmostEqual(exact["ve"], 0.0)
        self.assertAlmostEqual(exact["vc"], 12.0)
        self.assertAlmostEqual(exact["vce"], 12.0)
        self.assertAlmostEqual(exact["vb"], 0.25)
        self.assertTrue(any("cutoff" in warning for warning in result["warnings"]))

    def test_saturation_when_vce_at_or_below_limit(self):
        args = dict(DEFAULT, rc=10000)
        result = calculate_dc_bias(**args)
        self.assertEqual(result["region"], "saturation")
        self.assertAlmostEqual(result["exact"]["vce"], -2.569251955, delta=1e-6)
        self.assertAlmostEqual(result["ic_sat"], 0.001072727273, delta=1e-9)
        self.assertTrue(any("saturation" in warning for warning in result["warnings"]))


class TestApproximateComparison(unittest.TestCase):
    def test_default_case_matches_approximation_closely(self):
        result = calculate_dc_bias(**DEFAULT)
        approx = result["approximate"]
        self.assertTrue(approx["applicable"])
        self.assertEqual(approx["reason"], "")
        self.assertAlmostEqual(approx["ratio"], 1.5, places=9)
        self.assertAlmostEqual(approx["vb"], 2.1052631579, places=6)
        self.assertAlmostEqual(approx["ve"], 1.4052631579, places=6)
        self.assertAlmostEqual(approx["ic"], 0.001405263158, delta=1e-9)
        self.assertAlmostEqual(approx["vce"], 7.503157895, places=6)
        comparison = result["comparison"]
        self.assertAlmostEqual(comparison["ic_diff_pct"], 6.16374269, delta=0.01)
        self.assertAlmostEqual(comparison["vce_diff_pct"], 3.25265504, delta=0.01)

    def test_condition_failure_marks_inapplicable(self):
        args = dict(DEFAULT, re=100)
        result = calculate_dc_bias(**args)
        approx = result["approximate"]
        self.assertFalse(approx["applicable"])
        self.assertIn("10R2", approx["reason"])
        self.assertIsNotNone(approx["ic"])
        self.assertIsNone(result["comparison"]["ic_diff_pct"])
        self.assertIsNone(result["comparison"]["vce_diff_pct"])

    def test_cutoff_case_approximation_is_unavailable(self):
        result = calculate_dc_bias(**dict(DEFAULT, r2=1000))
        approx = result["approximate"]
        self.assertFalse(approx["applicable"])
        self.assertIn("cutoff", approx["reason"])
        self.assertIsNone(approx["ve"])
        self.assertIsNone(result["comparison"]["ic_diff_pct"])


if __name__ == "__main__":
    unittest.main()
