from collections import namedtuple

import re


class Token(namedtuple('Token', ['symbol', 'value', 'start', 'end', 'input_term', 'params'])):
    __slots__ = ()

    def __new__(cls, symbol, value='', start=-1, end=-1, input_term='', params=None):
        return super(cls, Token).__new__(cls, symbol, value, start, end, input_term, params)

    def __repr__(self):
        return '%s' % self.symbol

class TokenizerException(Exception):
    pass


class SimpleRegexTokenizer(object):
    def __init__(self, symbol_regex_dict, regex_flags = re.M | re.U | re.I):
        patterns = []
        for symbol, regex in symbol_regex_dict.items():
            if '(?P<' in regex:
                raise TokenizerException('Invalid regex "%s" for symbol "%s"' % (regex, symbol))
            patterns.append('(?P<%s>%s)' % (symbol, regex))
        self.re = re.compile('|'.join(patterns), regex_flags)
        self.symbols = set(symbol_regex_dict.keys())

    def scan(self, text):
        for m in self.re.finditer(text):
            yield Token(m.lastgroup, m.group(m.lastgroup), m.start(), m.end())


class CharTypeTokenizer(SimpleRegexTokenizer):
    def __init__(self):
        symbol_regex_dict = {
            'alpha': r'[^\W\d_]+',
            'space': r'\s+',
            'digit': r'\d+',
            'punct': r'[^\w\s]|_',
        }
        super(CharTypeTokenizer, self).__init__(symbol_regex_dict)


