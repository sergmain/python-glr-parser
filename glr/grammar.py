# coding=utf8
from collections import namedtuple

Rule = namedtuple('Rule', ['left_symbol', 'right_symbols', 'commit'])


class Grammar(object):
    def __init__(self, rules):
        self._rules = rules
        self._rules_for_symbol = dict()
        for rule in self._rules:
            self._rules_for_symbol.setdefault(rule.left_symbol, set()).add(self._rules.index(rule))

        def all_symbols():
            for rule in self._rules:
                yield rule.left_symbol
                for symbol in rule.right_symbols:
                    yield symbol

        self._symbols = set(all_symbols())
        self._nonterminals = set(rule.left_symbol for rule in self._rules)
        self._terminals = self._symbols - self._nonterminals

    def __getitem__(self, item):
        return self._rules[item]

    def rules_for_symbol(self, symbol):
        return self._rules_for_symbol[symbol]

    @property
    def rules(self):
        return self._rules

    @property
    def symbols(self):
        return self._symbols

    @property
    def terminals(self):
        return self._terminals

    @property
    def nonterminals(self):
        return self._nonterminals
