from glr.grammar import Grammar
from glr.lr import generate_tables
from glr.stack import StackItem
from glr.utils import format_stack_item, format_syntax_tree


class Parser(object):
    def __init__(self, grammar, log_level=0):
        assert isinstance(grammar, Grammar)
        self.grammar = grammar
        self.action_goto_table = generate_tables(self.grammar)
        self.log_level = log_level

    def log(self, level, pattern, *args):
        if level <= self.log_level:
            print pattern % args

    def get_by_action_type(self, nodes, token, action_type):
        for node in nodes:
            node_actions = self.action_goto_table[node.state][token.symbol]
            for action in node_actions:
                if action.type == action_type:
                    yield node, action

    # http://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=DBFD4413CFAD29BC537FD98959E6B779?doi=10.1.1.39.1262&rep=rep1&type=pdf
    def parse(self, tokens, reduce_validator=None):
        accepted_nodes = []

        current = [StackItem.start_new()]

        for token in tokens:
            self.log(1, '\n\nTOKEN: %s', token)

            process_reduce_nodes = current[:]
            while process_reduce_nodes:
                new_reduce_nodes = []
                for node, action in self.get_by_action_type(process_reduce_nodes, token, 'R'):
                    self.log(1, '- REDUCE: (%s) by (%s)', node, action.rule_index)
                    rule = self.grammar[action.rule_index]
                    reduced_nodes = node.reduce(self.action_goto_table, rule, reduce_validator)
                    new_reduce_nodes.extend(reduced_nodes)
                    for n in reduced_nodes:
                        self.log('    %s', format_stack_item(n, '     '))
                process_reduce_nodes = new_reduce_nodes
                current.extend(new_reduce_nodes)

            for node, action in self.get_by_action_type(current, token, 'A'):
                self.log(1, '- ACCEPT: (%s)', node)
                accepted_nodes.append(node)

            shifted_nodes = []
            for node, action in self.get_by_action_type(current, token, 'S'):
                shifted_node = node.shift(token, action.state)
                self.log(1, '- SHIFT: (%s) to (%s)  =>  %s', node, action.state, shifted_node)
                shifted_nodes.append(shifted_node)

            current = shifted_nodes

            current = list(StackItem.merge(current))

            self.log(1, '\n- STACK:')
            for node in current:
                self.log(1, '%s', format_stack_item(node))

        self.log(1, '\n--------------------\nACCEPTED:')
        for node in accepted_nodes:
            self.log(1, '%s', format_syntax_tree(node.syntax_tree))

        return [node.syntax_tree for node in accepted_nodes]
