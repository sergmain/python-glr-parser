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

    def parse(self, text):

        def validator(syntax_tree):
            return True

        tokens = list(self.lexer.scan(text))

        # filter tokens, keep only symbols exist in grammar
        tokens = [token for token in tokens if token.symbol in self.grammar.terminals or token.symbol == '$']

        return self.parser.parse(tokens, validator)
