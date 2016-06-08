# coding=utf8
from collections import defaultdict

from glr.grammar import Rule, Grammar
from glr.tokenizer import SimpleRegexTokenizer


class GrammarParser(object):

    lr_grammar_tokenizer = SimpleRegexTokenizer(dict(
        sep='=',
        alt='[|]',
        word=r"\b\w+\b",
        raw=r"\'[^\s']+\'",
        whitespace=r'[ \t\r\n]+',
        minus=r'[-]',
        label=r'\<.+?\>',
    ), ['whitespace'])

    def _scan_rules(self, grammar, start):
        words = [start]
        labels = []
        edit_rule = '@'
        edit_rule_commit = True
        next_edit_rule_commit = True
        for token in self.lr_grammar_tokenizer.scan(grammar):
            if token.symbol == 'minus':
                next_edit_rule_commit = False
            if token.symbol == 'word' or token.symbol == 'raw':
                words.append(token.value)
                labels.append(None)
            elif token.symbol == 'alt':
                yield (edit_rule, tuple(words), edit_rule_commit, labels[1:-1])
                words = []
                labels = []
            elif token.symbol == 'sep':
                tmp = words.pop()
                yield (edit_rule, tuple(words), edit_rule_commit, labels[1:-1])
                edit_rule_commit = next_edit_rule_commit
                next_edit_rule_commit = True
                edit_rule = tmp
                words = []
                labels = [None]
            elif token.symbol == 'label':
                # "a=b, b=c, d" -> {"a": "b", "b": "c", "d": None}
                token_value = token.value.strip().replace(" ", "")
                label = defaultdict(list)
                for l in token_value[1:-1].split(","):
                    key, value = tuple(l.split("=", 1) + [None])[:2]
                    label[key].append(value)
                # label = dict([tuple(l.split("=", 1) + [None])[:2] for l in tokvalue[1:-1].split(",")])
                labels[-1] = label
        yield (edit_rule, tuple(words), edit_rule_commit, labels[1:-1])

    def parse(self, grammar, start='S'):
        rules = []
        for rulename, elems, commit, labels in self._scan_rules(grammar, start):
            if len(elems) > 0:
                #TODO: support weight parsing
                rules.append(Rule(len(rules), rulename, elems, commit, labels, 1.0))
            else:
                raise Exception('GLR parser does not support epsilon free rules')

        return Grammar(rules)