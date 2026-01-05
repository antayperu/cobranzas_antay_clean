
import pandas as pd

def clean_key_part(val):
    return str(val).strip()

def build_match_key_ctas(row):
    # Logic currently in processing.py
    return clean_key_part(row.get('coddoc', '')) + clean_key_part(row.get('sersun', '')) + clean_key_part(row.get('numsun', ''))

def build_match_key_cobranza(row):
    # Logic currently in processing.py
    return clean_key_part(row.get('coddoc', '')) + clean_key_part(row.get('numsun', ''))

# Case: Standard Invoice
# Ctas: 01, F001, 00002541
# Cobranza: 01, F001-00002541 (Common format in SUNAT systems)

row_ctas = {'coddoc': '01', 'sersun': 'F001', 'numsun': '00002541'}
row_cob = {'coddoc': '01', 'numsun': 'F001-00002541'}

key_ctas = build_match_key_ctas(row_ctas)
key_cob = build_match_key_cobranza(row_cob)

print(f"--- SCENARIO 1 (Current Logic) ---")
print(f"Ctas Data: {row_ctas}")
print(f"Cob Data:  {row_cob}")
print(f"Key Ctas: '{key_ctas}'")
print(f"Key Cob:  '{key_cob}'")
print(f"MATCH?:   {key_ctas == key_cob}")

# Case: Improved Logic (Removing dashes)
def clean_key_part_enhanced(val):
    return str(val).strip().replace("-", "").replace(" ", "")

def build_key_ctas_enhanced(row):
    return clean_key_part_enhanced(row.get('coddoc', '')) + clean_key_part_enhanced(row.get('sersun', '')) + clean_key_part_enhanced(row.get('numsun', ''))

def build_key_cob_enhanced(row):
    return clean_key_part_enhanced(row.get('coddoc', '')) + clean_key_part_enhanced(row.get('numsun', ''))

key_ctas_v2 = build_key_ctas_enhanced(row_ctas)
key_cob_v2 = build_key_cob_enhanced(row_cob)

print(f"\n--- SCENARIO 2 (Enhanced Logic) ---")
print(f"Key Ctas V2: '{key_ctas_v2}'")
print(f"Key Cob V2:  '{key_cob_v2}'")
print(f"MATCH?:      {key_ctas_v2 == key_cob_v2}")
