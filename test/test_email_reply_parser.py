import os
import sys
import unittest
import logging

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sys.path.append(root)
from mailparser_reply import EmailReplyParser
from mailparser_reply.constants import MAIL_LANGUAGE_DEFAULT


class EmailMessageTest(unittest.TestCase):
    def test_simple_body(self):
        mail = self.get_email('email_1_1', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("riak-users" in mail.replies[0].content)
        self.assertTrue("riak-users" in mail.replies[0].signatures)
        self.assertTrue("riak-users" not in mail.replies[0].body)

    def test_simple_quoted_body(self):
        mail = self.get_email('email_1_3', parse=True, languages=['en'])
        self.assertEqual(3, len(mail.replies))
        self.assertTrue("On 01/03/11 7:07 PM, Russell Brown wrote:" in mail.replies[1].content)
        self.assertTrue("On 01/03/11 7:07 PM, Russell Brown wrote:" not in mail.replies[1].body)
        self.assertTrue("-Abhishek Kona" in mail.replies[0].signatures)
        self.assertTrue("-Abhishek Kona" not in mail.replies[0].body)

        self.assertTrue("> Hi," == mail.replies[1].body)
        # test if matching quoted signatures works
        self.assertTrue(">> -Abhishek Kona" in mail.replies[2].content)
        self.assertTrue(">> -Abhishek Kona" in mail.replies[2].signatures)
        self.assertTrue(">> -Abhishek Kona" not in mail.replies[2].body)

    def test_simple_scrambled_body(self):
        mail = self.get_email('email_1_4', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("defunkt<reply@reply.github.com>" in mail.replies[1].content)
        self.assertTrue("defunkt<reply@reply.github.com>" in mail.replies[1].headers)

    def test_simple_longer_mail(self):
        mail = self.get_email('email_1_5', parse=True, languages=['en', 'de', 'david'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue(len(mail.latest_reply.split('\n')) == 15)

    def test_simple_scrambled_header(self):
        mail = self.get_email('email_1_6', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("<reply@reply.github.com>" in mail.replies[1].headers)

    def test_simple_scrambled_header2(self):
        mail = self.get_email('email_1_7', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("<notifications@github.com>wrote:" in mail.replies[1].headers)

    def test_simple_quoted_reply(self):
        mail = self.get_email('email_1_8', parse=True, languages=['en'])
        # TODO: Should this *actually* be the desired behaviour? tbh, nobody sends mails including this header tho
        #   Maybe otherwise: 1) Negative lookahead unquoted message
        #                    2) Unless message is disclaimer/signature (scan from behind)
        self.assertEqual(2, len(mail.replies))
        # self.assertTrue("--\nHey there, this is my signature" == mail.replies[1].signatures)

    def test_gmail_header(self):
        mail = self.get_email('email_2_1', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("Outlook with a reply\n\n\n------------------------------" == mail.replies[0].body)
        self.assertTrue("Google Apps Sync Team [mailto:mail-noreply@google.com]" in mail.replies[1].headers)
        self.assertTrue("Google Apps Sync Team [mailto:mail-noreply@google.com]" not in mail.replies[1].body)

    def test_gmail_indented(self):
        mail = self.get_email('email_2_3', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("Outlook with a reply above headers using unusual format" == mail.replies[0].body)
        # _normalize_body flattens the lines
        self.assertTrue("Ei tale aliquam eum, at vel tale sensibus, an sit vero magna. Vis no veri" in mail.replies[1].body)

    def test_complex_mail_thread(self):
        mail = self.get_email('email_3_1', parse=True, languages=['en', 'de', 'david'])
        self.assertEqual(5, len(mail.replies))

    def test_multiline_on(self):
        mail = self.get_email('multiline_on', parse=True, languages=['en', 'de'])
        self.assertEqual(4, len(mail.replies))

    def test_header_no_delimiter(self):
        mail = self.get_email('email_headers_no_delimiter', parse=True, languages=['en',])
        self.assertEqual(3, len(mail.replies))
        self.assertTrue("And another reply!" == mail.replies[0].body)
        self.assertTrue("A reply" == mail.replies[1].body)
        self.assertTrue("--\nSent from my iPhone" == mail.replies[1].signatures)
        self.assertTrue("This is a message.\nWith a second line." == mail.replies[2].body)

    def test_sent_from_junk1(self):
        mail = self.get_email('email_sent_from_iPhone', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email" == mail.replies[0].body)
        self.assertTrue("Sent from my iPhone" == mail.replies[0].signatures)

    def test_sent_from_junk2(self):
        mail = self.get_email('email_sent_from_multi_word_mobile_device', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email" == mail.replies[0].body)
        self.assertTrue("Sent from my Verizon Wireless BlackBerry" == mail.replies[0].signatures)

    def test_sent_from_junk3(self):
        mail = self.get_email('email_sent_from_BlackBerry', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email" == mail.replies[0].body)
        self.assertTrue("Sent from my BlackBerry" == mail.replies[0].signatures)

    def test_sent_from_junk4(self):
        mail = self.get_email('email_sent_from_not_signature', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email\n\nSent from my desk, is much easier than my mobile phone." == mail.replies[0].body)
        self.assertTrue("" == mail.replies[0].signatures)

    def get_email(self, name: str, parse: bool = True, languages: list = None):
        """ Return EmailMessage instance or text content """
        with open(f'emails/{name}.txt') as f:
            text = f.read()
        return EmailReplyParser(
            languages=languages or [MAIL_LANGUAGE_DEFAULT]
        ).read(text) if parse else text


# class EmailMessageTest(unittest.TestCase):
#     def test_simple_body(self):
#         message = self.get_email('email_1_1')
#
#         self.assertEqual(3, len(message.fragments))
#         self.assertEqual(
#             [False, True, True],
#             [f.signature for f in message.fragments]
#         )
#         self.assertEqual(
#             [False, True, True],
#             [f.hidden for f in message.fragments]
#         )
#         self.assertTrue("folks" in message.fragments[0].content)
#         self.assertTrue("riak-users" in message.fragments[2].content)
#
#     def test_reads_bottom_message(self):
#         message = self.get_email('email_1_2')
#
#         self.assertEqual(6, len(message.fragments))
#         self.assertEqual(
#             [False, True, False, True, False, False],
#             [f.quoted for f in message.fragments]
#         )
#
#         self.assertEqual(
#             [False, False, False, False, False, True],
#             [f.signature for f in message.fragments]
#         )
#
#         self.assertEqual(
#             [False, False, False, True, True, True],
#             [f.hidden for f in message.fragments]
#         )
#
#         self.assertTrue("Hi," in message.fragments[0].content)
#         self.assertTrue("On" in message.fragments[1].content)
#         self.assertTrue(">" in message.fragments[3].content)
#         self.assertTrue("riak-users" in message.fragments[5].content)
#
#     def test_reads_inline_replies(self):
#         message = self.get_email('email_1_8')
#         self.assertEqual(7, len(message.fragments))
#
#         self.assertEqual(
#             [True, False, True, False, True, False, False],
#             [f.quoted for f in message.fragments]
#         )
#
#         self.assertEqual(
#             [False, False, False, False, False, False, True],
#             [f.signature for f in message.fragments]
#         )
#
#         self.assertEqual(
#             [False, False, False, False, True, True, True],
#             [f.hidden for f in message.fragments]
#         )
#
#     def test_reads_top_post(self):
#         message = self.get_email('email_1_3')
#         self.assertEqual(5, len(message.fragments))
#
#     def test_multiline_reply_headers(self):
#         message = self.get_email('email_1_6')
#         self.assertTrue('I get' in message.fragments[0].content)
#         self.assertTrue('On' in message.fragments[1].content)
#
#     def test_captures_date_string(self):
#         message = self.get_email('email_1_4')
#
#         self.assertTrue('Awesome' in message.fragments[0].content)
#         self.assertTrue('On' in message.fragments[1].content)
#         self.assertTrue('Loader' in message.fragments[1].content)
#
#     def test_complex_body_with_one_fragment(self):
#         message = self.get_email('email_1_5')
#
#         self.assertEqual(1, len(message.fragments))
#
#     def test_verify_reads_signature_correct(self):
#         message = self.get_email('correct_sig')
#         self.assertEqual(2, len(message.fragments))
#
#         self.assertEqual(
#             [False, False],
#             [f.quoted for f in message.fragments]
#         )
#
#         self.assertEqual(
#             [False, True],
#             [f.signature for f in message.fragments]
#         )
#
#         self.assertEqual(
#             [False, True],
#             [f.hidden for f in message.fragments]
#         )
#
#         self.assertTrue('--' in message.fragments[1].content)
#
#     def test_deals_with_windows_line_endings(self):
#         msg = self.get_email('email_1_7')
#
#         self.assertTrue(':+1:' in msg.fragments[0].content)
#         self.assertTrue('On' in msg.fragments[1].content)
#         self.assertTrue('Steps 0-2' in msg.fragments[1].content)
#
#     def test_reply_is_parsed(self):
#         message = self.get_email('email_1_2')
#         self.assertTrue("You can list the keys for the bucket" in message.reply)
#
#     def test_reply_from_gmail(self):
#         with open('test/emails/email_gmail.txt') as f:
#             self.assertEqual('This is a test for inbox replying to a github message.',
#                              EmailReplyParser().parse_reply(f.read()))
#
#     def test_parse_out_just_top_for_outlook_reply(self):
#         with open('test/emails/email_2_1.txt') as f:
#             self.assertEqual("Outlook with a reply", EmailReplyParser().parse_reply(f.read()))
#
#     def test_parse_out_just_top_for_outlook_with_reply_directly_above_line(self):
#         with open('test/emails/email_2_2.txt') as f:
#             self.assertEqual("Outlook with a reply directly above line", EmailReplyParser().parse_reply(f.read()))
#
#     def test_parse_out_just_top_for_outlook_with_unusual_headers_format(self):
#         with open('test/emails/email_2_3.txt') as f:
#             self.assertEqual(
#                 "Outlook with a reply above headers using unusual format",
#                 EmailReplyParser().parse_reply(f.read()))
#
#     def test_sent_from_iphone(self):
#         with open('test/emails/email_iPhone.txt') as email:
#
#             self.assertTrue("Sent from my iPhone" not in EmailReplyParser().parse_reply(email.read()))
#
#     def test_email_one_is_not_on(self):
#         with open('test/emails/email_one_is_not_on.txt') as email:
#             self.assertTrue(
#                 "On Oct 1, 2012, at 11:55 PM, Dave Tapley wrote:" not in EmailReplyParser().parse_reply(email.read()))
#
#     def test_partial_quote_header(self):
#         message = self.get_email('email_partial_quote_header')
#         self.assertTrue("On your remote host you can run:" in message.reply)
#         self.assertTrue("telnet 127.0.0.1 52698" in message.reply)
#         self.assertTrue("This should connect to TextMate" in message.reply)
#
#     def test_email_headers_no_delimiter(self):
#         message = self.get_email('email_headers_no_delimiter')
#         self.assertEqual(message.reply.strip(), 'And another reply!')
#
#     def test_multiple_on(self):
#         message = self.get_email("greedy_on")
#         self.assertTrue(re.match('^On your remote host', message.fragments[0].content))
#         self.assertTrue(re.match('^On 9 Jan 2014', message.fragments[1].content))
#
#         self.assertEqual(
#             [False, True, False],
#             [fragment.quoted for fragment in message.fragments]
#         )
#
#         self.assertEqual(
#             [False, False, False],
#             [fragment.signature for fragment in message.fragments]
#         )
#
#         self.assertEqual(
#             [False, True, True],
#             [fragment.hidden for fragment in message.fragments]
#         )
#
#     def test_pathological_emails(self):
#         t0 = time.time()
#         message = self.get_email("pathological")
#         self.assertTrue(time.time() - t0 < 1, "Took too long")
#
#     def test_doesnt_remove_signature_delimiter_in_mid_line(self):
#         message = self.get_email('email_sig_delimiter_in_middle_of_line')
#         self.assertEqual(1, len(message.fragments))
#


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    unittest.main()
