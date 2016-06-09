"""
>>> from glr.utils import *
>>> from glr.grammar_parser import GrammarParser
>>> text = '''
...     S = NP VP | S PP
...     NP = pnoun (1.2)
...          | noun
...          | adj noun noun (4,5)
...          | NP PP
...     PP = prep NP (2)
...     VP = verb<a=1,b> NP <a>
...     NP = 'test' "test"
...     '''
>>> print format_grammar(GrammarParser().parse(text, 'S'))
#0: @  = S
#1: S  = NP VP
#2: S  = S PP
#3: NP = pnoun   (1.2)
#4: NP = noun
#5: NP = adj noun noun   (4.5)
#6: NP = NP PP
#7: PP = prep NP   (2)
#8: VP = verb<a=1,b> NP<a>
#9: NP = test<raw> test<raw>
>>> text = ''''''
"""