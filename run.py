# coding=utf-8
import re
import sys
from itertools import groupby

from glr.parser import Parser
from glr.tokenizer import Token
from glrengine import GLRScanner
from glrengine.lr import *
from glrengine.utils import gen_printable_table, print_ast, print_stack_item, change_state_indexes
from glrengine.utils import print_table

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

grammar = u"""
S = NP VP
S = S PP
NP = n
NP = det n
NP = NP PP
PP = prep NP
VP = v NP
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

for i, r in sorted(rules.items()):
    if isinstance(i, int):
        print '%2d | %-10s | %s' %(i,r[0],' '.join(r[1]))

# nodes = generate_state_graph(rules)
action_goto_table = generate_tables(rules)

action_goto_table = change_state_indexes(action_goto_table, {3:4, 4:3, 7:8, 8:9, 9:7})

print_table(gen_printable_table(action_goto_table), sys.stdout)

# for t, v, s, e in tokenize(u'Кронштейн f0a f_n КАМАЗ 20т. (На 5320,740-15)'):
#     print t, v, s, e

#TODO: rename Rule.name -> left_symbol
#TODO: rename Rule.elements -> right_symbols



tokens = [
    Token('n', 'I', 0, 0),
    Token("v", 'saw', 0, 0),
    Token("det", 'a', 0, 0),
    Token("n", 'man', 0, 0),
    Token("prep", 'in', 0, 0),
    Token("det", 'the', 0, 0),
    Token("n", 'apartment', 0, 0),
    Token("prep", 'with', 0, 0),
    Token("det", 'a', 0, 0),
    Token("n", 'telescope', 0, 0),
    Token("$", '', 0, 0),
]

parser = Parser(rules, action_goto_table)

res = parser.parse(tokens)
#s = res[-1]
#print_ast(s)