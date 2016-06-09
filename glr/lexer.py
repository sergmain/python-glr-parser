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

    def __init__(self, tokenizer, dictionaries=None):
        self.tokenizer = tokenizer
        self.morph = pymorphy2.MorphAnalyzer()

        self.dictionary = {}
        if dictionaries:
            for category, values in dictionaries.iteritems():
                for value in values:
                    value = self.normal(value)
                    if value in self.dictionary:
                        raise Exception('Duplicate value in dictionaries %s and %s' % (category, self.dictionary[value]))
                    self.dictionary[value] = category

    def scan(self, text):
        for token in self.tokenizer.scan(text):
            assert isinstance(token, Token)

            if token.symbol == 'word':
                morphed = self.morph.parse(token.value)
                if morphed:
                    value = morphed[0].normal_form
                    if value in self.dictionary:
                        token = Token(
                            symbol=self.dictionary[value],
                            value=value,
                            start=token.start,
                            end=token.end,
                            input_term=token.input_term,
                            params=morphed[0].tag
                        )
                    else:
                        token = Token(
                            symbol=self.TAG_MAPPER.get(morphed[0].tag.POS) or token.symbol,
                            value=value,
                            start=token.start,
                            end=token.end,
                            input_term=token.input_term,
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
