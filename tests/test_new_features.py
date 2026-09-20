import os
import shutil
import sys
import unittest

import pandas as pd

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import utils.db_manager as dbm
import utils.state_manager as sm


class TestNewFeatures(unittest.TestCase):
    def setUp(self):
        self.test_cache_dir = ".cache_test"
        sm.CACHE_DIR = self.test_cache_dir
        sm.SESSION_FILE = os.path.join(self.test_cache_dir, "test_session.parquet")
        sm.META_FILE = os.path.join(self.test_cache_dir, "test_meta.txt")

    def tearDown(self):
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)

    def test_persistence(self):
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        ok, _ = sm.save_session(df, "MetaInfo")
        self.assertTrue(ok)

        loaded_df, meta, _ = sm.load_session()
        self.assertIsNotNone(loaded_df)
        self.assertEqual(len(loaded_df), 2)
        self.assertEqual(meta, "MetaInfo")

        has, _, _ = sm.has_valid_session()
        self.assertTrue(has)

    def test_db_manager_status_priority(self):
        rows = [
            {
                "recipient": "overwrite@dacta.pe",
                "status": "FAILED",
                "timestamp": "2023-01-01 10:00:00",
            },
            {
                "recipient": "overwrite@dacta.pe",
                "status": "SENT",
                "timestamp": "2023-01-01 10:05:00",
            },
        ]

        status_map = dbm._process_rows_into_map(rows)
        self.assertEqual(status_map["overwrite@dacta.pe"]["status"], "SENT")
        self.assertEqual(status_map["overwrite@dacta.pe"]["ts_raw"], "2023-01-01 10:05:00")
        self.assertIn("time", status_map["overwrite@dacta.pe"])

    def test_db_manager_requires_supabase(self):
        original_get_credentials = dbm._get_credentials
        original_client = dbm._client

        try:
            dbm._client = None
            dbm._get_credentials = lambda: (None, None)
            with self.assertRaises(dbm.SupabaseUnavailableError):
                dbm.get_status_map(["test@dacta.pe"])
        finally:
            dbm._get_credentials = original_get_credentials
            dbm._client = original_client


if __name__ == "__main__":
    unittest.main()
