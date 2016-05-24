# -*- coding: utf-8 -*-
from collections import defaultdict
from collections import namedtuple
from itertools import ifilter, imap

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


def first(itemset, R):
    """
        Set of the tokens at the right of each dot in this item set
    """
    ret = set()
    for ruleelems, i, rulename in expand_itemset(itemset, R):
        if i == len(ruleelems):
            continue
        e = ruleelems[i]
        if not e in R:
            ret.add(e)
    return ret


def follow(itemset, rules):
    """
        All transitions from an item set in a dictionary [token]->item set
    """
    result = defaultdict(set)
    for item in itemset:
        rule = rules[item.rule_index]

        if item.dot_position == len(rule.elements):
            # dot is in the end, there is no look ahead symbol
            continue

        lookahead = rule.elements[item.dot_position]

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
        for item in result:
            rule = rules[item.rule_index]

            if item.dot_position == len(rule.elements):
                # dot is in the end, there is no look ahead symbol
                continue

            lookahead = rule.elements[item.dot_position]
            if lookahead in rules and lookahead not in visited:
                visited.add(lookahead)
                for rule_index in rules[lookahead]: # TODO: get_by_symbol
                    tmp.add(Item(rule_index, 0))

        if not tmp:
            # no changes
            return result
        result.update(tmp)


def kernel(itemset):
    """
        The kernel items in this item set
    """
    return set(ifilter(lambda (r, i): not r or i, itemset))
