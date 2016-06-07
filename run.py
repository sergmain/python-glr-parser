# coding=utf-8
import re
import sys
from itertools import groupby

from glrengine import GLRScanner
from glrengine.lr import *
from glrengine.utils import gen_printable_table
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


def change_state_indexes(table, mapping):
    reverse_map = dict((v,k) for k,v in mapping.items())
    result = [table[reverse_map.get(i,i)] for i in range(len(table))]
    for row in result:
        for symbol, actions in row.items():
            for i, action in enumerate(actions):
                if action.state in mapping:
                    actions[i] = Action(action.action, mapping[action.state], action.rule_index)
    return result

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


class StackItem(namedtuple('StackItem', ['token', 'state', 'prev'])):
    __slots__ = ()

    def get_pathes(self):
        if self.prev:
            for prev in self.prev:
                for p in prev.get_pathes():
                    yield p + [self]
        else:
            yield [self]

    def path_str(self, second_line_prefix = ''):
        if self.prev:
            pathes = []
            for path in self.get_pathes():
                pathes.append(' > '.join(repr(i) for i in path))
            length = max(len(p) for p in pathes)

            results = []
            for i, path in enumerate(pathes):
                result = '' if i == 0 else second_line_prefix
                result += path.rjust(length)
                if len(pathes) > 1:
                    if i == 0:
                        result += ' ╮'
                    elif i!=len(pathes)-1:
                        result += ' │'
                    else:
                        result += ' ╯'
                results.append(result)

            return '\n'.join(results)
        else:
            return '0'

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

    def shift(self, head, token, state):
        new_head = StackItem(token, state, (head, ) if head else None)
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
                if goto_action.action == 'G':
                    new_head = self.shift(path[0], rule.name, goto_action.state)
                    result.append(new_head)
        return result



#TODO: rename Rule.name -> left_symbol
#TODO: rename Rule.elements -> right_symbols


def get_by_action_type(nodes, token, action_type):
    for node in nodes:
        node_actions = action_goto_table[node.state][token.symbol]
        for action in node_actions:
            if action.action == action_type:
                yield node, action

def parse(rules, action_goto_table, tokens):
    stack = Stack(rules, action_goto_table)

    stack.shift(None, None, 0)

    current = stack.heads[:]
    print current
    for token in tokens:
        print '\n\nToken', token

        process_reduce_nodes = current[:]
        while process_reduce_nodes:
            new_reduce_nodes = []
            for node, action in get_by_action_type(process_reduce_nodes, token, 'R'):
                print '- %s reduce by %s' % (node, action.rule_index)
                reduced_nodes = stack.reduce(node, action.rule_index)
                new_reduce_nodes.extend(reduced_nodes)
                for n in reduced_nodes:
                    print '    ', n.path_str('     ')
            process_reduce_nodes = new_reduce_nodes
            current.extend(new_reduce_nodes)

        shifted_nodes = []
        for node, action in get_by_action_type(current, token, 'S'):
            shifted_node = stack.shift(node, token, action.state)
            print '- %s shift to %s => %s' % (node, action.state, shifted_node)
            shifted_nodes.append(shifted_node)

        current = shifted_nodes

        merged = []
        for key, group in groupby(sorted(current), lambda si: (si.token, si.state)):
            group = [g for g in group]
            if len(group) > 1:
                all_prevs = tuple(p for node in group for p in node.prev)
                merged.append(StackItem(key[0], key[1], all_prevs))
            else:
                merged.append(group[0])
        current = merged


        print
        for node in current:
            print node.path_str()

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

parse(rules, action_goto_table, tokens)