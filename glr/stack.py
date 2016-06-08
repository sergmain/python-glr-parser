from collections import namedtuple
from itertools import groupby


class SyntaxTree(namedtuple('SyntaxTree', ['symbol', 'token', 'rule_index', 'children'])):
    __slots__ = ()

    def is_leaf(self):
        return not self.children


class StackItem(namedtuple('StackItem', ['syntax_tree', 'state', 'prev'])):
    __slots__ = ()

    def pop(self, depth):
        if depth == 0:
            return [[self]]
        if not self.prev:
            return []

        result = []
        for prev in self.prev:
            for path in prev.pop(depth - 1):
                result.append(path + [self])
        return result

    def shift(self, token, state):
        syntax_tree = SyntaxTree(token.symbol, token, None, ())
        return StackItem(syntax_tree, state, (self,))

    def reduce(self, action_goto_table, rule, reduce_validator=None):
        result = []
        depth = len(rule.right_symbols)
        for path in self.pop(depth):
            goto_actions = action_goto_table[path[0].state][rule.left_symbol]
            # TODO: probably assert that only 1 goto action and it is 'G'
            for goto_action in goto_actions:
                if goto_action.type == 'G':
                    # TODO: use rule.index instead of 0
                    syntax_tree = SyntaxTree(rule.left_symbol, None, 0, tuple(stack_item.syntax_tree for stack_item in path[1:]))
                    if reduce_validator is None or reduce_validator(syntax_tree):
                        new_head = StackItem(syntax_tree, goto_action.state, (path[0],))
                        result.append(new_head)
        return result

    @classmethod
    def merge(cls, stack_items):
        for key, group in groupby(sorted(stack_items), lambda si: (si.syntax_tree, si.state)):
            group = [g for g in group]
            if len(group) > 1:
                all_prevs = tuple(p for stack_item in group for p in stack_item.prev)
                yield StackItem(group[0].syntax_tree, group[0].state, all_prevs)
            else:
                yield group[0]

    @classmethod
    def start_new(cls):
        return StackItem(None, 0, None)

    def __repr__(self):
        if self.prev:
            return '%s.%s' % (self.syntax_tree.symbol, self.state)
        else:
            return '0'
