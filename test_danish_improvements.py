import os
import sys
import unittest
import logging

# Helper to import from parent directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mailparser_reply import EmailReplyParser, EmailMessage
from mailparser_reply.constants import MAIL_LANGUAGE_DEFAULT

class EmailMessageTest(unittest.TestCase):
    def get_email(self, name: str, parse: bool = True, languages: list = None):
        """ Return EmailMessage instance or text content """
        # Adjust path for running from root or test dir
        path = f'test/emails/{name}.txt'
        if not os.path.exists(path):
            path = f'emails/{name}.txt'
            
        with open(path, encoding='utf-8') as f:
            text = f.read()
        return EmailReplyParser(
            languages=languages or [MAIL_LANGUAGE_DEFAULT]
        ).read(text) if parse else text

    def test_danish_gmail_header(self):
        mail = self.get_email('email_danish_3', parse=True, languages=['da'])
        # Should have 2 replies if header is detected
        if len(mail.replies) != 2:
            print(f"\n[FAIL] Gmail Header: Expected 2 replies, got {len(mail.replies)}")
            print(f"Replie 0 body: {mail.replies[0].body}")
        self.assertEqual(2, len(mail.replies))
        self.assertIn("Svar.", mail.replies[0].body)
        self.assertIn("Hej", mail.replies[1].body)

    def test_danish_outlook_separator(self):
        mail = self.get_email('email_danish_4', parse=True, languages=['da'])
        if len(mail.replies) != 2:
            print(f"\n[FAIL] Outlook Separator: Expected 2 replies, got {len(mail.replies)}")
            print(f"Replie 0 body: {mail.replies[0].body}")
        self.assertEqual(2, len(mail.replies))
        self.assertIn("Svar.", mail.replies[0].body)
        # Verify separator is removed/handled
        self.assertNotIn("-----Oprindelig meddelelse-----", mail.replies[0].body)
        self.assertIn("Hej", mail.replies[1].body)

    def test_danish_signatures_short(self):
        mail = self.get_email('email_danish_5', parse=True, languages=['da'])
        self.assertEqual(1, len(mail.replies))
        self.assertIn("Svar.", mail.replies[0].body)
        # Check if 'Kh' signature is detected (should fail currently)
        if "Kh\nPeter" in mail.replies[0].body:
             print(f"\n[FAIL] Signature 'Kh': Signature still in body")
        self.assertIn("Kh\nPeter", mail.replies[0].signatures)
        self.assertNotIn("Kh\nPeter", mail.replies[0].body)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    unittest.main()

