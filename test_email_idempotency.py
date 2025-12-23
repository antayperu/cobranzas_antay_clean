import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

# Ensure modules are loaded
import utils.email_sender 
from utils.email_sender import send_email_batch

class TestEmailIdempotency(unittest.TestCase):
    
    def setUp(self):
        self.smtp_config = {
            'server': 'smtp.test.com',
            'port': 587,
            'user': 'test@test.com',
            'password': 'password'
        }
        self.messages = [
            {
                'email': 'client@test.com', 
                'subject': 'Test Subject', 
                'html_body': '<p>Body</p>', 
                'client_name': 'Test Client',
                'notification_key': 'KEY1'
            }
        ]

    # Patch where the class is defined/used. Since send_email_batch imports smtplib inside,
    # we patch smtplib.SMTP globally or we ensure we patch what it uses.
    # The safest is patching 'smtplib.SMTP' if we can.
    @patch('smtplib.SMTP')
    @patch('utils.email_sender.sqlite3')
    def test_send_success_fresh(self, mock_sqlite, mock_smtp_cls):
        """Test sending a fresh email works and updates ledger."""
        
        # Setup Mock SMTP
        mock_server_instance = MagicMock()
        mock_smtp_cls.return_value = mock_server_instance
        
        # Setup Mock DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Check Ledger -> Returns None (Not found)
        mock_cursor.fetchone.return_value = None 
        
        stats = send_email_batch(self.smtp_config, self.messages)
        
        if stats['success'] != 1:
            print("\nDEBUG LOGS:", stats['log'])
            
        self.assertEqual(stats['success'], 1)
        self.assertEqual(stats['blocked'], 0)
        
        # Verify SMTP send_message called
        self.assertTrue(mock_server_instance.send_message.called)
        
        # Verify Insert called
        self.assertTrue(any("INSERT INTO send_attempts" in str(call) for call in mock_cursor.execute.mock_calls))


    @patch('smtplib.SMTP')
    @patch('utils.email_sender.sqlite3')
    def test_block_ttl(self, mock_sqlite, mock_smtp_cls):
        """Test immediate resend is blocked by TTL."""
        
        from datetime import datetime
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Ledger returns a RECENT timestamp (1 min ago)
        recent_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
        mock_cursor.fetchone.return_value = (recent_ts,)
        
        stats = send_email_batch(self.smtp_config, self.messages)
        
        if stats['blocked'] != 1:
             print("\nDEBUG LOGS (TTL):", stats['log'])

        self.assertEqual(stats['success'], 0)
        self.assertEqual(stats['blocked'], 1)
        
        # Verify NO SMTP called
        mock_server_instance = mock_smtp_cls.return_value
        self.assertFalse(mock_server_instance.send_message.called)


    @patch('smtplib.SMTP')
    @patch('utils.email_sender.sqlite3')
    def test_force_resend(self, mock_sqlite, mock_smtp_cls):
        """Test force_resend bypasses TTL."""
        
        from datetime import datetime
        
        mock_server_instance = MagicMock()
        mock_smtp_cls.return_value = mock_server_instance
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Ledger returns a RECENT timestamp
        recent_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
        mock_cursor.fetchone.return_value = (recent_ts,)
        
        # Force Resend = True
        stats = send_email_batch(self.smtp_config, self.messages, force_resend=True)
        
        self.assertEqual(stats['success'], 1)
        self.assertEqual(stats['blocked'], 0)
        self.assertTrue(mock_server_instance.send_message.called)


    @patch('smtplib.SMTP')
    @patch('utils.email_sender.sqlite3')
    def test_multi_client_same_email(self, mock_sqlite, mock_smtp_cls):
        """Test RC-BUG-016: Multiple clients with same email should trigger distinct sends."""
        
        mock_server_instance = MagicMock()
        mock_smtp_cls.return_value = mock_server_instance
        
        msgs = [
            {'email': 'shared@test.com', 'notification_key': 'KEY_CLIENT_A', 'subject': 'A', 'html_body': 'A', 'client_name': 'Client A'},
            {'email': 'shared@test.com', 'notification_key': 'KEY_CLIENT_B', 'subject': 'B', 'html_body': 'B', 'client_name': 'Client B'}
        ]
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None # No prev sends
        
        stats = send_email_batch(self.smtp_config, msgs)
        
        self.assertEqual(stats['success'], 2) 
        self.assertEqual(stats['blocked'], 0)
        self.assertEqual(mock_server_instance.send_message.call_count, 2)

if __name__ == '__main__':
    unittest.main()
