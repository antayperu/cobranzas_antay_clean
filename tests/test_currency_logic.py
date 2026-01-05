
import unittest
import pandas as pd
from utils.helpers import safe_clean_decimal

class TestCurrencySep(unittest.TestCase):
    def test_clean_decimal(self):
        # Test cleaning logic isolated
        self.assertEqual(safe_clean_decimal("S/ 1,200.50"), 1200.50)
        self.assertEqual(safe_clean_decimal("$ 500.00"), 500.00)
        self.assertEqual(safe_clean_decimal("100"), 100.0)
        self.assertEqual(safe_clean_decimal(10.5), 10.5)
        self.assertEqual(safe_clean_decimal("invalid"), 0.0)

    def test_logic_separation(self):
        # Simulate logic from email_sender.py
        data = {
            'SALDO REAL': ["S/ 100.00", "$ 50.00", "S/ 200.00", "$ 20.00"],
            'MONEDA': ["S/", "US$", "S/.", "$"]
        }
        df = pd.DataFrame(data)
        
        # 1. Clean
        df['SALDO_CLEAN'] = df['SALDO REAL'].apply(safe_clean_decimal)
        
        # 2. Filter (Logic from email_sender)
        mask_soles = df['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
        
        df_sol = df[mask_soles]
        df_dol = df[~mask_soles]
        
        sum_s = df_sol['SALDO_CLEAN'].sum()
        sum_d = df_dol['SALDO_CLEAN'].sum()
        
        # Expected: Soles = 100 + 200 = 300
        # Expected: Dollars = 50 + 20 = 70
        
        self.assertEqual(sum_s, 300.0)
        self.assertEqual(sum_d, 70.0)
        
        print(f"Test Logic Success: Soles={sum_s}, Dollars={sum_d}")

if __name__ == '__main__':
    unittest.main()
