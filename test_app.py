import unittest

from app import create_app

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

    def test_post_valid_input_shows_active_q_point(self):
        response = self.client.post("/", data=VALID_FORM)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Active", response.data)
        self.assertIn(b"7.755", response.data)
        self.assertIn(b"1.324", response.data)


    def test_zero_resistance_shows_validation_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, r1="0"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("มากกว่า 0".encode(), response.data)
        self.assertNotIn(b"region-active", response.data)

    def test_non_numeric_input_shows_parse_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, vcc="abc"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("ตัวเลข".encode(), response.data)

    def test_zero_vce_saturation_returns_page(self):
        form = dict(
            VALID_FORM, vcc="5", r1="1000", r2="100", rc="105.5",
            re="10", beta="200", vbe="0",
        )
        response = self.client.post("/", data=form)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Saturation", response.data)


if __name__ == "__main__":
    unittest.main()
