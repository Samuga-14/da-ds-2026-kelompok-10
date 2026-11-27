import sys
import unittest
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "etl"))

from normalize_survey import (
    RAW_PATH,
    STAGING_PATH,
    classify_distance_meters,
    clean_bedroom_facilities,
    normalize_kos_name,
    normalize_security,
    numeric_value,
    parse_campus_distance,
    parse_distance_meters,
    parse_extra_cost,
    parse_floor,
    parse_rent_price,
    parse_room_area,
    normalize_survey,
)


class SurveyNormalizationTests(unittest.TestCase):
    def test_numeric_value_accepts_common_survey_formats(self):
        self.assertEqual(numeric_value("40.000"), 40000.0)
        self.assertEqual(numeric_value("550000"), 550000.0)
        self.assertTrue(pd.isna(numeric_value("tidak ada")))

    def test_parse_room_area_handles_multiplication_1d_shorthand_and_typo(self):
        self.assertEqual(parse_room_area("4×4"), 16.0)
        self.assertEqual(parse_room_area("4*3"), 12.0)
        self.assertEqual(parse_room_area("3,5x5"), 17.5)
        self.assertEqual(parse_room_area("3x6 m2"), 18.0)
        self.assertEqual(parse_room_area("3"), 9.0)
        self.assertEqual(parse_room_area("4 m"), 16.0)
        self.assertEqual(parse_room_area("2000"), 200.0)

    def test_parse_floor_maps_basement_and_high_floors(self):
        self.assertEqual(parse_floor("bawah tanah"), (1.0, "1"))
        self.assertEqual(parse_floor("9"), (4.0, "4 - 5"))
        self.assertEqual(parse_floor("2"), (2.0, "2"))

    def test_parse_rent_price_scales_shorthand_and_strips_dots(self):
        self.assertEqual(parse_rent_price("7", is_annual=1), 7_000_000.0)
        self.assertEqual(parse_rent_price("7", is_annual=0), 700_000.0)
        self.assertEqual(parse_rent_price("700", is_annual=0), 700_000.0)
        self.assertEqual(parse_rent_price("70000", is_annual=0), 700_000.0)
        self.assertEqual(parse_rent_price("60000", is_annual=0), 600_000.0)
        self.assertEqual(parse_rent_price("700.000", is_annual=0), 700_000.0)
        self.assertEqual(parse_rent_price("2.000.000", is_annual=1), 2_000_000.0)

    def test_parse_campus_and_facility_distance_in_meters(self):
        dest, meters = parse_campus_distance("1,5 km")
        self.assertEqual(meters, 1500.0)
        self.assertEqual(classify_distance_meters(meters), "Sedang (1001 - 3000 m)")
        dest2, meters2 = parse_campus_distance("Kampus IT Del 450")
        self.assertEqual(dest2, "Kampus IT Del")
        self.assertEqual(meters2, 450.0)
        self.assertEqual(classify_distance_meters(meters2), "Sangat Dekat (<= 500 m)")
        self.assertTrue(pd.isna(parse_distance_meters("0", allow_zero=False)))
        self.assertEqual(parse_distance_meters("0", allow_zero=True), 0.0)

    def test_normalize_security_merges_cctv_saja_into_cctv(self):
        self.assertEqual(normalize_security("CCTV Saja"), "CCTV")
        self.assertEqual(normalize_security("CCTV"), "CCTV")
        self.assertEqual(normalize_security("Penjaga & CCTV"), "Penjaga & CCTV")
        self.assertEqual(normalize_security("Penjaga/Satpam"), "Penjaga/Satpam")

    def test_parse_extra_cost_and_logical_facility_cleaning(self):
        self.assertEqual(parse_extra_cost("100rb uang token listrik ", "Ada"), 100_000.0)
        self.assertEqual(parse_extra_cost("40", "Ada"), 40_000.0)
        self.assertEqual(parse_extra_cost("8150000", "Tidak"), 0.0)
        self.assertEqual(normalize_kos_name("Kos  birong"), "Kos Birong")
        self.assertEqual(
            clean_bedroom_facilities(
                "Ventilasi Jendela, Gorden, Kamar Kosong (Jika tidak ada fasilitas dalam kamar yang tersedia)"
            ),
            "Ventilasi Jendela, Gorden",
        )

    def test_real_survey_normalization(self):
        canonical, report = normalize_survey(RAW_PATH)

        self.assertEqual(report["raw_rows"], 569)
        self.assertEqual(report["staging_rows"], len(canonical))
        self.assertEqual(report["raw_columns"], 35)
        self.assertGreaterEqual(report["accepted_for_analysis"], 500)
        self.assertIn("harga_bulanan_norm", canonical.columns)
        self.assertIn("jarak_jalan_raya_m", canonical.columns)
        self.assertIn("klasifikasi_jarak_kampus_sekolah_tempatkerja", canonical.columns)
        self.assertIn("kategori_lantai", canonical.columns)
        self.assertNotIn("CCTV Saja", canonical["keamanan_kos"].unique())
        self.assertEqual(int((canonical["jarak_laundry_m"] == 0).sum()), 0)
        self.assertTrue(STAGING_PATH.exists())


if __name__ == "__main__":
    unittest.main()
