# -*- coding: utf-8 -*-
from collections import defaultdict
from collections import namedtuple
from itertools import ifilter, imap, izip

from glrengine.rules import RuleSet

Item = namedtuple('Item', ['rule_index', 'dot_position'])


def expand_item(item, R):
    rule = R[item[0]]
    return rule[1], item[1], rule[0]


def expand_itemset(itemset, R):
    return imap(lambda x: expand_item(x, R), itemset)


def expand_itemset2(itemset, R):
    for item in itemset:
        rule = R[item[0]]
        yield item[0], rule[1], item[1], rule[0]


def itemstr(item, R):
    e, i, n = expand_item(item, R)
    return ("[%s -> %s . %s" % (n, ' '.join(e[:i]), ' '.join(e[i:]))).strip() + ']'


def itemsetstr(itemset, R, label=''):
    items = map(lambda x: itemstr(x, R), sorted(itemset))
    width = reduce(lambda a, b: max(a, len(b)), items, 3)
    label = label and '[' + unicode(label) + ']' or ''
    build = ["+-%s%s-+" % (label, '-' * (width - len(label)))]
    build.extend("| %-*s |" % (width, item) for item in items)
    build.append("+-" + "-" * width + '-+')
    return '\n'.join(build)


def iterate_lookaheads(itemset, rules):
    for item in itemset:
        rule = rules[item.rule_index]

        if item.dot_position == len(rule.elements):
            # dot is in the end, there is no look ahead symbol
            continue

        lookahead = rule.elements[item.dot_position]

        yield item, lookahead


def first(itemset, rules):
    """
        Set of the tokens at the right of each dot in this item set
    """
    result = set()
    for item, lookahead in iterate_lookaheads(itemset, rules):
        if not lookahead in rules:
            result.add(lookahead)
    return result


def follow(itemset, rules):
    """
        All transitions from an item set in a dictionary [token]->item set
    """
    result = defaultdict(set)
    for item, lookahead in iterate_lookaheads(itemset, rules):
        tmp = closure([Item(item.rule_index, item.dot_position + 1)], rules)
        result[lookahead].update(tmp)
    return result


def closure(itemset, rules):
    """
        The epsilon-closure of this item set
    """
    result = set(itemset)
    visited = set()
    while True:
        tmp = set()
        for item, lookahead in iterate_lookaheads(result, rules):
            if lookahead in rules and lookahead not in visited:
                visited.add(lookahead)
                for rule_index in rules[lookahead]: # TODO: get_by_symbol
                    tmp.add(Item(rule_index, 0))

        if not tmp:
            # no changes
            return result
        result.update(tmp)


def generate_tables(rules):
    assert isinstance(rules, RuleSet)

    LR0 = set()
    x = closure([Item(0, 0)], rules)
    stack = [tuple(sorted(x))]
    while stack:
        x = stack.pop()
        LR0.add(x)
        F = follow(x, rules)
        for t, s in F.iteritems():
            s = tuple(sorted(s))
            if s not in LR0:
                stack.append(s)
    LR0 = list(sorted(LR0))

    LR0_idx = {}
    for i, s in enumerate(LR0):
        LR0_idx[s] = i

    GOTO = []
    for s in LR0:
        f = {}
        for tok, dest in follow(s, rules).iteritems():
            f[tok] = LR0_idx[tuple(sorted(closure(dest, rules)))]
        GOTO.append(f)


    ACTION = []
    for s, g in izip(LR0, GOTO):
        action = defaultdict(list)

        # свертки
        for item in ifilter(lambda item: item.dot_position == len(rules[item.rule_index].elements), s):
            if not item.rule_index:
                action['$'].append(('A', 0))
            # else:
            #     for kw in self.following_tokens(item):
            #         action[kw].append(('R', item.rule_index))

        # переносы
        for tok, dest in g.iteritems():
            action[tok].append(('S', dest))

        # commit
        ACTION.append(action)

    return ACTION, GOTO, LR0

def kernel(itemset):
    """
        The kernel items in this item set
    """
    return set(ifilter(lambda (r, i): not r or i, itemset))
