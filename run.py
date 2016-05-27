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


grammar2 = u"""
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

    def print_row(i, chars, row=None):
        if i>0 and i % 2 == 0:
            buf.write('\033[48;5;236m')
        for j, cell in enumerate(row or col_widths):
            if j == 0:
                buf.write(chars[0:2])

            if row:
                buf.write(str(cell).ljust(col_widths[j]))
            else:
                buf.write(chars[1] * col_widths[j])

            if j < len(col_widths) - 1:
                buf.write(chars[1:4])
            else:
                buf.write(chars[3:5])

        buf.write('\033[m')
        buf.write('\n')

    for i, row in enumerate(table):
        if i == 0:
            print_row(i, u'┌─┬─┐')
        elif i == 1:
            print_row(i, u'├─┼─┤')
        if True:
            print_row(i, u'│ │ │', row)
        if i == len(table) - 1:
            print_row(i, u'└─┴─┘')


def gen_printable_table(action_table):
    table = []
    symbols = sorted(unique(k for row in t for k in row.keys()))
    table.append([''] + symbols)
    for i, row in enumerate(action_table):
        res = [i]
        for k in symbols:
            res.append(', '.join('%s%s' % a for a in row[k]) if k in row else '')
        table.append(res)
    return table

print_table(gen_printable_table(t), sys.stdout)

