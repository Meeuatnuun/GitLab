import unittest

from app import create_app, format_resistance, parse_form

VALID_FORM = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_get_index_shows_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Q-point".encode(), response.data)

    def test_index_shows_circuit_diagram(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<svg", response.data)
        self.assertIn("Voltage Divider Bias".encode(), response.data)

    def test_diagram_shows_parameter_values(self):
        response = self.client.get("/")
        self.assertIn("47 kΩ".encode(), response.data)
        self.assertIn("2.2 kΩ".encode(), response.data)

    def test_diagram_updates_with_submitted_values(self):
        response = self.client.post("/", data=dict(VALID_FORM, r1="22000"))
        self.assertIn("22 kΩ".encode(), response.data)

    def test_post_valid_input_shows_active_q_point(self):
        response = self.client.post("/", data=VALID_FORM)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Active", response.data)
        self.assertIn(b"7.755", response.data)
        self.assertIn(b"1.324", response.data)


    def test_zero_resistance_shows_validation_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, r1="0"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("greater than 0".encode(), response.data)
        self.assertNotIn(b"region-active", response.data)

    def test_non_numeric_input_shows_parse_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, vcc="abc"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("numbers".encode(), response.data)

    def test_zero_vce_saturation_returns_page(self):
        form = dict(
            VALID_FORM, vcc="5", r1="1000", r2="100", rc="105.5",
            re="10", beta="200", vbe="0",
        )
        response = self.client.post("/", data=form)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Saturation", response.data)


class TestFormatResistance(unittest.TestCase):
    def test_kilo_ohm_amount_formats_without_conversion(self):
        self.assertEqual(format_resistance("100", "kΩ"), "100 kΩ")
        self.assertEqual(format_resistance("2.2", "kΩ"), "2.2 kΩ")
        self.assertEqual(format_resistance("1.0", "kΩ"), "1.0 kΩ")

    def test_ohm_amount_converts_to_kilo_ohms(self):
        self.assertEqual(format_resistance("47000", "Ω"), "47 kΩ")
        self.assertEqual(format_resistance("2200", "Ω"), "2.2 kΩ")
        self.assertEqual(format_resistance("1000", "Ω"), "1.0 kΩ")

    def test_small_values_stay_in_ohms(self):
        self.assertEqual(format_resistance("470", "Ω"), "470 Ω")

    def test_invalid_value_passes_through(self):
        self.assertEqual(format_resistance("abc"), "abc")


class TestParseForm(unittest.TestCase):
    def setUp(self):
        self.base = {
            "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
            "re": "1", "beta": "100", "vbe": "0.7",
        }

    def test_kilo_ohm_unit_multiplies_by_1000(self):
        form = dict(
            self.base,
            r1="100", r1_unit="kΩ",
            r2="22", r2_unit="kΩ",
            rc="2.2", rc_unit="kΩ",
            re="1", re_unit="kΩ",
        )
        values = parse_form(form)
        self.assertAlmostEqual(values["r1"], 100000.0)
        self.assertAlmostEqual(values["r2"], 22000.0)
        self.assertAlmostEqual(values["rc"], 2200.0)
        self.assertAlmostEqual(values["re"], 1000.0)

    def test_ohm_unit_keeps_value(self):
        form = dict(self.base, r1="470", r1_unit="Ω")
        self.assertAlmostEqual(parse_form(form)["r1"], 470.0)

    def test_missing_unit_defaults_to_base_unit(self):
        values = parse_form(dict(self.base, r1="47000"))
        self.assertAlmostEqual(values["r1"], 47000.0)

    def test_invalid_unit_raises(self):
        with self.assertRaises(ValueError) as context:
            parse_form(dict(self.base, r1_unit="MΩ"))
        self.assertIn("valid unit", str(context.exception))


if __name__ == "__main__":
    unittest.main()
