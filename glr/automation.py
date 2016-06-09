from glr.grammar_parser import GrammarParser
from glr.lexer import MorphologyLexer
from glr.parser import Parser
from glr.tokenizer import WordTokenizer


class Automation(object):

    def __init__(self, grammar_text, start='S'):
        self.tokenizer = WordTokenizer()
        self.lexer = MorphologyLexer(self.tokenizer)
        self.grammar_parser = GrammarParser()

        self.grammar = self.grammar_parser.parse(grammar_text, start)
        self.parser = Parser(self.grammar)

    def parse(self, text, full_math=False):

        def validator(syntax_tree):
            return True

        tokens = list(self.lexer.scan(text))

        return self.parser.parse(tokens, full_math, validator)
