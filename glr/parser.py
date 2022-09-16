from glr.grammar import Grammar
from glr.lr import generate_action_goto_table
from glr.stack import StackItem
from glr.tokenizer import Token
from glr.utils import format_stack_item, format_syntax_tree, format_rule


class Parser(object):
    def __init__(self, grammar, log_level=0):
        assert isinstance(grammar, Grammar)
        self.grammar = grammar
        self.action_goto_table = generate_action_goto_table(self.grammar)
        self.log_level = log_level

    def log(self, level, pattern, *args):
        if level <= self.log_level:
            print(pattern % args)

    def get_by_action_type(self, nodes, token, action_type):
        for node in nodes:
            node_actions = self.action_goto_table[node.state][token.symbol]
            for action in node_actions:
                if action.type == action_type:
                    yield node, action

    # http://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=DBFD4413CFAD29BC537FD98959E6B779?doi=10.1.1.39.1262&rep=rep1&type=pdf
    def parse(self, reduce_by_tokens_params, full_math=False, reduce_validator=None):
        accepted_nodes = []

        current = [StackItem.start_new()] if full_math else []

        for token_index, token in enumerate(reduce_by_tokens_params):
            self.log(1, '\n\nTOKEN: %s', token)

            reduce_by_tokens = [token]

            if not full_math:
                if token.symbol not in self.grammar.terminals:
                    self.log(1, '- Not in grammar, interpret as end of stream')
                    reduce_by_tokens = []

                # If not full match on each token we assume rule may start or end
                current.append(StackItem.start_new())
                if token.symbol != '$':
                    reduce_by_tokens.append(Token('$'))

            for reduce_by_token in reduce_by_tokens:
                process_reduce_nodes = current[:]
                while process_reduce_nodes:
                    new_reduce_nodes = []
                    for node, action in self.get_by_action_type(process_reduce_nodes, reduce_by_token, 'R'):
                        rule = self.grammar[action.rule_index]
                        self.log(1, '- REDUCE: (%s) by (%s)', node, format_rule(rule))
                        reduced_nodes = node.reduce(self.action_goto_table, rule, reduce_validator)
                        new_reduce_nodes.extend(reduced_nodes)
                        for n in reduced_nodes:
                            self.log(1, '    %s', format_stack_item(n, '     '))
                    process_reduce_nodes = new_reduce_nodes
                    current.extend(new_reduce_nodes)

                for node, action in self.get_by_action_type(current, reduce_by_token, 'A'):
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
                self.log(1, '    %s', format_stack_item(node, '     '))

        self.log(1, '\n--------------------\nACCEPTED:')
        for node in accepted_nodes:
            self.log(1, '%s', format_syntax_tree(node.syntax_tree))

        return [node.syntax_tree for node in accepted_nodes]
