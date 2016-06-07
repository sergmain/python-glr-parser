from glr.grammar import Grammar
from glr.lr import generate_tables
from glr.stack import StackItem
from glr.utils import print_stack_item, print_ast


class Parser(object):
    def __init__(self, grammar):
        assert isinstance(grammar, Grammar)
        self.grammar = grammar
        self.action_goto_table = generate_tables(self.grammar)

    def get_by_action_type(self, nodes, token, action_type):
        for node in nodes:
            node_actions = self.action_goto_table[node.state][token.symbol]
            for action in node_actions:
                if action.type == action_type:
                    yield node, action

    # http://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=DBFD4413CFAD29BC537FD98959E6B779?doi=10.1.1.39.1262&rep=rep1&type=pdf
    def parse(self, tokens):
        accepted_nodes = []

        current = [StackItem.start_new()]

        for token in tokens:
            print '\n\nTOKEN:', token

            process_reduce_nodes = current[:]
            while process_reduce_nodes:
                new_reduce_nodes = []
                for node, action in self.get_by_action_type(process_reduce_nodes, token, 'R'):
                    print '- REDUCE: (%s) by (%s)' % (node, action.rule_index)
                    rule = self.grammar[action.rule_index]
                    reduced_nodes = node.reduce(self.action_goto_table, rule)
                    new_reduce_nodes.extend(reduced_nodes)
                    for n in reduced_nodes:
                        print '    ', print_stack_item(n, '     ')
                process_reduce_nodes = new_reduce_nodes
                current.extend(new_reduce_nodes)

            for node, action in self.get_by_action_type(current, token, 'A'):
                print '- ACCEPT: (%s)' % (node,)
                accepted_nodes.append(node)

            shifted_nodes = []
            for node, action in self.get_by_action_type(current, token, 'S'):
                shifted_node = node.shift(token, action.state)
                print '- SHIFT: (%s) to (%s)  =>  %s' % (node, action.state, shifted_node)
                shifted_nodes.append(shifted_node)

            current = shifted_nodes

            current = list(StackItem.merge(current))

            print '\n- STACK:'
            for node in current:
                print print_stack_item(node)

        print '\n--------------------\nACCEPTED:'
        for node in accepted_nodes:
            print_ast(node)

        return accepted_nodes
