# coding=utf-8
import re
import sys
from itertools import groupby

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

class Token(namedtuple('Token', ['symbol', 'value', 'start', 'end'])):
    __slots__ = ()
    def __repr__(self):
        return '%s' % self.symbol

def tokenize(string):
    split_re = re.compile('(?:(?P<alpha>[^\W\d_]+)|(?P<space>\s+)|(?P<digit>\d+)|(?P<punct>[^\w\s]|_))', re.U)
    for m in split_re.finditer(string):
        yield Token(m.lastgroup, m.group(m.lastgroup), m.start(), m.end())

# for t, v, s, e in tokenize(u'Кронштейн f0a f_n КАМАЗ 20т. (На 5320,740-15)'):
#     print t, v, s, e






class StackItem(namedtuple('StackItem', ['token', 'state', 'reduced', 'prev'])):
    __slots__ = ()

    def pop(self, depth):
        if depth == 0:
            return [[self]]
        if not self.prev:
            return []

        result = []
        for prev in self.prev:
            for path in prev.pop(depth-1):
                result.append(path + [self])
        return result

    def shift(self, token, state, reduced=None):
        return StackItem(token, state, reduced, (self, ))

    def reduce(self, action_goto_table, rule):
        result = []
        depth = len(rule.elements)
        for path in self.pop(depth):
            goto_actions = action_goto_table[path[0].state][rule.name]
            # TODO: probably assert that only 1 goto action and it is 'G'
            for goto_action in goto_actions:
                if goto_action.type == 'G':
                    new_head = path[0].shift(Token(rule.name, '', 0, 0), goto_action.state, tuple(path[1:]))
                    result.append(new_head)
        return result

    @classmethod
    def start_new(self):
        return StackItem(None, 0, None, None)

    def __repr__(self):
        if self.prev:
            return '%s.%s' % (self.token, self.state)
        else:
            return '0'

class Stack(object):

    def __init__(self, rules, action_goto_table):
        self.rules = rules
        self.action_goto_table = action_goto_table

        self.heads = []

    def pop(self, node, depth):
        if depth == 0:
            return [[node]]
        if not node.prev:
            return []

        result = []
        for prev in node.prev:
            for path in self.pop(prev, depth-1):
                result.append(path + [node])
        return result

    def shift(self, head, token, state, reduced=None):
        new_head = StackItem(token, state, reduced, (head, ) if head else None)
        self.heads.append(new_head)
        return new_head

    def reduce(self, head, rule_index):
        result = []
        rule = self.rules[rule_index]
        depth = len(rule.elements)
        for path in self.pop(head, depth):
            goto_actions = self.action_goto_table[path[0].state][rule.name]
            # TODO: probably assert that only 1 goto action and it is 'G'
            for goto_action in goto_actions:
                if goto_action.type == 'G':
                    new_head = self.shift(path[0], Token(rule.name, '', 0, 0), goto_action.state, tuple(path[1:]))
                    result.append(new_head)
        return result



#TODO: rename Rule.name -> left_symbol
#TODO: rename Rule.elements -> right_symbols


def get_by_action_type(nodes, token, action_type):
    for node in nodes:
        node_actions = action_goto_table[node.state][token.symbol]
        for action in node_actions:
            if action.type == action_type:
                yield node, action

# http://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=DBFD4413CFAD29BC537FD98959E6B779?doi=10.1.1.39.1262&rep=rep1&type=pdf
def parse(rules, action_goto_table, tokens):
    accepted_nodes = []

    current = [StackItem.start_new()]

    for token in tokens:
        print '\n\nTOKEN:', token

        process_reduce_nodes = current[:]
        while process_reduce_nodes:
            new_reduce_nodes = []
            for node, action in get_by_action_type(process_reduce_nodes, token, 'R'):
                print '- REDUCE: (%s) by (%s)' % (node, action.rule_index)
                rule = rules[action.rule_index]
                reduced_nodes = node.reduce(action_goto_table, rule)
                new_reduce_nodes.extend(reduced_nodes)
                for n in reduced_nodes:
                    print '    ', print_stack_item(n, '     ')
            process_reduce_nodes = new_reduce_nodes
            current.extend(new_reduce_nodes)

        for node, action in get_by_action_type(current, token, 'A'):
            print '- ACCEPT: (%s)' % (node,)
            accepted_nodes.append(node)

        shifted_nodes = []
        for node, action in get_by_action_type(current, token, 'S'):
            shifted_node = node.shift(token, action.state)
            print '- SHIFT: (%s) to (%s)  =>  %s' % (node, action.state, shifted_node)
            shifted_nodes.append(shifted_node)

        current = shifted_nodes

        merged = []
        for key, group in groupby(sorted(current), lambda si: (si.token, si.state, si.reduced)):
            group = [g for g in group]
            if len(group) > 1:
                all_prevs = tuple(p for node in group for p in node.prev)
                merged.append(StackItem(key[0], key[1], key[2], all_prevs))
            else:
                merged.append(group[0])
        current = merged

        print '\n- STACK:'
        for node in current:
            print print_stack_item(node)

    print '\n--------------------\nACCEPTED:'
    for node in accepted_nodes:
        print_ast(node)

    return accepted_nodes

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

res = parse(rules, action_goto_table, tokens)
#s = res[-1]
#print_ast(s)