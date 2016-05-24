# coding=utf-8
from collections import defaultdict
from itertools import ifilter, izip

from glr import GLRParser
from glrengine import GLRScanner
from glrengine.lr import closure, Item, follow, generate_tables
from glrengine.parser import Parser
from glrengine.rules import RuleSet

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

class Grammar(object):
    def __init__(self, grammar_str, dictionaries):
        parser_rules = GrammarParser().parse_grammar(grammar_str, dictionaries)
        scanner = GLRScanner(**parser_rules)
        self._symbols = set(scanner.tokens.keys()).union({'$'})
        self._rules = RuleSet(grammar, self._symbols, 'S')

        self._rules_by_symbol = defaultdict(list)
        for index, rule in self._rules.iteritems():
            if index is int:
                self._rules_by_symbol[index].append(rule)

    def get_symbols(self):
        return self._symbols

    def __getitem__(self, item):
        assert item is int
        return self._rules[item]

    def __len__(self):
        return len(self._rules)

    def rule_by_symbol(self, symbol):
        return self._rules_by_symbol[symbol]


class LrTable(object):
    def __init__(self, grammar):
        assert isinstance(grammar, Grammar)
        self._grammar = grammar

    def generate_table(self):
        self.LR0 = set()
        x = closure([Item(0, 0)], self.R)
        self.initial_items = x
        stack = [tuple(sorted(x))]
        while stack:
            x = stack.pop()
            self.LR0.add(x)
            F = follow(x, self.R)
            for t, s in F.iteritems():
                s = tuple(sorted(s))
                if s not in self.LR0:
                    stack.append(s)

g = Grammar(grammar, dictionaries)

for k, rule in sorted(rules.items()):
     print k, '=>', rule

class TableBuilder(object):
    def __init__(self):
        self.R = rules

    def compute_lr0(self):
        """
            Compute the LR(0) sets.
        """
        self.LR0 = set()
        x = closure([Item(0, 0)], self.R)
        self.initial_items = x
        stack = [tuple(sorted(x))]
        while stack:
            x = stack.pop()
            self.LR0.add(x)
            F = follow(x, self.R)
            for t, s in F.iteritems():
                s = tuple(sorted(s))
                if s not in self.LR0:
                    stack.append(s)

    def compute_GOTO(self):
        """
            Compute the GOTO table.
        """
        self.GOTO = []
        for s in self.LR0:
            f = {}
            for tok, dest in follow(s, self.R).iteritems():
                f[tok] = self.LR0_idx[self.closure(dest)]
            self.GOTO.append(f)

    def compute_ACTION(self):
        """
            Compute the ACTION/GOTO table.
        """
        self.compute_GOTO()
        self.ACTION = []
        for s, g in izip(self.LR0, self.GOTO):
            action = self.init_row()

            # свертки
            for item in ifilter(lambda item: item.dot_position == len(self.R[item.rule_index].elements), s):
                if not item.rule_index:
                    action['$'].append(('A', ))
                else:
                    for kw in self.following_tokens(item):
                        action[kw].append(('R', item.rule_index))

            # переносы
            for tok, dest in g.iteritems():
                action[tok].append(('S', dest))

            # commit
            self.ACTION.append(action)

# tb = TableBuilder()
# tb.compute_lr0()
print sorted(scanner.tokens.keys())

parser = Parser(grammar, scanner.tokens.keys(), 'S')

a, g, l = generate_tables(rules)


print '  |',
for k, v in sorted(parser.ACTION[0].items()):
    print '%-9s|' % k,
print
for i, row in enumerate(parser.ACTION):
    print '%2d|' %i,
    for k, v in sorted(row.items()):
        print '%-9s|' % ' '.join([('%s.%s' % ri if len(ri)==2 else ri[0]) for ri in v]),
    print

print
for i, row in enumerate(parser.GOTO):
    print '%2d|' %i,
    for k, v in sorted(parser.ACTION[0].items()):
        cell = ''
        if k in row:
            cell = row[k]
        print '%-9s|' % cell,
    print

glr = GLRParser(grammar, dictionaries=dictionaries, debug=False)

text = u"a mul 2 plus 1"
for parsed in glr.parse(text):
    print "FOUND:", parsed