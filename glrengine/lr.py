# -*- coding: utf-8 -*-
from collections import defaultdict, OrderedDict
from collections import namedtuple

from glrengine.rules import RuleSet

Item = namedtuple('Item', ['rule_index', 'dot_position'])


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
Action = namedtuple('Action', ['action', 'rule_index'])


def generate_graph(rules):
    assert isinstance(rules, RuleSet)

    nodes = []
    node_by_itemset = {}

    first_itemset = closure([Item(0, 0)], rules)
    first_itemset = tuple(sorted(first_itemset))
    stack = [(None, None, first_itemset)]
    while stack:
        parent_node_index, parent_lookahead, itemset = stack.pop(0)

        node = Node(len(nodes), itemset, defaultdict(set), parent_node_index, parent_lookahead)
        nodes.append(node)
        node_by_itemset[node.itemset] = node

        #print '%2s | %9s | %2d | %s' % (parent_node_index or 0, parent_lookahead or '', node.index, node.itemset)

        if parent_node_index is not None:
            nodes[parent_node_index].follow_dict[parent_lookahead].add(node.index)

        for lookahead, itemset in follow(node.itemset, rules):
            itemset = tuple(sorted(itemset))
            if itemset not in node_by_itemset:
                # Add new state, follow links will be added when it popped from the stack
                stack.append((node.index, lookahead, itemset))
            else:
                # State already exist, just add follow link
                child_node = node_by_itemset[itemset]
                node.follow_dict[lookahead].add(child_node.index)
                #print '%2s | %9s | %2d | %s' % (node.index, lookahead, child_node.index, '')
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

    def get_followers(symbol):
        result = []
        for rule in rules.values():
            if isinstance(rule, set):  # TODO: remove warkaround
                continue

            if symbol not in rule.elements:
                continue

            index = rule.elements.index(symbol)
            if index + 1 == len(rule.elements):
                if rule.name != symbol:
                    result.extend(get_followers(rule.name))
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
    nodes = generate_graph(rules)
    followers = generate_followers(rules)

    result = []
    for node in nodes:
        actions = defaultdict(list)

        # Reduces
        for item in node.itemset:
            rule = rules[item.rule_index]
            if item.dot_position == len(rule.elements):
                if rule.name == '@':
                    actions['$'].append(Action('A', 0))
                else:
                    for follower in followers[rule.name]:
                        actions[follower].append(Action('R', item.rule_index))
                    actions['$'].append(Action('R', item.rule_index))

        # Shifts
        for lookahead, node_indexes in node.follow_dict.items():
            for node_index in node_indexes:
                child_node = nodes[node_index]
                actions[lookahead].append(Action('' if lookahead in followers else 'S', child_node.index))

        result.append(actions)
    return result