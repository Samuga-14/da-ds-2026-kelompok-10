import unittest
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from models.features import FEATURE_COLS
from services.analytics_service import (
    classify_fair_price,
    enrich_price_analysis,
    get_storytelling_insights,
    simulate_facility_upgrades,
)


class FairPriceAndSimulationTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        X = pd.DataFrame(rng.random((30, len(FEATURE_COLS))), columns=FEATURE_COLS)
        # Positive weight on AC and KM Dalam so facility simulation shows clear positive delta
        y = 550000 + X["is_ac"] * 350000 + X["km_dalam"] * 150000 + X["is_wifi"] * 100000
        self.model = LinearRegression().fit(X, y)
        self.models = {
            "Linear Regression (Baseline)": self.model,
            "Ridge Regression (L2 Tuned)": self.model,
            "Random Forest Regressor (Tuned)": self.model,
            "Gradient Boosting / XGBoost (Tuned)": self.model,
        }

    def test_classify_fair_price_categories(self):
        under = classify_fair_price(actual_price=600000, predicted_price=750000)
        self.assertEqual(under["kategori_harga"], "murah")
        self.assertIn("Underpriced", under["status_kewajaran"])

        fair = classify_fair_price(actual_price=710000, predicted_price=700000)
        self.assertEqual(fair["kategori_harga"], "wajar")
        self.assertIn("Fair Price", fair["status_kewajaran"])

        over = classify_fair_price(actual_price=900000, predicted_price=700000)
        self.assertEqual(over["kategori_harga"], "mahal")
        self.assertIn("Overpriced", over["status_kewajaran"])

    def test_simulate_facility_upgrades_increases_estimated_rent(self):
        base = {"is_ac": 0, "km_dalam": 0, "is_wifi": 0}
        result = simulate_facility_upgrades(base, self.model, candidate_upgrades=["is_ac", "km_dalam", "is_wifi"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["simulations"]), 3)
        self.assertGreater(result["combined_upgrade_monthly_rp"], result["baseline_monthly_rp"])
        self.assertIn("limitations", result)

    def test_storytelling_insights_contains_required_sections(self):
        df = pd.DataFrame({
            "kecamatan": ["Balige", "Laguboti", "Porsea", "Balige"],
            "harga_bulanan_norm": [700000, 725000, 725000, 650000],
            "status_kewajaran": [
                "Fair Price (Harga Wajar)",
                "Fair Price (Harga Wajar)",
                "Underpriced (Sangat Hemat)",
                "Overpriced (Kemahalan)",
            ],
        })
        story = get_storytelling_insights(df)
        self.assertEqual(story["status"], "ok")
        self.assertGreaterEqual(len(story["key_findings"]), 4)
        self.assertIn("untuk_penyewa", story["recommendations"])
        self.assertIn("untuk_pemilik_kos", story["recommendations"])


if __name__ == "__main__":
    unittest.main()
