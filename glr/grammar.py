# coding=utf8
from collections import namedtuple

from glr.utils import unique

Rule = namedtuple('Rule', ['name', 'elements', 'commit'])


class Grammar(object):
    def __init__(self, rules):
        self._rules = rules
        self._rules_for_symbol = dict()
        for rule in rules:
            self._rules_for_symbol.setdefault(rule.name, set()).add(self._rules.index(rule))
            for symbol in rule.elements:
                self._rules_for_symbol.setdefault(symbol, set()).add(self._rules.index(rule))

        self._symbols = unique(symbol for rule in self._rules for symbol in rule.elements)
        self._nonterminals = set(rule.name for rule in self._rules)
        self._terminals = set(symbol for symbol in self._symbols if symbol not in self._nonterminals)

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
