# -*- coding: utf-8 -*-
from collections import defaultdict, OrderedDict
from collections import namedtuple

from glrengine.rules import RuleSet

class Item(namedtuple('Item', ['rule_index', 'dot_position'])):
    __slots__ = ()
    def __repr__(self):
        return '#%d.%d' % self


def itemstr():
    pass
def itemsetstr():
    pass
def first():
    pass
def kernel():
    pass

def iterate_lookaheads(itemset, rules):
    for item in itemset:
        rule = rules[item.rule_index]

        if item.dot_position == len(rule.elements):
            # dot is in the end, there is no look ahead symbol
            continue

        lookahead = rule.elements[item.dot_position]

        yield item, lookahead


def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def follow(itemset, rules):
    """
        All transitions from an item set in a dictionary [token]->item set
    """
    result = OrderedDict()
    for item, lookahead in iterate_lookaheads(itemset, rules):
        tmp = closure([Item(item.rule_index, item.dot_position + 1)], rules)

        if lookahead not in result:
            result[lookahead] = []
        result[lookahead].extend(tmp)

    for lookahead, itemset in result.iteritems():
        yield lookahead, unique(itemset)


def closure(itemset, rules):
    """
        The epsilon-closure of this item set
    """
    items_to_process = itemset
    visited_lookaheads = set()
    while True:
        for item in items_to_process:
            yield item

        nested_to_process = []
        for item, lookahead in iterate_lookaheads(items_to_process, rules):
            if lookahead in rules and lookahead not in visited_lookaheads:
                visited_lookaheads.add(lookahead)
                for rule_index in rules[lookahead]: # TODO: get_by_symbol
                    nested_to_process.append(Item(rule_index, 0))

        if not nested_to_process:
            # no changes
            return

        items_to_process = nested_to_process


Node = namedtuple('Node', ['index', 'itemset', 'follow_dict', 'parent_rule_index', 'parent_lookahead'])
Action = namedtuple('Action', ['action', 'state', 'rule_index'])


def generate_state_graph(rules):
    assert isinstance(rules, RuleSet)
    print 'Parent          | Next        '
    print 'St | Lookahead  | St | Itemset'
    nodes = []
    node_by_itemset = {}

    first_itemset = closure([Item(0, 0)], rules)
    first_itemset = tuple(sorted(first_itemset))
    stack = [(None, None, first_itemset)]
    while stack:
        parent_node_index, parent_lookahead, itemset = stack.pop(0)

        if itemset in node_by_itemset:
            # State already exist, just add follow link
            node = node_by_itemset[itemset]
            nodes[parent_node_index].follow_dict[parent_lookahead].add(node.index)
            print '%2s | %-10s | %2d | %s' % (parent_node_index, parent_lookahead, node.index, '')
            continue

        node = Node(len(nodes), itemset, defaultdict(set), parent_node_index, parent_lookahead)
        nodes.append(node)
        node_by_itemset[node.itemset] = node

        print '%2s | %-10s | %2d | %s' % (parent_node_index or 0, parent_lookahead or '', node.index, node.itemset)

        if parent_node_index is not None:
            nodes[parent_node_index].follow_dict[parent_lookahead].add(node.index)

        for lookahead, itemset in follow(node.itemset, rules):
            itemset = tuple(sorted(itemset))
            stack.append((node.index, lookahead, itemset))
    return nodes


def generate_followers(rules):
    symbols = unique(e for r in rules.values() if not isinstance(r, set) for e in r.elements)
    nonterminals = set(s for s in symbols if s in rules)

    def get_starters(symbol):
        result = []
        for rule_index in rules[symbol]:  # TODO: use get_by_symbol
            rule = rules[rule_index]
            if rule.elements[0] in nonterminals:
                if rule.elements[0] != symbol:
                    result.extend(get_starters(rule.elements[0]))
            else:
                result.append(rule.elements[0])
        return result

    starters = dict((s, set(get_starters(s))) for s in nonterminals)

    def get_followers(symbol, seen_symbols=None):
        seen_symbols = seen_symbols or set()
        seen_symbols.add(symbol)

        result = []
        for rule in rules.values():
            if isinstance(rule, set):  # TODO: remove workaround
                continue

            if symbol not in rule.elements:
                continue

            index = rule.elements.index(symbol)
            if index + 1 == len(rule.elements):
                if rule.name != symbol and rule.name not in seen_symbols:
                    result.extend(get_followers(rule.name, seen_symbols))
            else:
                next = rule.elements[index+1]
                if next in nonterminals:
                    result.extend(starters[next])
                else:
                    result.append(next)
        return result

    followers = dict((s, set(get_followers(s))) for s in nonterminals)
    return followers


def generate_tables(rules):
    nodes = generate_state_graph(rules)
    followers = generate_followers(rules)

    result = []
    for node in nodes:
        actions = defaultdict(list)

        # Reduces
        for item in node.itemset:
            rule = rules[item.rule_index]
            if item.dot_position == len(rule.elements):
                if rule.name == '@':
                    actions['$'].append(Action('A', None, None))
                else:
                    for follower in followers[rule.name]:
                        actions[follower].append(Action('R', None, item.rule_index))
                    actions['$'].append(Action('R', None, item.rule_index))

        # Shifts & goto's
        for lookahead, node_indexes in node.follow_dict.items():
            for node_index in node_indexes:
                child_node = nodes[node_index]
                if lookahead in followers:
                    actions[lookahead].append(Action('G', child_node.index, None))
                else:
                    actions[lookahead].append(Action('S', child_node.index, None))

        result.append(actions)
    return result
