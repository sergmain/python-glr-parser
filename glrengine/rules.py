# coding=utf8
from collections import defaultdict
from scanner import make_scanner


lr_grammar_scanner = make_scanner(
    sep='=',
    alt='[|]',
    word=r"\b\w+\b",
    raw=r"\'\w+?\'",
    whitespace=r'[ \t\r\n]+',
    minus=r'[-]',
    label=r'\<.+?\>',
    discard_names=('whitespace',)
)


def make_rules(start, grammar, kw):
    words = [start]
    labels = []
    edit_rule = '@'
    edit_rule_commit = True
    next_edit_rule_commit = True
    kw.add(edit_rule)
    for tokname, tokvalue, tokpos in lr_grammar_scanner(grammar):
        if tokname == 'minus':
            next_edit_rule_commit = False
        if tokname == 'word' or tokname == 'raw':
            words.append(tokvalue)
            labels.append(None)
            kw.add(tokvalue)
        elif tokname == 'alt':
            yield (edit_rule, tuple(words), edit_rule_commit, labels[1:-1])
            words = []
            labels = []
        elif tokname == 'sep':
            tmp = words.pop()
            yield (edit_rule, tuple(words), edit_rule_commit, labels[1:-1])
            edit_rule_commit = next_edit_rule_commit
            next_edit_rule_commit = True
            edit_rule = tmp
            words = []
            labels = [None]
        elif tokname == 'label':
            # "a=b, b=c, d" -> {"a": "b", "b": "c", "d": None}
            tokvalue = tokvalue.strip().replace(" ", "")
            label = defaultdict(list)
            for l in tokvalue[1:-1].split(","):
                key, value = tuple(l.split("=", 1) + [None])[:2]
                label[key].append(value)
            # label = dict([tuple(l.split("=", 1) + [None])[:2] for l in tokvalue[1:-1].split(",")])
            labels[-1] = label
    yield (edit_rule, tuple(words), edit_rule_commit, labels[1:-1])


class RuleSet(dict):
    def __init__(self, rules):
        dict.__init__(self)
        self.names_count = 0
        self.rules_count = 0
        self.labels = {}
        self.init(rules)

    def init(self, rules):
        epsilons = self.fill(rules)
        must_cleanup = False
        while epsilons:
            eps = epsilons.pop()
            if eps in self:
                # Rule produces something and has an epsilon alternative
                self.add_epsilon_free(eps, epsilons)
            else:
                must_cleanup |= self.remove_epsilon(eps, epsilons)
        if must_cleanup:
            rules = sorted(self[i] for i in xrange(self.rules_count) if self[i] is not None)
            epsilons = self.fill(rules)
            if epsilons:
                #print "D'oh ! I left epsilon rules in there !", epsilons
                raise Exception("There is a bug ! There is a bug ! " +
                                "Failed to refactor this grammar into " +
                                "an epsilon-free one !")

    def fill(self, rules):
        self.names_count = 0
        self.rules_count = 0
        self.clear()
        epsilons = set()
        for rulename, elems, commit, labels in rules:
            if len(elems) > 0:
                self.add(rulename, elems, commit, labels)
            else:
                epsilons.add(rulename)
        #print 'found epsilon rules', epsilons
        return epsilons

    def add(self, rulename, elems, commit, labels):
        if rulename not in self:
            self.names_count += 1
            self[rulename] = set()
        rule = (rulename, elems, commit)
        if rule not in (self[i] for i in self[rulename]):
            self[rulename].add(self.rules_count)
            self[self.rules_count] = rule
            self.labels[self.rules_count] = labels
            self.rules_count += 1

    def add_epsilon_free(self, eps, epsilons):
        #print "Adding", eps, "-free variants"
        i = 0
        while i < self.rules_count:
            if self[i] is None:
                i += 1
                continue
            rulename, elems, commit = self[i]
            if eps in elems:
                #print "... to", rulename, elems
                E = set([elems])
                old = 0
                while len(E) != old:
                    old = len(E)
                    E = E.union(elems[:i] + elems[i + 1:]
                                for elems in E
                                for i in xrange(len(elems))
                                if elems[i] == eps)
                #print "Created variants", E
                for elems in E:
                    if len(elems) == 0:
                        #print "got new epsilon rule", rulename
                        epsilons.add(rulename)
                    else:
                        self.add(rulename, elems, commit, [])
                        #
                        #
            i += 1
            #

    def remove_epsilon(self, eps, epsilons):
        must_cleanup = False
        i = 0
        while i < self.rules_count:
            if self[i] is None:
                i += 1
                continue
            rulename, elems, commit = self[i]
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
                    #print "epsilon removal created new epsilon rule", rulename
                else:
                    self[i] = (rulename, elems, commit)
                    #
            i += 1
        return must_cleanup

