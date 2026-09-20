import unittest
import pandas as pd
import os
import shutil
import sqlite3
from datetime import datetime
import sys

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils.state_manager as sm
import utils.db_manager as dbm

class TestNewFeatures(unittest.TestCase):
    
    def setUp(self):
        # Setup Cache
        self.test_cache_dir = ".cache_test"
        sm.CACHE_DIR = self.test_cache_dir
        sm.SESSION_FILE = os.path.join(self.test_cache_dir, "test_session.parquet")
        sm.META_FILE = os.path.join(self.test_cache_dir, "test_meta.txt")
        
        # Setup DB
        self.test_db = "test_ledger.db"
        dbm.DB_NAME = self.test_db
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        c.execute("CREATE TABLE send_attempts (att_id TEXT, ledger_key TEXT, recipient TEXT, status TEXT, reason TEXT, timestamp TEXT, run_id TEXT)")
        conn.commit()
        conn.close()

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

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
        # Insert Data
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO send_attempts VALUES (?,?,?,?,?,?,?)", 
                  ("1", "key1", "test@dacta.pe", "SENT", "OK", now, "run1"))
        c.execute("INSERT INTO send_attempts VALUES (?,?,?,?,?,?,?)", 
                  ("2", "key2", "fail@dacta.pe", "FAILED", "ERR", now, "run1"))
        conn.commit()
        conn.close()
        
        # Test Query
        emails = ["test@dacta.pe", "fail@dacta.pe", "missing@dacta.pe"]
        status_map = dbm.get_status_map(emails)
        
        self.assertEqual(status_map["test@dacta.pe"]['status'], 'SENT')
        self.assertEqual(status_map["fail@dacta.pe"]['status'], 'FAILED')
        self.assertTrue("missing@dacta.pe" not in status_map or status_map["missing@dacta.pe"]['status'] == 'PENDING')

    def test_db_manager_overwrite(self):
        # Insert FAILED then SENT
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        now1 = "2023-01-01 10:00:00"
        now2 = "2023-01-01 10:05:00"
        
        # Test overwriting logic on specific date
        fake_date = "2023-01-01"
        c.execute("INSERT INTO send_attempts VALUES (?,?,?,?,?,?,?)", 
                  ("1", "k", "overwrite@dacta.pe", "FAILED", "ERR", now1, "r1"))
        c.execute("INSERT INTO send_attempts VALUES (?,?,?,?,?,?,?)", 
                  ("2", "k", "overwrite@dacta.pe", "SENT", "OK", now2, "r2"))
        conn.commit()
        conn.close()
        
        status_map = dbm.get_status_map(["overwrite@dacta.pe"], target_date_str=fake_date)
        status_map = dbm.get_status_map(["overwrite@dacta.pe"], target_date_str=fake_date)
        # Should be SENT because logic prioritizes 'SENT' or latest?
        # My logic:
        # if status == 'SENT': map = SENT.
        # So yes, if any is SENT, it becomes SENT.
        self.assertEqual(status_map["overwrite@dacta.pe"]['status'], 'SENT')
        
        # Phase 4 Check: Rich Data
        self.assertIn('ts_raw', status_map["overwrite@dacta.pe"])
        self.assertEqual(status_map["overwrite@dacta.pe"]['ts_raw'], now2) # Should match the SENT timestamp

    def test_session_scoped_status(self):
        # Insert Old Record
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        old_time = "2023-01-01 10:00:00"
        c.execute("INSERT INTO send_attempts VALUES (?,?,?,?,?,?,?)", 
                  ("1", "k", "old@dacta.pe", "SENT", "OK", old_time, "r1"))
        conn.commit()
        conn.close()
        
        # 1. Query without filter (Resume Session scenario or No Min TS)
        # NOTE: get_status_map defaults to TODAY if no date provided.
        # Since our record is 2023, we must explicitly ask for that date to see it.
        res = dbm.get_status_map(["old@dacta.pe"], target_date_str="2023-01-01")
        self.assertEqual(res["old@dacta.pe"]['status'], 'SENT')
        
        # 2. Query with Future TS (New Upload / Reset Session scenario)
        # Should see PENDING (Empty map result means pending logic in app)
        future_ts = "2024-01-01 10:00:00"
        res_filtered = dbm.get_status_map(["old@dacta.pe"], min_timestamp=future_ts)
        # Should NOT contain the email (or return pending if logic inside dbm changes)
        # Current logic: returns only rows that match. So email key won't exist.
        self.assertNotIn("old@dacta.pe", res_filtered)

if __name__ == '__main__':
    unittest.main()
