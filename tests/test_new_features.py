import unittest
import pandas as pd
import os
import shutil
from datetime import datetime
import sys

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils.state_manager as sm
import utils.db_manager as dbm
from utils.db_manager import _process_rows_into_map

class TestNewFeatures(unittest.TestCase):

    def setUp(self):
        # Setup Cache
        self.test_cache_dir = ".cache_test"
        sm.CACHE_DIR = self.test_cache_dir
        sm.SESSION_FILE = os.path.join(self.test_cache_dir, "test_session.parquet")
        sm.META_FILE = os.path.join(self.test_cache_dir, "test_meta.txt")

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)

    def test_persistence(self):
        df = pd.DataFrame({'A': [1, 2], 'B': ['x', 'y']})
        ok, msg = sm.save_session(df, "MetaInfo")
        self.assertTrue(ok)
        
        loaded_df, meta, ts = sm.load_session()
        self.assertIsNotNone(loaded_df)
        self.assertEqual(len(loaded_df), 2)
        self.assertEqual(meta, "MetaInfo")
        
        has, _, _ = sm.has_valid_session()
        self.assertTrue(has)

    def test_db_manager(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = [
            {"recipient": "test@dacta.pe", "status": "SENT", "timestamp": now},
            {"recipient": "fail@dacta.pe", "status": "FAILED", "timestamp": now},
        ]
        status_map = _process_rows_into_map(rows)
        self.assertEqual(status_map["test@dacta.pe"]['status'], 'SENT')
        self.assertEqual(status_map["fail@dacta.pe"]['status'], 'FAILED')
        self.assertNotIn("missing@dacta.pe", status_map)

    def test_db_manager_overwrite(self):
        now1 = "2023-01-01 10:00:00"
        now2 = "2023-01-01 10:05:00"
        rows = [
            {"recipient": "overwrite@dacta.pe", "status": "FAILED", "timestamp": now1},
            {"recipient": "overwrite@dacta.pe", "status": "SENT", "timestamp": now2},
        ]
        status_map = _process_rows_into_map(rows)
        self.assertEqual(status_map["overwrite@dacta.pe"]['status'], 'SENT')
        self.assertIn('ts_raw', status_map["overwrite@dacta.pe"])
        self.assertEqual(status_map["overwrite@dacta.pe"]['ts_raw'], now2)

    def test_session_scoped_status(self):
        old_time = "2023-01-01 10:00:00"
        rows = [{"recipient": "old@dacta.pe", "status": "SENT", "timestamp": old_time}]
        status_map = _process_rows_into_map(rows)
        self.assertEqual(status_map["old@dacta.pe"]['status'], 'SENT')

        # Empty rows = sin resultado (pending implícito en la app)
        empty_map = _process_rows_into_map([])
        self.assertNotIn("old@dacta.pe", empty_map)

if __name__ == '__main__':
    unittest.main()
