from glr.grammar_parser import GrammarParser
from glr.labels import LABELS_CHECK
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
            rule = self.grammar[syntax_tree.rule_index]
            tokens = [child.token for child in syntax_tree.children]
            for i, token in enumerate(tokens):
                params = rule.params[i]
                for label_key, label_values in params.iteritems():
                    for label_value in label_values:
                        ok = LABELS_CHECK[label_key](label_value, tokens, i)
                        if not ok:
                            #print 'Label failed: %s=%s for #%s in %s' % (label_key, label_value, i, tokens)
                            return False
            return True

        tokens = list(self.lexer.scan(text))

        return self.parser.parse(tokens, full_math, validator)
