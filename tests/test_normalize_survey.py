import sys
import unittest
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "etl"))

from normalize_survey import (
    RAW_PATH,
    STAGING_PATH,
    normalize_survey,
    numeric_value,
    room_area_value,
)


class SurveyNormalizationTests(unittest.TestCase):
    def test_numeric_value_accepts_common_survey_formats(self):
        self.assertEqual(numeric_value("40.000"), 40000.0)
        self.assertEqual(numeric_value("550000"), 550000.0)
        self.assertTrue(pd.isna(numeric_value("tidak ada")))

    def test_room_area_accepts_dimensions(self):
        self.assertEqual(room_area_value("2 x 3"), 6.0)
        self.assertEqual(room_area_value("3,5x5"), 17.5)
        self.assertEqual(room_area_value("18 m2"), 18.0)

    def test_real_survey_normalization(self):
        canonical, report = normalize_survey(RAW_PATH)

        self.assertEqual(report["raw_rows"], 328)
        self.assertEqual(report["staging_rows"], len(canonical))
        self.assertEqual(report["raw_columns"], 44)
        self.assertIn("harga_bulanan_norm", canonical.columns)
        self.assertIn("jarak_jalan_raya_m", canonical.columns)
        self.assertTrue(STAGING_PATH.exists())


if __name__ == "__main__":
    unittest.main()
