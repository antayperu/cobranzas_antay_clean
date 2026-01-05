import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.email_sender import send_email_batch

class TestEmailGates(unittest.TestCase):
    
    def setUp(self):
        # Clean DB before each test
        if os.path.exists("email_ledger.db"):
            os.remove("email_ledger.db")
            
        self.smtp_config = {
            "server": "smtp.test.com", 
            "port": 587, 
            "user": "test@dacta.pe", 
            "password": "xxx"
        }

    def test_exactly_once_sending(self):
        """Verify that 1 message in list = 1 SMTP call (Idempotency Base)"""
        messages = [{
            'email': 'client@test.com',
            'client_name': 'Cliente Test',
            'subject': 'Asunto',
            'html_body': '<h1>Hola</h1>',
            'plain_body': 'Hola'
        }]
        
        with patch("smtplib.SMTP") as mock_smtp:
            instance = mock_smtp.return_value
            send_email_batch(self.smtp_config, messages)
            
            # Assertions
            instance.send_message.assert_called_once()
            
    def test_ttl_blocking(self):
        """Verify that sending the same message twice is blocked by TTL"""
        msg = {
            'email': 'client@test.com',
            'client_name': 'Cliente Test',
            'subject': 'Asunto TTL',
            'html_body': '<h1>Hola</h1>',
            'plain_body': 'Hola'
        }
        
        with patch("smtplib.SMTP") as mock_smtp:
            instance = mock_smtp.return_value
            
            # First Send
            stats1 = send_email_batch(self.smtp_config, [msg])
            self.assertEqual(stats1['success'], 1)
            
            # Second Send (Immediate)
            stats2 = send_email_batch(self.smtp_config, [msg])
            self.assertEqual(stats2['success'], 0)
            self.assertEqual(stats2['blocked'], 1)

    def test_supervisor_copy_bcc(self):
        """RC-FEAT-011: Verify Supervisor receives copy via BCC (Envelope only)"""
        msg = {'email': 'client@test.com', 'client_name': 'C', 'subject': 'S', 'html_body': 'B'}
        
        supervisor_cfg = {
            "email": "boss@test.com", 
            "enabled": True, 
            "mode": "BCC"
        }
        
        with patch("smtplib.SMTP") as mock_smtp:
            instance = mock_smtp.return_value
            send_email_batch(self.smtp_config, [msg], supervisor_config=supervisor_cfg)
            
            # Verify send_message arguments
            call_args = instance.send_message.call_args
            sent_msg = call_args[0][0] # The MIME message object
            sent_to_addrs = call_args[1]['to_addrs'] # The envelope recipients
            
            # Envelope MUST include both client and supervisor
            self.assertIn('client@test.com', sent_to_addrs)
            self.assertIn('boss@test.com', sent_to_addrs)
            
            # Header 'To' must be client
            self.assertEqual(sent_msg['To'], 'client@test.com')
            
            # Header 'Cc' must NOT be present (Strict BCC)
            self.assertIsNone(sent_msg['Cc'])

    def test_supervisor_copy_cc(self):
        """RC-FEAT-011: Verify Supervisor receives copy via CC (Envelope + Header)"""
        msg = {'email': 'client@test.com', 'client_name': 'C', 'subject': 'S', 'html_body': 'B'}
        
        supervisor_cfg = {
            "email": "boss@test.com", 
            "enabled": True, 
            "mode": "CC"
        }
        
        with patch("smtplib.SMTP") as mock_smtp:
            instance = mock_smtp.return_value
            send_email_batch(self.smtp_config, [msg], supervisor_config=supervisor_cfg)
            
            call_args = instance.send_message.call_args
            sent_msg = call_args[0][0]
            sent_to_addrs = call_args[1]['to_addrs']
            
            # Envelope includes both
            self.assertIn('client@test.com', sent_to_addrs)
            self.assertIn('boss@test.com', sent_to_addrs)
            
            # Header Cc IS present
            self.assertEqual(sent_msg['Cc'], 'boss@test.com')

    def test_supervisor_disabled(self):
        """RC-FEAT-011: Verify no copy if disabled"""
        msg = {'email': 'client@test.com', 'client_name': 'C', 'subject': 'S', 'html_body': 'B'}
        
        supervisor_cfg = {
            "email": "boss@test.com", 
            "enabled": False, 
            "mode": "BCC"
        }
        
        with patch("smtplib.SMTP") as mock_smtp:
            instance = mock_smtp.return_value
            send_email_batch(self.smtp_config, [msg], supervisor_config=supervisor_cfg)
            
            call_args = instance.send_message.call_args
            sent_to_addrs = call_args[1]['to_addrs']
            
            # Envelope includes ONLY client
            self.assertIn('client@test.com', sent_to_addrs)
            self.assertNotIn('boss@test.com', sent_to_addrs)

    def test_force_resend_with_supervisor(self):
        """RC-FEAT-011: Verify override works and still copies supervisor"""
        msg = {'email': 'client@test.com', 'client_name': 'C', 'subject': 'S', 'html_body': 'B'}
        supervisor_cfg = {"email": "boss@test.com", "enabled": True, "mode": "BCC"}
        
        with patch("smtplib.SMTP") as mock_smtp:
            instance = mock_smtp.return_value
            
            # First send
            send_email_batch(self.smtp_config, [msg], supervisor_config=supervisor_cfg)
            
            # Second send FORCED
            stats = send_email_batch(self.smtp_config, [msg], force_resend=True, supervisor_config=supervisor_cfg)
            
            self.assertEqual(stats['success'], 1)
            self.assertEqual(stats['blocked'], 0)
            
            # Verify verification calls (should be 2 total calls)
            self.assertEqual(instance.send_message.call_count, 2)

if __name__ == '__main__':
    unittest.main()
