import unittest

from bjt_bias import validate_inputs


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


if __name__ == "__main__":
    unittest.main()
