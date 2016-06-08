# -*- coding: utf-8 -*-
import pymorphy2

from glr.tokenizer import Token


class MorphologyLexer(object):
    TAG_MAPPER = {
        "NOUN": "noun",
        "ADJF": "adj",
        "ADJS": "adj",
        "COMP": "adj",
        "VERB": "verb",
        "INFN": "verb",
        "PRTF": "pr",
        "PRTS": "pr",
        "GRND": "dpr",
        "NUMR": "num",
        "ADVB": "adv",
        "NPRO": "pnoun",
        "PRED": "adv",
        "PREP": "prep",
        "CONJ": "conj",
        "PRCL": "prcl",
        "INTJ": "noun",
        "LATN": "lat",
        "NUMB": "num"
    }

    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()

    def scan(self, tokens):
        for token in tokens:
            assert isinstance(token, Token)

            if token.symbol == 'word':
                morphed = self.morph.parse(token.value)
                if morphed:
                    token = Token(
                        symbol=self.TAG_MAPPER.get(morphed[0].tag.POS) or token.symbol,
                        value=morphed[0].normal_form,
                        start=token.start,
                        end=token.end,
                        input_term=token.value,
                        params=morphed[0].tag
                    )
            yield token

    def normal(self, word):
        morphed = self.morph.parse(word)
        if morphed:
            return morphed[0].normal_form
        return word

    def parse_tags(self, word):
        parsed = self.morph.parse(word)
        if not parsed:
            return None
        return parsed[0].tag

morphology_lexer = MorphologyLexer()


