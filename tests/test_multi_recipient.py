import unittest
from utils.helpers import normalize_emails

class TestMultiRecipient(unittest.TestCase):
    def test_single_email(self):
        """Caso base: un solo correo"""
        self.assertEqual(normalize_emails("test@example.com"), ["test@example.com"])

    def test_comma_separated(self):
        """Caso principal: separación por comas"""
        input_str = "user1@test.com, user2@test.com"
        expected = ["user1@test.com", "user2@test.com"]
        self.assertEqual(normalize_emails(input_str), expected)

    def test_semicolon_separated(self):
        """Caso Excel: separación por punto y coma"""
        input_str = "user1@test.com; user2@test.com"
        expected = ["user1@test.com", "user2@test.com"]
        self.assertEqual(normalize_emails(input_str), expected)

    def test_mixed_separators_and_whitespace(self):
        """Caso sucio: mezcla de separadores y espacios"""
        input_str = "  user1@test.com , user2@test.com;user3@test.com  "
        expected = ["user1@test.com", "user2@test.com", "user3@test.com"]
        self.assertEqual(normalize_emails(input_str), expected)
        
    def test_deduplication(self):
        """Caso seguridad: no enviar doble al mismo"""
        input_str = "user1@test.com, user1@test.com"
        expected = ["user1@test.com"]
        self.assertEqual(normalize_emails(input_str), expected)

if __name__ == '__main__':
    unittest.main()
