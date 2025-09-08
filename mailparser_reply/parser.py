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

from functools import lru_cache
def _get_language_regex_patterns(languages: Tuple[str, ...], regex_key: str, default_language: str) -> List[str]:
    """Helper to get all language-specific regex patterns for a given key."""
    patterns = []
    
    def flat_list(x):
        return '|'.join(chain(x)) if isinstance(x, list) else x

    for lang in languages:
        if lang in MAIL_LANGUAGES and regex_key in MAIL_LANGUAGES[lang]:
            patterns.append(flat_list(MAIL_LANGUAGES[lang][regex_key]))

    # Fallback to default language if the key is missing for all specified languages
    if not patterns and default_language not in languages:
        if default_language in MAIL_LANGUAGES and regex_key in MAIL_LANGUAGES[default_language]:
            patterns.append(flat_list(MAIL_LANGUAGES[default_language][regex_key]))
            
    return [p for p in patterns if p]

@lru_cache(maxsize=128)
def get_disclaimers_regex(languages: Tuple[str, ...], default_language: str) -> Pattern:
    """Compiles and caches the disclaimer regex for a given set of languages."""
    ALLOW_ANY_EXTENSION = r'[a-zA-Z0-9\u00C0-\u017F:;.,?!<>()@&/\'\"\“\” \u200b\xA0\t\-]*'
    disclaimers = _get_language_regex_patterns(languages, 'disclaimers', default_language)
    disclaimers_pattern = '|'.join(disclaimers).replace(' ', SINGLE_SPACE_VARIATIONS)
    
    regex = re.compile(
        f'{SENTENCE_START}(?:{disclaimers_pattern})(?:{OPTIONAL_LINEBREAK}{ALLOW_ANY_EXTENSION}?(?:mail){ALLOW_ANY_EXTENSION}){{1,2}}',
        flags=re.MULTILINE | re.IGNORECASE
    )
    logger.debug(f'Compiled Disclaimer RegEx for {languages}: "{regex.pattern!r}"')
    return regex

@lru_cache(maxsize=128)
def get_header_regex(languages: Tuple[str, ...], default_language: str) -> Pattern:
    """
    Compiles and caches the header regex for a given set of languages.
    **UPDATED**: Now handles common leading characters like *, >, and spaces.
    """
    wrote_headers = _get_language_regex_patterns(languages, 'wrote_header', default_language)
    from_headers = _get_language_regex_patterns(languages, 'from_header', default_language)
    
    # Combine language-specific headers
    lang_headers = wrote_headers + from_headers
    
    # Prepend a pattern to each rule to optionally match leading characters.
    # This allows it to match "> From:" or "* From:" etc.
    prefixed_lang_headers = [f'(?:^[\\s*>-]*)({h})' for h in lang_headers]
    
    # The generic separator should match exactly, without prefixes
    all_headers = prefixed_lang_headers + [f'({GENERIC_MAIL_SEPARATOR})']
    
    headers_pattern = '|'.join(filter(None, all_headers))

    regex = re.compile(headers_pattern, flags=re.MULTILINE | re.IGNORECASE)
    logger.debug(f'Compiled Header RegEx for {languages}: "{regex.pattern!r}"')
    return regex

@lru_cache(maxsize=128)
def get_signature_regex(languages: Tuple[str, ...], default_language: str) -> Pattern:
    """Compiles and caches the signature regex for a given set of languages."""
    sent_from = '|'.join(_get_language_regex_patterns(languages, 'sent_from', default_language))
    signatures = '|'.join(_get_language_regex_patterns(languages, 'signatures', default_language))
    
    # CORRECTED: Removed the overly broad |{OUTLOOK_MAIL_SEPARATOR}
    regex = re.compile(
        fr'(({DEFAULT_SIGNATURE_REGEX}|' +  # <-- The separator check was removed from here
        fr'\s*^{QUOTED_MATCH_INCLUDE}(?:{sent_from}) ?(?:(?:[\w.<>:// ]+)|(?:\w+ ){{1,3}})$|' +
        fr'(?<!\A)^{QUOTED_MATCH_INCLUDE}(?:{signatures}))(.|\s)*)',
        flags=re.MULTILINE | re.IGNORECASE
    )
    logger.debug(f'Mail Signature RegEx: "{regex.pattern!r}"')
    return regex
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

    def __post_init__(self):
        if self.include_english and 'en' not in self.languages:
            self.languages.append('en')
        self.languages_tuple = tuple(sorted(self.languages))
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
        disclaimers_regex = get_disclaimers_regex(self.languages_tuple, self.default_language)
        signature_regex = get_signature_regex(self.languages_tuple, self.default_language)
        
        disclaimers = disclaimers_regex.findall(text)
        signatures_match = signature_regex.search(text)
        return disclaimers, signatures_match.group() if signatures_match else ''

    def read(self):
        """
        OPTIMIZED: Processes mail text body using re.finditer for better performance
        while preserving the original find-and-slice logic.
        """
        header_regex = get_header_regex(self.languages_tuple, self.default_language)
        
        current_position = 0
        previous_header = ''
        
        # re.finditer is an efficient way to loop over all matches
        for match in header_regex.finditer(self.text):
            position = match.start()
            header = match.group(0)

            # Process the content between the last header and this one
            content_slice = self.text[current_position:position]
            disclaimers, signatures = self._process_signatures_disclaimers(content_slice)
            
            _reply = EmailReply(
                headers=previous_header,
                content=content_slice,
                signatures=signatures,
                disclaimers=disclaimers
            )

            if _reply.content:
                self.replies.append(_reply)
            
            current_position = position
            previous_header = header

        # Add the final part of the message after the last header
        final_content = self.text[current_position:]
        disclaimers, signatures = self._process_signatures_disclaimers(final_content)
        _reply = EmailReply(
            headers=previous_header,
            content=final_content,
            signatures=signatures,
            disclaimers=disclaimers
        )
        if _reply.content or not self.replies:
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
