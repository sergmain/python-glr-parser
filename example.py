# -*- coding: utf-8 -*-
from glr import GLRParser


dictionaries = {
    u"VARIABLES": [u"A", u"B", u"C"]
}

grammar = u"""
S = Sums
Sums = Sums 'plus' Products
Sums = Products
Products = Products 'mul' Value
Products = Value
Value = num
Value = VARIABLES
"""

glr = GLRParser(grammar, dictionaries=dictionaries, debug=True)

text = u"A mul 2 plus 1"
for parsed in glr.parse(text):
    print "FOUND:", parsed
