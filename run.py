# coding=utf-8
import sys

from glrengine import GLRScanner
from glrengine.lr import *




dictionaries = {
    u"VARIABLES": [u"A", u"B", u"C"]
}

grammar = u"""
S = Sums
Sums = Sums 'plus' Products
Sums = Products
Products = Products 'mul' Value
Products = Value
Value = number
Value = VARIABLES
"""


grammar = u"""
S = Sums
Sums = Sums 'plus' Sums
Sums = number
S = E
E = A '1'
E = B '2'
A = '1'
B = '1'
"""

class GrammarParser(object):
    DEFAULT_PARSER = {
        "word": r"[\w\d_-]+",
        "number": r"[\d]+",
        "space": r"[\s]+",
        "newline": r"[\n]+",
        "dot": r"[\.]+",
        "comma": r"[,]+",
        "colon": r"[:]+",
        "percent": r"[%]+",
        "quote": r"[\"\'«»`]+",
        "brace": r"[\(\)\{\}\[\]]+",
    }

    DEFAULT_PARSER_DISCARD_NAMES = ["space"]

    DEFAULT_GRAMMAR = """
        Word = word
        Word = noun
        Word = adj
        Word = verb
        Word = pr
        Word = dpr
        Word = num
        Word = adv
        Word = pnoun
        Word = prep
        Word = conj
        Word = prcl
        Word = lat
    """

    def parse_grammar(self, grammar, dictionaries):
        grammar_rules = u"%s\n%s" % (grammar, self.DEFAULT_GRAMMAR)
        if dictionaries:
            # превращает {k: [a, b, c]} -> "k = 'a' | 'b' | 'c'"
            for dict_name, dict_words in dictionaries.items():
                morphed = []
                for word in dict_words:
                    # morphed.append(morph_parser.normal(word))
                    morphed.append(word)
                grammar_rules += u"\n%s = '%s'" % (dict_name, "' | '".join(morphed))

        parser_rules = self.DEFAULT_PARSER
        parser_rules.update({"discard_names": self.DEFAULT_PARSER_DISCARD_NAMES})
        return parser_rules

parser_rules = GrammarParser().parse_grammar(grammar, dictionaries)

# for k,v in parser_rules.items():
#     print k , v

scanner = GLRScanner(**parser_rules)
rules = RuleSet(grammar, set(scanner.tokens.keys()).union({'$'}), 'S')

nodes = generate_graph(rules)
t = generate_tables(rules)


def print_table(table, buf):
    col_widths = [0] * len(table[0])
    for row in table:
        for j, cell in enumerate(row):
            col_widths[j] = max(col_widths[j], len(str(cell)))
    print col_widths


    for i, row in enumerate(table):
        for j, cell in enumerate(row):
            buf.write(str(cell).ljust(col_widths[j]))
            buf.write(' | ')
        buf.write('\n')

table = []
symbols = sorted(unique(k for row in t for k in row.keys()))
table.append([''] + symbols)
for i, row in enumerate(t):
    res = [i]
    for k in symbols:
        res.append(', '.join('%s%s' % a for a in row[k]) if k in row else '')
    table.append(res)

print_table(table, sys.stdout)

# print '\n # |',
# for k in symbols:
#     print '%-9s|' % k,
# for i, row in enumerate(t):
#     print '\n%2d |' % i,
#     for k in symbols:
#         print '%-9s|' % (', '.join('%s%s' % a for a in row[k]) if k in row else ''),

folowers = generate_followers(rules)
print folowers