# -*- coding: utf-8 -*-
from glr_parser import GLRParser

import pymorphy2

print(list(pymorphy2.analyzer._lang_dict_paths().keys()))

dictionaries = {
    u"CITY": [u"san-francisco"]
}

grammar = u"""
    S = adj<agr-gnc=1> CITY
"""

glr = GLRParser(grammar, dictionaries=dictionaries, debug=False)

text = u"today i'm in cool san-francisco"
for parsed in glr.parse(text):
    print("FOUND:", parsed)
