# Copyright (c) 2023 – RAUSYS, Rau Systemberatung GmbH

import logging
import re
from dataclasses import dataclass, field
from itertools import chain
from typing import Union, List, Optional, Tuple

from typing import Pattern

from .constants import MAIL_LANGUAGES, MAIL_LANGUAGE_DEFAULT, OUTLOOK_MAIL_SEPARATOR, QUOTED_REMOVAL_REGEX, \
    SINGLE_SPACE_VARIATIONS, SENTENCE_START, OPTIONAL_LINEBREAK, DEFAULT_SIGNATURE_REGEX, QUOTED_MATCH_INCLUDE, \
    GENERIC_MAIL_SEPARATOR

logger = logging.getLogger(__name__)


@dataclass
class EmailReplyParser:
    """ Easy EmailMessage parsing interface """
    languages: List[str] = field(default_factory=lambda: [])
    default_language: str = MAIL_LANGUAGE_DEFAULT

    def __post_init__(self):
        self.languages = [language.lower().strip() for language in self.languages]
        self.languages = [language for language in self.languages if language in MAIL_LANGUAGES]
        if not self.languages:
            self.languages = [self.default_language]

    def read(self, text: str) -> 'EmailMessage':
        """ Factory method that splits email into list of fragments
            text - A string email body"""
        return EmailMessage(text=text, languages=self.languages).read()

    def parse_reply(self, text: str) -> Union[str, None]:
        """ Provides the latest reply portion of email.
        text - A string email body """
        return self.read(text).latest_reply


@dataclass
class EmailMessage:
    """ An email message represents a parsed email body. """

    #: Email message text body
    text: str

    #: Languages used to detect common mail client email headers, separating replies.
    #: This is used to fragment the mail into its single replies.
    languages: List[str] = field(default_factory=lambda: [])

    #: Standalone replies mail is made out of
    replies: List['EmailReply'] = field(default_factory=lambda: [])

    #: Whether to automatically include English versions too; desirable in multi-language environments
    include_english: bool = True

    #: Whether to remove quotes on standalone replies (aka replies, that do not *include* quoted content,
    #: but are completely quoted by themselves)
    remove_quotes_replies: bool = False  # TODO: Implement?

    #: Fallback language when other languages don't have dict entry
    default_language: str = MAIL_LANGUAGE_DEFAULT
    _header_regex: Union[Pattern, None] = None
    _disclaimers_regex: Union[Pattern, None] = None
    _signature_regex: Union[Pattern, None] = None

    def __post_init__(self):
        if self.include_english and 'en' not in self.languages:
            self.languages.append('en')
        self._normalize_text()

    def __str__(self):
        return self.text

    def __repr__(self):
        return f'<EmailMessage {self.languages=} {len(self.replies)} replies,>'

    @property
    def latest_reply(self) -> Union[str, None]:
        """ Captures the latest reply message within email """
        if not self.replies: return None
        return self.replies[0].content

    def _get_language_regex(self, language: str, regex_key: str) -> str:
        """ Returns the language-specific regex pattern; if no pattern is available
         for the language it falls back to the default_language's regex """
        flat_list = lambda x: '|'.join(chain(x)) if isinstance(x, list) else x

        if language in MAIL_LANGUAGES.keys():
            if regex_key in MAIL_LANGUAGES[language].keys():
                return flat_list(MAIL_LANGUAGES[language][regex_key])

        if self.default_language in self.languages: return ''
        # Fallback; language does not have regex_key defined; use global fallback language's regex key
        return flat_list(MAIL_LANGUAGES[self.default_language][regex_key])

    @property
    def DISCLAIMERS_REGEX(self) -> Pattern:
        """ Compile regex to remove disclaimers at the end of the mail """
        if self._disclaimers_regex: return self._disclaimers_regex

        ALLOW_ANY_EXTENSION = r'[a-zA-Z0-9\u00C0-\u017F:;.,?!<>()@&/\'\"\“\” \u200b\xA0\t\-]*'
        disclaimers = [self._get_language_regex(language=language, regex_key='disclaimers') for language in self.languages]
        disclaimers = '|'.join([
            disclaimer for disclaimer in disclaimers if disclaimer
        ]).replace(' ', SINGLE_SPACE_VARIATIONS)

        self._disclaimers_regex = re.compile(
            f'{SENTENCE_START}(?:{disclaimers})(?:{OPTIONAL_LINEBREAK}{ALLOW_ANY_EXTENSION}?(?:mail){ALLOW_ANY_EXTENSION}){{1,2}}',
            flags=re.MULTILINE | re.IGNORECASE
        )
        logger.debug(f'Mail Disclaimer RegEx: "{self._disclaimers_regex.pattern!r}"')
        return self._disclaimers_regex

    @property
    def HEADER_REGEX(self) -> Pattern:
        """ Helper function to build the regex used for detecting headers  """
        if self._header_regex: return self._header_regex
        regex_headers = [self._get_language_regex(language=language, regex_key='wrote_header') for language in self.languages]
        regex_headers += [self._get_language_regex(language=language, regex_key='from_header') for language in self.languages]
        regex_headers.append(f'({GENERIC_MAIL_SEPARATOR})')
        regex_headers = '|'.join([header for header in regex_headers if header])
        self._header_regex = re.compile(regex_headers, flags=re.MULTILINE | re.IGNORECASE)
        logger.debug(f'Mail Header RegEx: "{self._header_regex.pattern!r}"')
        return self._header_regex

    @property
    def SIGNATURE_REGEX(self) -> Pattern:
        if self._signature_regex: return self._signature_regex
        sent_from_regex = [self._get_language_regex(language=language, regex_key='sent_from') for language in self.languages]
        sent_from_regex = '|'.join([header for header in sent_from_regex if header])
        signatures = [self._get_language_regex(language=language, regex_key='signatures') for language in self.languages]
        signatures = '|'.join([header for header in signatures if header])

        # Matches the following signatures – when a signature is matched it's considered to move all the way
        # until the end of the mail body. Might be dangerous; but honestly how github/email_reply_parser works too
        #   1) Outlook-style signatures
        #   2) Idiot-filter phone email_reply_parser "Sent from my ..." (usually 1-3 words)
        #   3) Get Outlook for... / Sent from Outlook for iOS<https://greed.com">
        #   4) Regular signature-indicating stuff; e.g. "Best regards, ..."
        # TODO: Add quotation as optional matching
        self._signature_regex = re.compile(
            fr'(({DEFAULT_SIGNATURE_REGEX}|{OUTLOOK_MAIL_SEPARATOR}|' +   # 1)
            fr'\s*^{QUOTED_MATCH_INCLUDE}(?:{sent_from_regex}) ?(?:(?:[\w.<>:// ]+)|(?:\w+ ){1,3})$|'+  # 2) + 3)
            fr'(?<!\A)^{QUOTED_MATCH_INCLUDE}(?:{signatures}))(.|\s)*)',  # 4)
            flags=re.MULTILINE | re.IGNORECASE
        )
        logger.debug(f'Mail Signature RegEx: "{self._signature_regex.pattern!r}"')

        # TODO: Always match whole signature until the next fragment/regex or until end of text
        return self._signature_regex

    def _normalize_text(self):
        # Normalize Line Endings
        self.text = self.text.replace("\r\n", "\n")
        # Remove invisible characters and dead line-beginnings/-endings
        self.text = '\n'.join([line.strip() for line in self.text.split('\n')])

        # Some users may reply directly above a line of underscores.
        # In order to ensure that these fragments are split correctly, make sure that all lines
        # of underscores are preceded by at least two newline characters.
        #   See email_2_2.txt for an example
        self.text = re.sub(f'([^\n]){OUTLOOK_MAIL_SEPARATOR}', '\\1\n', self.text, re.MULTILINE)

    def _process_signatures_disclaimers(self, text: str) -> Tuple[List[str], str]:
        """ Identifies Signature Elements and Disclaimers """
        disclaimers = self.DISCLAIMERS_REGEX.findall(text)
        signatures = self.SIGNATURE_REGEX.search(text)
        return disclaimers, signatures.group() if signatures else ''

    def read(self):
        """ Processes mail text body, splitting it up in distinct, digestible EmailReplies
         based on headers separating mail replies/mail parts """

        # Find all headers in mail body and convert to flat list
        headers = self.HEADER_REGEX.findall(self.text)
        headers = [header for header in chain.from_iterable(headers) if header]

        current_position = 0
        previous_header = ''

        # Delimits eMail body by headers
        for header in headers:
            position = self.text.find(
                header,
                current_position + 1 if current_position > 0 else current_position
            )

            disclaimers, signatures = self._process_signatures_disclaimers(self.text[current_position:position])

            _reply = EmailReply(
                headers=previous_header,
                content=self.text[current_position:position],
                signatures=signatures,
                disclaimers=disclaimers
            )
            current_position = position if position >= 0 else 0
            previous_header = header
            if not _reply.content: continue
            self.replies.append(_reply)

        # Add last reply element that is otherwise skipped due to the way we're iterating over headers.
        # This also adds the message body as a whole, in case there are no email headers at all
        disclaimers, signatures = self._process_signatures_disclaimers(self.text[current_position:])
        _reply = EmailReply(
            headers=previous_header,
            content=self.text[current_position:],
            signatures=signatures,
            disclaimers=disclaimers
        )
        self.replies.append(_reply)

        return self


@dataclass
class EmailReply:
    """ A reply is a standalone part of an Email Message, including headers, body, signatures and disclaimers """

    #: Unprocessed mail text body
    content: str

    #: Headers element within text body
    headers: Optional[str] = ''
    #: Signature element within text body
    signatures: Optional[str] = ''
    #: Disclaimers within text body
    disclaimers: Optional[List[str]] = field(default_factory=lambda: [])

    def __post_init__(self):
        self.content = self.content.strip()
        self.headers = self.headers.strip()
        self.signatures = self.signatures.strip()
        self.disclaimers = [d.strip() for d in self.disclaimers]

    def __str__(self):
        return self.full_body

    def __repr__(self):
        return f'<EmailReply: {str(self)[:64] + "..." if len(str(self)) > 64 else str(self)}'

    @property
    def body(self) -> str:
        """ Returns the message's body without the headers, signatures and disclaimers """
        _body = self.content
        for disclaimer in self.disclaimers:
            _body = _body.replace(disclaimer, '')
        if self.signatures:
            _body = _body.replace(self.signatures, '')
        return _body.replace(self.headers or '', '').strip()

    @property
    def full_body(self) -> str:
        """ Returns the message's body without the headers, but with signatures and disclaimers """
        return self.content.replace(self.headers or '', '').strip()
