
import unittest
from unittest.mock import MagicMock, patch, ANY
import os
import sys

# Add root to path so we can import utils
sys.path.append(os.getcwd())

import utils.email_sender as es
import utils.qa_mode as qa_lib

class TestEmailLogic(unittest.TestCase):

    def setUp(self):
        # Base Config for SMTP
        self.smtp_config = {
            'server': 'smtp.test.com',
            'port': '587',
            'user': 'sender@test.com',
            'password': 'password'
        }
        
        # Sample Message Data
        self.msg_data = {
            'email': 'client@client.com',
            'client_name': 'Cliente Real',
            'subject': 'Estado de Cuenta',
            'html_body': '<p>Hola Cliente</p>',
            'plain_body': 'Hola Cliente',
            'notification_key': 'key_123'
        }

    @patch('utils.email_sender.smtplib.SMTP')
    @patch('utils.email_sender.sqlite3.connect')
    def test_qa_mode_enabled(self, mock_sqlite, mock_smtp_cls):
        """
        Test that QA Mode overrides recipients, subject and headers, 
        and ignores production copies.
        """
        # --- Setup Mocks ---
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        
        # Mock DB to avoid file creation
        mock_conn = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None # No TTL block

        # --- QA Configuration ---
        qa_settings = {
            'enabled': True,
            'mode': 'ALL',
            'recipients': ['qa@test.com'],
            'cc_recipients': ['qa_cc@test.com'],
            'bcc_recipients': ['qa_bcc@test.com']
        }
        
        # Internal Copies (Should be IGNORED in QA)
        internal_copies = {
            'cc_list': ['prod_cc@company.com'],
            'bcc_list': ['prod_bcc@company.com']
        }

        # --- Prepare Message (Simulate app.py processing) ---
        # In app.py, the message is modified BEFORE passing to batch if QA is on.
        # So we must simulate that transformation here to test the full flow or 
        # test send_email_batch's handling of the *envelope* specifically.
        # send_email_batch is responsible for the Headers (CC) and Envelope assembly.
        
        # Let's simulate what app.py does:
        # 1. Resolve Recipients
        qa_recips, _, is_qa = qa_lib.resolve_recipients(self.msg_data['email'], qa_settings)
        # 2. Modify Msg Data
        msg_payload = self.msg_data.copy()
        msg_payload['email'] = qa_recips # ['qa@test.com']
        msg_payload['subject'] = qa_lib.modify_subject_for_qa(msg_payload['subject'])
        msg_payload['html_body'] = qa_lib.get_qa_banner_html('client@client.com', qa_recips) + msg_payload['html_body']

        # --- Execute ---
        results = es.send_email_batch(
            self.smtp_config,
            [msg_payload],
            qa_settings=qa_settings, # Pass QA settings
            internal_copies_config=internal_copies # Pass Prod copies (to verify ignorance)
        )

        # --- Assertions ---
        
        # 1. Verify SMTP Connection
        mock_server.starttls.assert_called()
        mock_server.login.assert_called_with('sender@test.com', 'password')
        
        # 2. Verify SendMail Call (The Envelope)
        # Expected Envelope: QA_TO + QA_CC + QA_BCC
        # Prod copies/Client email should NOT be here.
        expected_envelope = {'qa@test.com', 'qa_cc@test.com', 'qa_bcc@test.com'}
        
        # The implementation uses send_message(msg, to_addrs=...)
        self.assertTrue(mock_server.send_message.called, "send_message should be called")
        
        args, kwargs = mock_server.send_message.call_args
        msg_obj = args[0]
        to_addrs = kwargs.get('to_addrs')
        
        self.assertEqual(set(to_addrs), expected_envelope)
        
        # 3. Verify Message Content (Headers)
        # Subject should have QA prefix
        self.assertIn("[QA - MARCHA BLANCA]", msg_obj['Subject'])
        # Cc Header should ONLY have QA CC
        self.assertEqual(msg_obj['Cc'], "qa_cc@test.com")
        
        # Body verification (Banner)
        # Search for HTML part
        html_part = None
        for part in msg_obj.walk():
            if part.get_content_type() == "text/html":
                html_part = part
                break
        
        self.assertIsNotNone(html_part, "Should have a text/html part")
        body_content = html_part.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        self.assertIn("PRUEBA INTERNA", body_content)
        self.assertNotIn("prod_cc@company.com", body_content)
        
        print("\n✅ Test QA Mode: PASSED")

    @patch('utils.email_sender.smtplib.SMTP')
    @patch('utils.email_sender.sqlite3.connect')
    def test_production_mode_copies(self, mock_sqlite, mock_smtp_cls):
        """
        Test that Production Mode respects Internal Copies (CC/BCC).
        """
        # --- Setup Mocks ---
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        
        mock_conn = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        # --- Prod Configuration ---
        # QA Disabled
        qa_settings = {'enabled': False} 
        
        # Internal Copies
        internal_copies = {
            'cc_list': ['boss@company.com'],
            'bcc_list': ['audit@company.com']
        }

        # --- Execute ---
        # No app.py transformation for Prod
        results = es.send_email_batch(
            self.smtp_config,
            [self.msg_data],
            qa_settings=qa_settings,
            internal_copies_config=internal_copies
        )

        # --- Assertions ---
        
        # 1. Envelope should include: Client + CC + BCC
        expected_envelope = {'client@client.com', 'boss@company.com', 'audit@company.com'}
        
        self.assertTrue(mock_server.send_message.called)
        args, kwargs = mock_server.send_message.call_args
        msg_obj = args[0]
        to_addrs = kwargs.get('to_addrs')
        
        self.assertEqual(set(to_addrs), expected_envelope)
        
        # 2. Verify Headers
        self.assertEqual(msg_obj['Subject'], "Estado de Cuenta")
        
        # Verify Body (No Banner)
        html_part = None
        for part in msg_obj.walk():
            if part.get_content_type() == "text/html":
                html_part = part
                break
        
        if html_part:
            body_content = html_part.get_payload(decode=True).decode('utf-8', errors='ignore')
            self.assertNotIn("MARCHA BLANCA", body_content)
        
        # Cc Header present
        self.assertIn("boss@company.com", msg_obj['Cc'])
        # Bcc Header should NOT be present (MIME standard)
        self.assertIsNone(msg_obj['Bcc'])

        print("\n✅ Test Production Mode: PASSED")

if __name__ == '__main__':
    unittest.main()
