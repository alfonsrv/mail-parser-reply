from typing import Dict

#: Fallback language if no other language is specified
MAIL_LANGUAGE_DEFAULT = 'en'

#: Matches text-mail quotation (usually starting with ">");
#: resulting in "> Hello world"
QUOTED_REGEX = r'(>+)'
#: Regex to remove all leading quotations
QUOTED_REMOVAL_REGEX = r'^(> *)'
#: Allow to match within (multi)-quoted body
#: e.g. allowing regex to match *inside* lines starting with "> > ..."
QUOTED_MATCH_INCLUDE = r'(?:> ?)*'

#: Outlook-style mail separator (32 underscores); also occasionally
#: used within signatures
OUTLOOK_MAIL_SEPARATOR = r'(\n{2,} ?[_-]{32,})'
#: Common mail separators (+ old Outlook separator)
GENERIC_MAIL_SEPARATOR = r'^-{5,} ?Original Message ?-{5,}$'

#: Outlook Signature defaults; line optionally starts with whitespace, contains two
#: hyphens or underscores, and ends with optional whitespace.
#   1) -- \nJohn Doe
#   2) -John Doe
DEFAULT_SIGNATURE_REGEX = rf'\s*^{QUOTED_MATCH_INCLUDE}(?:[-_]{{2}}\n|- ?\w).*'

#: All kinds of whitespaces incl special characters; used for Disclaimers, because they
#: are usually either added in post by a mailserver or scrambled due to their higher complexity.
SINGLE_SPACE_VARIATIONS = '[ \u200b\xA0\t]'
#: Linebreaks ok too
OPTIONAL_LINEBREAK = f'[,()]?{SINGLE_SPACE_VARIATIONS}{{0,3}}[\n\r]?{SINGLE_SPACE_VARIATIONS}{{0,3}}[,()]?'
#: Possible ways to check for linebreaks
SENTENCE_START = f'(?:[\n\r.!?]|^){SINGLE_SPACE_VARIATIONS}{{0,3}}'

#: Matching regex for all languages
MAIL_LANGUAGES: Dict[str, Dict[str, str]] = {
    'de': {
        'wrote_header': r'^(?!Am.*Am\s.+?schrieb.*:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Am\s(?:.+?\s?)schrieb\s(?:.+?\s?.+?):)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Von|Gesendet|An|Betreff|Datum|Cc|Organisation):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            '(?:Wichtiger )?Hinweis:',
            'Achtung:',
        ],
        'signatures': [
            r'Mit freundlichen Gr\u00fc\u00DFen',
            r'Mit freundlichen Gr\u00fc\u00DFen / (?:Best|Kind) regards,',
            r'(?:(?:Beste(?:n)?|Liebe|Viele) )?(?:Gr(?:\u00fc|ue)(?:\u00DF|ss)(?:e)?|Gru\u00DF|Gruss)',
        ],
        'sent_from': 'Gesendet von',
    },
    'en': {
        # Apple Mail-style header
        # ^(?!On[.\s]*On\s(.+?\s?.+?)\swrote:) – Negative lookahead, see:
        #    https://github.com/github/email_reply_parser/pull/31
        # <QUOTED_MATCH_INCLUDE> – allow matching this inside quoted levels
        # On\s(?:.+?\s?.+?)\swrote:) – match "On 01.01.2025, John Doe wrote:"
        #   See multiline_on.txt for example data
        'wrote_header': r'^(?!On[.\s]*On\s(.+?\s?.+?)\swrote:)(' + QUOTED_MATCH_INCLUDE + r'On\s(?:.+?\s?.+?)\s?wrote:)$',
        # Outlook-style header
        # (?:(?:^|\n)[* ]*(?:From|Sent|To|Subject|Date|Cc):[ *]* – match From:/*From*:, ... headers
        # (?:\s{,2}).*){2,} – allow multi-line headers; some clients split the headers up into multiple lines.
        #       Also require at least two occurrences of the above pattern; e.g. From: ...\n Sent: ...
        # (?:\n.*){,1} – allow optional subject or other broken multi-line at the end
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:From|Sent|To|Subject|Date|Cc|Organization):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            'CAUTION:',
            'Disclaimer:',
            'Warning:',
            'Confidential:',
            'CONFIDENTIALITY:',
            '(?:Privileged|Confidential|Private|Sensitive|Important) (?:Notice|Note|Information):',
            '[\* ]*Disclaimer[\* ]*',
        ],
        'signatures': [
            'Best regards',
            'Kind Regards',
            'Thanks,',
            'Thank you,',
            'Best,',
            'All the best',
            'regards,',
        ],
        'sent_from': 'Sent from my|Get Outlook for',
    },
    'fr': {
        'wrote_header': r'(?!Le.*Le\s.+?a \u00e9crit[a-zA-Z0-9.:;<>()&@ -]*:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Le\s(.+?)a \u00e9crit[a-zA-Z0-9.:;<>()&@ -]*:)',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:De |Envoy\u00e9 |\u00C0 |Objet |  |Cc ):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'signatures': [
            'cordialement',
            'salutations',
            r'bonne r[\u00e9e]ception',
            r'bonne journ[\u00e9e]e',
        ],
        'sent_from': r'Envoy\u00e9 depuis',
    },
    'it': {
        'wrote_header': r'^(?!Il[.\s]*Il\s(.+?\s?.+?)\sha scritto:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Il\s(?:.+?\s?.+?)\s?ha scritto:)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Da|Inviato|A|Oggetto|Data|Cc):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'signatures': [
            'Cordiali saluti',
        ],
        'sent_from': 'Inviato da',
    },
    'ja': {
        'wrote_header': r'^(?!.*\d{4}年\d{1,2}月\d{1,2}日\(.\) \d{1,2}:\d{2}.+? <.+?>:.*\d{4}年\d{1,2}月\d{1,2}日\(.\) \d{1,2}:\d{2}.+? <.+?>:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'\d{4}年\d{1,2}月\d{1,2}日\(.\) \d{1,2}:\d{2}.+? <.+?>):$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:From|Sent|To|Subject|Date|Cc):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [],
        'signatures': [],
        'sent_from': '',
    },
    'nl': {
        'wrote_header': r'^(?!Op[.\s]*Op\s(.+?\s?.+?)\sschreef:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Op\s(?:.+?\s?.+?)\s?schreef:)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Van|Verzonden|Aan|Onderwerp|Datum|Cc):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            'Disclaimer:',
            'Waarschuwing:',
        ],
        'signatures': [
            'Met vriendelijke groet',
            'Hartelijke groeten',
            'Bedankt,',
            'Dank u,',
        ],
        'sent_from': 'Verzonden vanaf mijn',
    },
    'pl': {
        'wrote_header': r'^(?!Dnia[.\s]*Dnia\s(.+?\s?.+?)\s(?:nadesłał|napisał\(a\)):)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Dnia\s(?:.+?\s?.+?)\s?(?:nadesłał|napisał\(a\)):)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Od|Wysłano|Do|Temat|Data|DW):[ *]*(?:\s{,2}).*){1,}(?:\n.*){,1})',
        'disclaimers': [
            'Uwaga:'
        ],
        'signatures': [
            'Z poważaniem',
            'Z powazaniem',
            'Pozdrawiam',
            'W przypadku niejasności, proszę o kontakt.'
        ],
        'sent_from': 'Wysłano z'
    },
    'david': {
        # Custom Software Headers – also kind of like a language, right?
        'from_header': r'((?:^ *' + QUOTED_MATCH_INCLUDE + r'\[?Original Message processed by david.+?$\n{,4})'
                       + r'(?:.*\n?){,2}'  # david's non-subject line + date wildcard identification
                       + r'(?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE + ')[* ]*(?:Von|An|Cc)(?:\s{,2}).*){2,})'
    },
}
