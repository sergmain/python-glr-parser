# -*- coding: utf-8 -*-
from glr_parser import GLRParser
from glrengine.parser import make_rules

dictionaries = {
    u"CLOTHES": [u"куртка", u"пальто", u"шубы"]
}

grammar = u"""
    S = adj<agr-gnc=1> CLOTHES
"""

gr = u"""
    S = adj<agr-gnc=1> CLOTHES


        Word = word
        Word = noun
        Word = adj
        Word = verb
        Word = pr
        Word = dpr
        Word = num
        Word = adv
        Word = pnoun
        Word = prep
        Word = conj
        Word = prcl
        Word = lat
    
CLOTHES = 'куртка' | 'пальто' | 'шуба'
"""

kws = [
    "word",
    "number",
    "space",
    "newline",
    "dot",
    "comma",
    "colon",
    "percent",
    "quote",
    "brace",
    "$"
]

for x in make_rules('S', gr, set(kws)):
    print(x)



glr = GLRParser(grammar, dictionaries=dictionaries, debug=False)

text = u"на вешалке висят пять красивых курток и вонючая шуба"
for parsed in glr.parse(text):
    print("FOUND:", parsed)
