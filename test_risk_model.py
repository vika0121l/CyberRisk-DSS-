
import unittest

from risk_model import calculate_advanced_risk


class TestAdvancedRiskModel(unittest.TestCase):

    def test_minimum_risk(self):
        result = calculate_advanced_risk(1, 1, 1)

        self.assertEqual(result["probability"], 1)
        self.assertEqual(result["impact"], 1)
        self.assertEqual(result["risk_score"], 1)
        self.assertEqual(result["risk_level"], "Дуже низький")

    def test_maximum_risk(self):
        result = calculate_advanced_risk(5, 5, 5)

        self.assertEqual(result["probability"], 5)
        self.assertEqual(result["impact"], 5)
        self.assertEqual(result["risk_score"], 25)
        self.assertEqual(result["risk_level"], "Критичний")

    def test_medium_risk(self):
        result = calculate_advanced_risk(3, 3, 4)

        self.assertEqual(result["probability"], 3)
        self.assertEqual(result["risk_score"], 12)
        self.assertEqual(result["risk_level"], "Середній")

    def test_rounding(self):
        result = calculate_advanced_risk(4, 5, 5)

        self.assertEqual(result["probability"], 5)
        self.assertEqual(result["risk_score"], 25)

    def test_invalid_low_value(self):
        with self.assertRaises(ValueError):
            calculate_advanced_risk(0, 3, 5)

    def test_invalid_high_value(self):
        with self.assertRaises(ValueError):
            calculate_advanced_risk(3, 6, 5)

    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            calculate_advanced_risk("5", 3, 5)

    def test_boolean_value(self):
        with self.assertRaises(ValueError):
            calculate_advanced_risk(True, 3, 5)

    def test_risk_score_range(self):
        for threat in range(1, 6):
            for vulnerability in range(1, 6):
                for criticality in range(1, 6):
                    result = calculate_advanced_risk(
                        threat,
                        vulnerability,
                        criticality
                    )

                    self.assertGreaterEqual(
                        result["risk_score"], 1
                    )
                    self.assertLessEqual(
                        result["risk_score"], 25
                    )


if __name__ == "__main__":
    unittest.main()
