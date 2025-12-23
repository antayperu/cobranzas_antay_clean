import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import MagicMock, patch
from utils.email_sender import send_email_batch

class TestEmailGates(unittest.TestCase):
    
    def test_send_mail_called_once_per_client(self):
        """
        RC-QA: Validate that send_email_batch calls SMTP.send_message exactly once per unique message.
        """
        # Setup mock data (input format for send_email_batch)
        messages = [
            {
                'email': 'test@example.com',
                'subject': 'Asunto Test',
                'html_body': '<b>Hola</b>',
                'plain_body': 'Hola',
                'client_name': 'Cliente Test',
                'notification_key': 'KEY001'
            }
        ]
        
        smtp_config = {
            'server': 'smtp.test.com',
            'port': 587,
            'user': 'user@test.com',
            'password': 'password'
        }
        
        # Mock dependencies
        with patch('utils.email_sender.smtplib.SMTP') as mock_smtp, \
             patch('utils.email_sender.sqlite3.connect') as mock_db: # Mock DB to avoid file creation
            
            # Configure SMTP mock
            instance = mock_smtp.return_value
            instance.send_message.return_value = {}
            
            # Run function
            send_email_batch(
                smtp_config, 
                messages, 
                progress_callback=None, 
                logo_path=None, 
                force_resend=True # Force to bypass ledger for this unit test
            )
            
            # Assertions
            # Should be called once for send_message
            self.assertEqual(instance.send_message.call_count, 1)

    def test_deduplication_prevention(self):
        """
        RC-QA: Validate internally that duplicates in the same batch are skipped.
        """
        messages_dup = [
            {
                'email': 'dup@test.com', 'subject': 'S1', 'html_body': 'B1', 'client_name': 'C1', 
                'notification_key': 'SAME_KEY'
            },
            {
                'email': 'dup@test.com', 'subject': 'S1', 'html_body': 'B1', 'client_name': 'C1', 
                'notification_key': 'SAME_KEY' # Duplicate key
            }
        ]
        
        smtp_config = {'server': 's', 'port': 587, 'user': 'u', 'password': 'p'}
        
        with patch('utils.email_sender.smtplib.SMTP') as mock_smtp, \
             patch('utils.email_sender.sqlite3.connect') as mock_db:
             
            instance = mock_smtp.return_value
            
            stats = send_email_batch(smtp_config, messages_dup, force_resend=True)
            
            # Should only attempt to send 1, despite 2 in input list
            self.assertEqual(instance.send_message.call_count, 1)
            # Log should mention internal duplicate
            # We don't check log content strictly here, but call count validates logic.

if __name__ == '__main__':
    unittest.main()
