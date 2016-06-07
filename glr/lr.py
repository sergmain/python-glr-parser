# -*- coding: utf-8 -*-
from collections import namedtuple, defaultdict, OrderedDict

from glr.utils import unique
from glr.grammar import Grammar


class Item(namedtuple('Item', ['rule_index', 'dot_position'])):
    __slots__ = ()

    def __repr__(self):
        return '#%d.%d' % self


State = namedtuple('State', ['index', 'itemset', 'follow_dict', 'parent_rule_index', 'parent_lookahead'])

Action = namedtuple('Action', ['type', 'state', 'rule_index'])


def iterate_lookaheads(itemset, grammar):
    for item in itemset:
        rule = grammar[item.rule_index]

        if item.dot_position == len(rule.right_symbols):
            # dot is in the end, there is no look ahead symbol
            continue

        lookahead = rule.right_symbols[item.dot_position]

        yield item, lookahead


def follow(itemset, grammar):
    """
        All transitions from an item set in a dictionary [token]->item set
    """
    result = OrderedDict()
    for item, lookahead in iterate_lookaheads(itemset, grammar):
        tmp = closure([Item(item.rule_index, item.dot_position + 1)], grammar)

        if lookahead not in result:
            result[lookahead] = []
        result[lookahead].extend(tmp)

    for lookahead, itemset in result.iteritems():
        yield lookahead, unique(itemset)


def closure(itemset, grammar):
    """
        The epsilon-closure of this item set
    """
    items_to_process = itemset
    visited_lookaheads = set()
    while True:
        for item in items_to_process:
            yield item

        nested_to_process = []
        for item, lookahead in iterate_lookaheads(items_to_process, grammar):
            if lookahead in grammar.symbols and lookahead not in visited_lookaheads:
                visited_lookaheads.add(lookahead)
                for rule_index in grammar.rules_for_symbol(lookahead):  # TODO: get_by_symbol
                    nested_to_process.append(Item(rule_index, 0))

        if not nested_to_process:
            # no changes
            return

        items_to_process = nested_to_process


def generate_state_graph(grammar):
    assert isinstance(grammar, Grammar)

    #print 'Parent          | Next        '
    #print 'St | Lookahead  | St | Itemset'
    states = []
    state_by_itemset = {}

    first_itemset = closure([Item(0, 0)], grammar)
    first_itemset = tuple(sorted(first_itemset))
    stack = [(None, None, first_itemset)]
    while stack:
        parent_state_index, parent_lookahead, itemset = stack.pop(0)

        if itemset in state_by_itemset:
            # State already exist, just add follow link
            state = state_by_itemset[itemset]
            states[parent_state_index].follow_dict[parent_lookahead].add(state.index)
            # print '%2s | %-10s | %2d | %s' % (parent_state_index, parent_lookahead, state.index, '')
            continue

        state = State(len(states), itemset, defaultdict(set), parent_state_index, parent_lookahead)
        states.append(state)
        state_by_itemset[state.itemset] = state

        # print '%2s | %-10s | %2d | %s' % (parent_state_index or 0, parent_lookahead or '', state.index, state.itemset)

        if parent_state_index is not None:
            states[parent_state_index].follow_dict[parent_lookahead].add(state.index)

        for lookahead, itemset in follow(state.itemset, grammar):
            itemset = tuple(sorted(itemset))
            stack.append((state.index, lookahead, itemset))
    return states


def generate_followers(grammar):
    assert isinstance(grammar, Grammar)

    def get_starters(symbol):
        result = []
        for rule_index in grammar.rules_for_symbol(symbol):
            rule = grammar[rule_index]
            if rule.right_symbols[0] in grammar.nonterminals:
                if rule.right_symbols[0] != symbol:
                    result.extend(get_starters(rule.right_symbols[0]))
            else:
                result.append(rule.right_symbols[0])
        return result

    starters = dict((s, set(get_starters(s))) for s in grammar.nonterminals)

    def get_followers(symbol, seen_symbols=None):
        seen_symbols = seen_symbols or set()
        seen_symbols.add(symbol)

        result = []
        for rule in grammar.rules:
            if isinstance(rule, set):  # TODO: remove workaround
                continue

            if symbol not in rule.right_symbols:
                continue

            index = rule.right_symbols.index(symbol)
            if index + 1 == len(rule.right_symbols):
                if rule.left_symbol != symbol and rule.left_symbol not in seen_symbols:
                    result.extend(get_followers(rule.left_symbol, seen_symbols))
            else:
                next = rule.right_symbols[index + 1]
                if next in grammar.nonterminals:
                    result.extend(starters[next])
                else:
                    result.append(next)
        return result

    followers = dict((s, set(get_followers(s))) for s in grammar.nonterminals)
    return followers


def generate_tables(grammar):
    assert isinstance(grammar, Grammar)

    states = generate_state_graph(grammar)
    followers = generate_followers(grammar)

    result = []
    for state in states:
        actions = defaultdict(list)

        # Reduces
        for item in state.itemset:
            rule = grammar[item.rule_index]
            if item.dot_position == len(rule.right_symbols):
                if rule.left_symbol == '@':
                    actions['$'].append(Action('A', None, None))
                else:
                    for follower in followers[rule.left_symbol]:
                        actions[follower].append(Action('R', None, item.rule_index))
                    actions['$'].append(Action('R', None, item.rule_index))

        # Shifts & goto's
        for lookahead, state_indexes in state.follow_dict.items():
            for state_index in state_indexes:
                child_state = states[state_index]
                if lookahead in followers:
                    actions[lookahead].append(Action('G', child_state.index, None))
                else:
                    actions[lookahead].append(Action('S', child_state.index, None))

        result.append(actions)
    return result
