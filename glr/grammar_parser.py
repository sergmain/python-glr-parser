# coding=utf8
from collections import defaultdict

from glr.grammar import Rule, Grammar
from glr.parser import Parser
from glr.tokenizer import SimpleRegexTokenizer
from glr.utils import flatten_syntax_tree, format_syntax_tree, format_tokens


class GrammarParser(object):
    lr_grammar_tokenizer = SimpleRegexTokenizer(dict(
        sep='=',
        alt='\|',
        word=r"\b\w+\b",
        raw=r"(?:'.+?'|\".+?\")",
        whitespace=r'[ \t\r\n]+',
        minus=r'-',
        label=r'<.+?>',
        weight=r'\(\d+(?:[.,]\d+)?\)',
    ), ['whitespace'])

    grammar = Grammar([
        Rule(0, '@', ('S',), False, None, 1.0),
        Rule(1, 'S', ('S', 'Rule'), False, None, 1.0),
        Rule(2, 'S', ('Rule',), False, None, 1.0),
        Rule(3, 'Rule', ('word', 'sep', 'Options'), False, None, 1.0),
        Rule(4, 'Options', ('Options', 'alt', 'Option'), False, None, 1.0),
        Rule(5, 'Options', ('Option',), False, None, 1.0),
        Rule(6, 'Option', ('Symbols', 'weight'), False, None, 1.0),
        Rule(7, 'Option', ('Symbols',), False, None, 1.0),
        Rule(8, 'Symbols', ('Symbols', 'Symbol'), False, None, 1.0),
        Rule(9, 'Symbols', ('Symbol',), False, None, 1.0),
        Rule(10, 'Symbol', ('word', 'label'), False, None, 1.0),
        Rule(11, 'Symbol', ('word',), False, None, 1.0),
        Rule(12, 'Symbol', ('raw',), False, None, 1.0),
    ])
    parser = Parser(grammar)

    @staticmethod
    def _parse_labels(labels_str):
        labels_str = labels_str.strip().replace(" ", "")
        labels = {}
        for key_value in labels_str.split(","):
            if '=' in key_value:
                key, value = tuple(key_value.split("=", 1))
                labels.setdefault(key, []).append(value)
            else:
                labels.setdefault(key_value, []).append(True)
        return labels

    def _scan_rules(self, grammar_str):
        syntax_trees = self.parser.parse(self.lr_grammar_tokenizer.scan(grammar_str))
        if len(syntax_trees) > 1:
            raise Exception('Ambiguous grammar')

        for rule_node in flatten_syntax_tree(syntax_trees[0], 'Rule'):
            left_symbol = rule_node.children[0].token.input_term

            for option_node in flatten_syntax_tree(rule_node.children[2], 'Option'):
                if option_node.rule_index == 6:
                    weight = float(option_node.children[1].token.input_term[1:-1].replace(',', '.'))
                else:
                    weight = 1.0

                right_symbols = []
                for symbol_node in flatten_syntax_tree(option_node, 'Symbol'):
                    if symbol_node.rule_index == 11:
                        right_symbols.append((symbol_node.children[0].token.input_term, dict()))
                    elif symbol_node.rule_index == 12:
                        right_symbols.append((symbol_node.children[0].token.input_term[1:-1], {'raw': True}))
                    elif symbol_node.rule_index == 10:
                        right_symbols.append((symbol_node.children[0].token.input_term,
                                             self._parse_labels(symbol_node.children[1].token.input_term[1:-1])))

                yield left_symbol, weight, right_symbols

    def parse(self, grammar, start='S'):
        rules = [Rule(0, '@', (start,), False, ('',), 1.0)]
        for left_symbol, weight, right_symbols in self._scan_rules(grammar):
            if len(right_symbols) > 0:
                rules.append(Rule(len(rules), left_symbol, tuple(s for s, l in right_symbols), False, tuple(l for s, l in right_symbols), weight))
            else:
                raise Exception('GLR parser does not support epsilon free rules')

        return Grammar(rules)