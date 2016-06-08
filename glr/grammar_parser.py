# coding=utf8
from collections import defaultdict

from glr.grammar import Rule, Grammar
from glr.tokenizer import SimpleRegexTokenizer

__all__ = ['parse_grammar']


class RuleSet(dict):
    lr_grammar_tokenizer = SimpleRegexTokenizer(dict(
        sep='=',
        alt='[|]',
        word=r"\b\w+\b",
        raw=r"\'[^\s']+\'",
        whitespace=r'[ \t\r\n]+',
        minus=r'[-]',
        label=r'\<.+?\>',
        discard_names=('whitespace',)
    ), ['whitespace'])

    def __init__(self, grammar, kw_set, start_sym='S'):
        dict.__init__(self)
        rules = self.__make_rules(grammar, kw_set, start_sym)
        self.names_count = 0
        self.rules_count = 0
        self.labels = {}
        self.__init(rules)

    def __make_rules(self, grammar, kw, start):
        words = [start]
        labels = []
        edit_rule = '@'
        edit_rule_commit = True
        next_edit_rule_commit = True
        kw.add(edit_rule)
        for token in self.lr_grammar_tokenizer.scan(grammar):
            if token.symbol == 'minus':
                next_edit_rule_commit = False
            if token.symbol == 'word' or token.symbol == 'raw':
                words.append(token.value)
                labels.append(None)
                kw.add(token.value)
            elif token.symbol == 'alt':
                yield (edit_rule, tuple(words), edit_rule_commit, labels[1:-1])
                words = []
                labels = []
            elif token.symbol == 'sep':
                tmp = words.pop()
                yield (edit_rule, tuple(words), edit_rule_commit, labels[1:-1])
                edit_rule_commit = next_edit_rule_commit
                next_edit_rule_commit = True
                edit_rule = tmp
                words = []
                labels = [None]
            elif token.symbol == 'label':
                # "a=b, b=c, d" -> {"a": "b", "b": "c", "d": None}
                token_value = token.value.strip().replace(" ", "")
                label = defaultdict(list)
                for l in token_value[1:-1].split(","):
                    key, value = tuple(l.split("=", 1) + [None])[:2]
                    label[key].append(value)
                # label = dict([tuple(l.split("=", 1) + [None])[:2] for l in tokvalue[1:-1].split(",")])
                labels[-1] = label
        yield (edit_rule, tuple(words), edit_rule_commit, labels[1:-1])

    def __init(self, rules):
        epsilons = self.__fill(rules)
        must_cleanup = False
        while epsilons:
            eps = epsilons.pop()
            if eps in self:
                # Rule produces something and has an epsilon alternative
                self.__add_epsilon_free(eps, epsilons)
            else:
                must_cleanup |= self.__remove_epsilon(eps, epsilons)
        if must_cleanup:
            rules = sorted(self[i] for i in xrange(self.rules_count) if self[i] is not None)
            epsilons = self.__fill(rules)
            if epsilons:
                # print "D'oh ! I left epsilon rules in there !", epsilons
                raise Exception("There is a bug ! There is a bug ! " +
                                "Failed to refactor this grammar into " +
                                "an epsilon-free one !")

    def __fill(self, rules):
        self.names_count = 0
        self.rules_count = 0
        self.clear()
        epsilons = set()
        for rulename, elems, commit, labels in rules:
            if len(elems) > 0:
                self.__add(rulename, elems, commit, labels)
            else:
                epsilons.add(rulename)
        # print 'found epsilon rules', epsilons
        return epsilons

    def __add(self, rulename, elems, commit, labels):
        if rulename not in self:
            self.names_count += 1
            self[rulename] = set()
        rule = Rule(self.rules_count, rulename, elems, commit, labels)
        if rule not in (self[i] for i in self[rulename]):
            self[rulename].add(self.rules_count)
            self[self.rules_count] = rule
            self.labels[self.rules_count] = labels
            self.rules_count += 1

    def __add_epsilon_free(self, eps, epsilons):
        # print "Adding", eps, "-free variants"
        i = 0
        while i < self.rules_count:
            if self[i] is None:
                i += 1
                continue
            rule_index, rulename, elems, commit, labels = self[i]
            if eps in elems:
                # print "... to", rulename, elems
                E = set([elems])
                old = 0
                while len(E) != old:
                    old = len(E)
                    E = E.union(elems[:i] + elems[i + 1:]
                                for elems in E
                                for i in xrange(len(elems))
                                if elems[i] == eps)
                # print "Created variants", E
                for elems in E:
                    if len(elems) == 0:
                        # print "got new epsilon rule", rulename
                        epsilons.add(rulename)
                    else:
                        self.__add(rulename, elems, commit, [])
                        #
                        #
            i += 1
            #

    def __remove_epsilon(self, eps, epsilons):
        must_cleanup = False
        i = 0
        while i < self.rules_count:
            if self[i] is None:
                i += 1
                continue
            rule_index, rulename, elems, commit, labels = self[i]
            if eps in elems:
                elems = tuple(e for e in elems if e != eps)
                if len(elems) == 0:
                    # yet another epsilon :/
                    self[i] = None
                    self[rulename].remove(i)
                    if not self[rulename]:
                        del self[rulename]
                    must_cleanup = True
                    epsilons.add(rulename)
                    # print "epsilon removal created new epsilon rule", rulename
                else:
                    self[i] = Rule(i, rulename, elems, commit, labels)
                    #
            i += 1
        return must_cleanup


def parse_grammar(grammar, kw_set, start_sym='S'):
    rules = RuleSet(grammar, kw_set, start_sym)

    rules = [rule for i, rule in sorted(rules.items()) if not isinstance(rule, set)]

    return Grammar(rules)