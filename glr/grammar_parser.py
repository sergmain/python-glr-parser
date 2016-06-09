# coding=utf8
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

    def _scan_rules(self, grammar):
        syntax_trees = self.parser.parse(self.lr_grammar_tokenizer.scan(grammar))
        if len(syntax_trees) > 1:
            raise Exception('Ambiguous grammar')

        for rule in flatten_syntax_tree(syntax_trees[0], 'Rule'):
            left_symbol = rule.children[0].token.input_term
            for option in flatten_syntax_tree(rule.children[2], 'Option'):
                symbols = []
                weight = float(
                    option.children[1].token.input_term[1:-1].replace(',', '.')) if option.rule_index == 6 else None
                for symbol in flatten_syntax_tree(option, 'Symbol'):
                    if symbol.rule_index == 11:
                        symbols.append((symbol.children[0].token.input_term, ''))
                    elif symbol.rule_index == 12:
                        symbols.append((symbol.children[0].token.input_term[1:-1], 'raw'))
                    elif symbol.rule_index == 10:
                        symbols.append((symbol.children[0].token.input_term,
                                        symbol.children[1].token.input_term[1:-1]))
                yield left_symbol, weight, symbols

    def parse(self, grammar, start='S'):
        rules = [Rule(0, '@', (start,), False, ('',), 1.0)]
        for left_symbol, weight, symbols in self._scan_rules(grammar):
            if len(symbols) > 0:
                rules.append(Rule(len(rules), left_symbol, tuple(s for s, l in symbols), False, tuple(l for s, l in symbols), weight or 1.0))
            else:
                raise Exception('GLR parser does not support epsilon free rules')

        return Grammar(rules)