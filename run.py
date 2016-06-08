# coding=utf-8
import sys

from glr.grammar_parser import GrammarParser
from glr.lr import *
from glr.parser import Parser
from glr.tokenizer import Token
from glr.utils import *

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


grammar = GrammarParser().parse(grammar, 'S')
print_grammar(grammar)

states = generate_state_graph(grammar)
print_states(states, grammar)

action_goto_table = generate_tables(grammar)
print_table(gen_printable_table(action_goto_table), sys.stdout)

action_goto_table = change_state_indexes(action_goto_table, {3:4, 4:3, 7:8, 8:9, 9:7})
print_table(gen_printable_table(action_goto_table), sys.stdout)


tokens = [
    Token('n', 'I'),
    Token("v", 'saw'),
    Token("det", 'a'),
    Token("n", 'man'),
    Token("prep", 'in'),
    Token("det", 'the'),
    Token("n", 'apartment'),
    Token("prep", 'with'),
    Token("det", 'a'),
    Token("n", 'telescope'),
    Token("$", ''),
]

def reduce_validator(syntax_tree):
    print 'LABELS: ', syntax_tree
    return True

parser = Parser(grammar)
res = parser.parse(tokens, reduce_validator)