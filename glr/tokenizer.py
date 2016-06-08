from collections import namedtuple

import re


class Token(namedtuple('Token', ['symbol', 'value', 'start', 'end', 'input_term', 'params'])):
    __slots__ = ()

    def __new__(cls, symbol, value='', start=-1, end=-1, input_term='', params=None):
        return super(cls, Token).__new__(cls, symbol, value, start, end, input_term, params)

    def __repr__(self):
        return '%s' % self.symbol


def tokenize(string):
    split_re = re.compile('(?:(?P<alpha>[^\W\d_]+)|(?P<space>\s+)|(?P<digit>\d+)|(?P<punct>[^\w\s]|_))', re.U)
    for m in split_re.finditer(string):
        yield Token(m.lastgroup, m.group(m.lastgroup), m.start(), m.end())
