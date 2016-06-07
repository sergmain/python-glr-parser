from collections import namedtuple

import re


class Token(namedtuple('Token', ['symbol', 'value', 'start', 'end'])):
    __slots__ = ()

    def __repr__(self):
        return '%s' % self.symbol


def tokenize(string):
    split_re = re.compile('(?:(?P<alpha>[^\W\d_]+)|(?P<space>\s+)|(?P<digit>\d+)|(?P<punct>[^\w\s]|_))', re.U)
    for m in split_re.finditer(string):
        yield Token(m.lastgroup, m.group(m.lastgroup), m.start(), m.end())
