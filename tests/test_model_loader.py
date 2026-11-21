"""Uji loader model (#31): jalankan dengan `python -m unittest tests.test_model_loader -v`."""
import json
import os
import pickle
import tempfile
import unittest
from unittest import mock

import numpy as np
import sklearn
from sklearn.linear_model import LinearRegression

import server
from models.features import FEATURE_COLS

MODEL_NAMES = [
    "Linear Regression (Baseline)",
    "Ridge Regression (L2 Tuned)",
    "Random Forest Regressor (Tuned)",
    "Gradient Boosting / XGBoost (Tuned)",
]


def _make_bundle(features=None):
    rng = np.random.default_rng(0)
    X = rng.random((20, len(FEATURE_COLS)))
    model = LinearRegression().fit(X, rng.random(20))
    return {
        "format_version": 2,
        "sklearn_version": sklearn.__version__,
        "best_algorithm": MODEL_NAMES[0],
        "model": model,
        "all_models": {name: model for name in MODEL_NAMES},
        "features": list(FEATURE_COLS) if features is None else features,
        "metrics": {name: {"MAE": 1.0} for name in MODEL_NAMES},
    }


class ModelLoaderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = self.tmp.name
        os.makedirs(os.path.join(base, "models", "registry"))
        patches = [
            mock.patch.object(server, "BASE_DIR", base),
            mock.patch.object(server, "MODEL_DIR", os.path.join(base, "models")),
            mock.patch.object(server, "REGISTRY_MANIFEST_PATH",
                              os.path.join(base, "models", "registry", "model_manifest.json")),
            mock.patch.object(server, "ensure_database", lambda: None),
            mock.patch.object(server, "MODEL_BUNDLE", None),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.base = base

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, bundle=None, manifest=None, write_artifact=True):
        bundle = bundle or _make_bundle()
        if write_artifact:
            with open(os.path.join(self.base, "models", "best_rf_model.pkl"), "wb") as f:
                pickle.dump(bundle, f)
        manifest = manifest if manifest is not None else {
            "model_artifact": "models/best_rf_model.pkl",
            "features": list(FEATURE_COLS),
            "best_algorithm": MODEL_NAMES[0],
            "sklearn_version": sklearn.__version__,
        }
        with open(server.REGISTRY_MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f)

    def test_valid_manifest_and_bundle_loads(self):
        self._write()
        bundle = server.load_model_bundle()
        self.assertEqual(bundle["features"], FEATURE_COLS)

    def test_manifest_missing(self):
        with self.assertRaisesRegex(server.ModelUnavailableError, "Manifest model tidak ditemukan"):
            server.load_model_bundle()

    def test_manifest_corrupt_json(self):
        with open(server.REGISTRY_MANIFEST_PATH, "w", encoding="utf-8") as f:
            f.write("{bukan json")
        with self.assertRaisesRegex(server.ModelUnavailableError, "rusak"):
            server.load_model_bundle()

    def test_manifest_missing_keys(self):
        self._write(manifest={"model_artifact": "models/best_rf_model.pkl"})
        with self.assertRaisesRegex(server.ModelUnavailableError, "kunci hilang"):
            server.load_model_bundle()

    def test_manifest_features_mismatch(self):
        self._write(manifest={
            "model_artifact": "models/best_rf_model.pkl",
            "features": FEATURE_COLS[::-1],
            "best_algorithm": MODEL_NAMES[0],
            "sklearn_version": sklearn.__version__,
        })
        with self.assertRaisesRegex(server.ModelUnavailableError, "fitur pada manifest"):
            server.load_model_bundle()

    def test_artifact_missing(self):
        self._write(write_artifact=False)
        with self.assertRaisesRegex(server.ModelUnavailableError, "tidak ditemukan"):
            server.load_model_bundle()

    def test_artifact_outside_models_folder_rejected(self):
        self._write(manifest={
            "model_artifact": "../luar.pkl",
            "features": list(FEATURE_COLS),
            "best_algorithm": MODEL_NAMES[0],
            "sklearn_version": sklearn.__version__,
        })
        with self.assertRaisesRegex(server.ModelUnavailableError, "di luar folder models"):
            server.load_model_bundle()

    def test_bundle_feature_order_differs(self):
        self._write(bundle=_make_bundle(features=FEATURE_COLS[::-1]))
        with self.assertRaisesRegex(server.ModelUnavailableError, "Urutan fitur model"):
            server.load_model_bundle()

    def test_bundle_not_matching_manifest_algorithm(self):
        bundle = _make_bundle()
        bundle["best_algorithm"] = MODEL_NAMES[1]
        self._write(bundle=bundle)
        with self.assertRaisesRegex(server.ModelUnavailableError, "Manifest tidak cocok"):
            server.load_model_bundle()

    def test_corrupt_pickle(self):
        self._write()
        with open(os.path.join(self.base, "models", "best_rf_model.pkl"), "wb") as f:
            f.write(b"bukan pickle")
        with self.assertRaisesRegex(server.ModelUnavailableError, "tidak kompatibel atau rusak"):
            server.load_model_bundle()

    def test_sklearn_version_mismatch(self):
        bundle = _make_bundle()
        bundle["sklearn_version"] = "0.0.1"
        self._write(bundle=bundle)
        with self.assertRaisesRegex(server.ModelUnavailableError, "scikit-learn"):
            server.load_model_bundle()


if __name__ == "__main__":
    unittest.main()