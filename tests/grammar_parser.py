"""
>>> from glr.utils import *
>>> from glr.grammar_parser import GrammarParser

Test spacing options
>>> text = '''
... S = a
... S=b
... S =c
... S= d
...  S = e
... \t\tS = f
... S =
...         g
... S = a b
... S = c
...         d
... S = e        f
... S = g\t\th
... '''
>>> print( format_grammar(GrammarParser().set_log_level(0).parse(text)) )
#0: @ = S
#1: S = a
#2: S = b
#3: S = c
#4: S = d
#5: S = e
#6: S = f
#7: S = g
#8: S = a b
#9: S = c d
#10: S = e f
#11: S = g h

Test variations of specifying alternatives
>>> text = '''
... S = a
... S = b
... S = c | d
... S = e|f
... S = g
...     |h
...     | i
... S = j
... \t\t|k
... \t\t|\tl
... '''
>>> print( format_grammar(GrammarParser().parse(text)) )
#0: @ = S
#1: S = a
#2: S = b
#3: S = c
#4: S = d
#5: S = e
#6: S = f
#7: S = g
#8: S = h
#9: S = i
#10: S = j
#11: S = k
#12: S = l

Test rule weight
>>> text = '''
... S = a (2)
... S = b (3.0)
... S = c (4,0)
... S = d (5) | e (6)
... S = f(7) |g(8)|h (9)
... S = i (0.001)
... '''
>>> print( format_grammar(GrammarParser().parse(text)) )
#0: @ = S
#1: S = a   (2)
#2: S = b   (3)
#3: S = c   (4)
#4: S = d   (5)
#5: S = e   (6)
#6: S = f   (7)
#7: S = g   (8)
#8: S = h   (9)
#9: S = i   (0.001)

Test symbol parameters
>>> text = '''
... S = a<a=1,b,c=val>
... S = b < a = 1 , b , c  = val >
... S = 'ccc' ' c c '
... S = "ddd" " d d "
... '''
>>> print( format_grammar(GrammarParser().parse(text)) )
#0: @ = S
#1: S = a<a=1,b,c=val>
#2: S = b<a=1,b,c=val>
#3: S = "ccc" "c c"
#4: S = "ddd" "d d"

Test end to end
>>> text = '''
...     S = NP VP | S PP
...     NP = pnoun (1.2)
...          | noun
...          | adj noun noun (4,5)
...          | NP PP
...     PP = prep NP (2)
...     VP = verb<a=1,b> NP <a> (0.5)
...     NP = 'test' "one two"
...     '''
>>> print( format_grammar(GrammarParser().parse(text)) )
#0: @  = S
#1: S  = NP VP
#2: S  = S PP
#3: NP = pnoun   (1.2)
#4: NP = noun
#5: NP = adj noun noun   (4.5)
#6: NP = NP PP
#7: PP = prep NP   (2)
#8: VP = verb<a=1,b> NP<a>   (0.5)
#9: NP = "test" "one two"
>>> text = ''''''
"""
