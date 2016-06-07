from collections import namedtuple
from itertools import groupby

from glr.tokenizer import Token


class StackItem(namedtuple('StackItem', ['token', 'state', 'reduced', 'prev'])):
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

    def shift(self, token, state, reduced=None):
        return StackItem(token, state, reduced, (self,))

    def reduce(self, action_goto_table, rule):
        result = []
        depth = len(rule.right_symbols)
        for path in self.pop(depth):
            goto_actions = action_goto_table[path[0].state][rule.left_symbol]
            # TODO: probably assert that only 1 goto action and it is 'G'
            for goto_action in goto_actions:
                if goto_action.type == 'G':
                    new_head = path[0].shift(Token(rule.left_symbol, '', 0, 0), goto_action.state, tuple(path[1:]))
                    result.append(new_head)
        return result

    @classmethod
    def merge(cls, stack_items):
        for key, group in groupby(sorted(stack_items), lambda si: (si.token, si.state, si.reduced)):
            group = [g for g in group]
            if len(group) > 1:
                all_prevs = tuple(p for stack_item in group for p in stack_item.prev)
                yield StackItem(key[0], key[1], key[2], all_prevs)
            else:
                yield group[0]

    @classmethod
    def start_new(cls):
        return StackItem(None, 0, None, None)

    def __repr__(self):
        if self.prev:
            return '%s.%s' % (self.token, self.state)
        else:
            return '0'
