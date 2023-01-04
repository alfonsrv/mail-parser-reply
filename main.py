# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def get_mail(name: str):
    with open('test/emails/%s.txt' % name) as f:
        return f.read()

x = get_mail('delete')
from mailparser_reply.parser import EmailReplyParser
p = EmailReplyParser(languages='en')
f = p.read(x)
