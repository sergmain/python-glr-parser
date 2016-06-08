from glr.grammar_parser import GrammarParser
from glr.lexer import MorphologyLexer
from glr.parser import Parser
from glr.tokenizer import WordTokenizer


class Automation(object):

    def __init__(self, grammar_text):
        self.tokenizer = WordTokenizer()
        self.lexer = MorphologyLexer()
        self.grammar_parser = GrammarParser()

        self.grammar = self.grammar_parser.parse(grammar_text, 'S')
        self.parser = Parser(self.grammar)

    def parse(self, text):

        def validator(syntax_tree):
            return True

        tokens = list(self.lexer.scan(self.tokenizer.scan(text)))

        return self.parser.parse(tokens, validator)
