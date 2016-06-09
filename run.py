# coding=utf-8

from glr.automation import Automation
from glr.grammar import Rule
from glr.grammar_parser import GrammarParser
from glr.lexer import MorphologyLexer
from glr.lr import *
from glr.parser import Parser
from glr.tokenizer import Token, WordTokenizer, SimpleRegexTokenizer
from glr.utils import *
from glr.utils import flatten_syntax_tree


def test1():
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
    print format_grammar(grammar)

    states = generate_state_graph(grammar)
    print format_states(states, grammar)

    action_goto_table = generate_action_goto_table(grammar)
    print format_action_goto_table(action_goto_table)

    action_goto_table = change_state_indexes(action_goto_table, {3:4, 4:3, 7:8, 8:9, 9:7})
    print format_action_goto_table(action_goto_table)


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


def test2():

    grammar = u"""
    S = NP VP
    S = S PP
    NP = pnoun
    NP = noun
    NP = adj noun
    NP = NP PP
    PP = prep NP
    VP = verb NP
    """

    grammar = GrammarParser().parse(grammar, 'S')
    format_grammar(grammar)

    parser = Parser(grammar)

    tokenizer = WordTokenizer()
    print format_tokens(tokenizer.scan(u'Я видел того человека в той квартире с таким телескопом'))

    lexer = MorphologyLexer(tokenizer)
    tokens = list(lexer.scan(u'Я видел того человека в той квартире с таким телескопом'))
    print format_tokens(tokens)

    def reduce_validator(syntax_tree):
        return True

    res = parser.parse(tokens, reduce_validator)

def test3():
    grammar = u"""
    S = NP VP
    S = S PP
    NP = pnoun
    NP = noun
    NP = adj noun
    NP = NP PP
    PP = prep NP
    VP = verb NP
    """
    automation = Automation(grammar)
    for syntax_tree in automation.parse(u'Я видел того человека в той квартире с таким телескопом'):
        print format_syntax_tree(syntax_tree)


text = '''
S = NP VP | S PP
NP = pnoun (1.2)
     | noun
     | adj noun noun (4,5)
     | NP PP
PP = prep NP (2)
VP = verb<a> NP <a>
NP = 'test' "test"
'''

grammar = GrammarParser().parse(text, 'S')
print format_grammar(grammar)
