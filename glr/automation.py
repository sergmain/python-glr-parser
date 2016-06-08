from glr.grammar_parser import parse_grammar
from glr.lexer import MorphologyLexer
from glr.parser import Parser
from glr.tokenizer import WordTokenizer


class Automation(object):

    def __init__(self, grammar_text):
        self.tokenizer = WordTokenizer()
        self.lexer = MorphologyLexer()
        self.grammar = parse_grammar(grammar_text, self.tokenizer.symbols.union({'$'}), 'S')
        self.parser = Parser(self.grammar)

    def parse(self, text):

        def validator(rule, tokens):
            return True

        tokens = list(self.lexer.scan(self.tokenizer.scan(text)))

        return self.parser.parse(tokens, validator)
