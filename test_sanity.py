import sys
import os
import pandas as pd
sys.path.append(os.getcwd())

from utils.processing import format_phone, format_client_code

# Test helpers
print("Testing helpers...")
assert format_phone(None) == ""
assert format_phone("999999999") == "+51999999999"
assert format_phone("51999999999") == "+51999999999"
assert format_phone("(01) 123-4567") == "+51011234567"
print("Helpers OK")

# Test client code
assert format_client_code(123) == "000123"
assert format_client_code("123") == "000123"
print("Client Code OK")

print("Imports OK")
