# -*- coding: utf-8 -*-
from glr_parser import GLRParser

dictionaries = {
    u"CLOTHES": [u"куртка", u"пальто", u"шубы"]
}

grammar = u"""
    S = adj<agr-gnc=1> CLOTHES
"""

glr = GLRParser(grammar, dictionaries=dictionaries, debug=True)

text = u"на вешалке висят пять красивых курток и вонючая шуба"
for parsed in glr.parse(text):
    print("FOUND:", parsed)
