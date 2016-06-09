# coding=utf-8
ur"""
Example from Tomita's whitepaper
>>> text = '''
... S = NP VP
... S = S PP
... NP = n
... NP = det n
... NP = NP PP
... PP = prep NP
... VP = v NP
... '''
>>> grammar = GrammarParser().parse(text)
>>> print format_grammar(grammar)
#0: @  = S
#1: S  = NP VP
#2: S  = S PP
#3: NP = n
#4: NP = det n
#5: NP = NP PP
#6: PP = prep NP
#7: VP = v NP
>>> print format_states(generate_state_graph(grammar), grammar)
┌────┬──────┬────┬────────────────────────────────────────────────────────────────────────┐
│ Go │ to   │ St │ Closure                                                                │
├────┼──────┼────┼────────────────────────────────────────────────────────────────────────┤
│ 0  │      │ 0  │ @ -> .S; S -> .NP VP; S -> .S PP; NP -> .n; NP -> .det n; NP -> .NP PP │
│ 0  │ S    │ 1  │ @ -> S.; S -> S.PP; PP -> .prep NP                                     │
│ 0  │ NP   │ 2  │ S -> NP.VP; NP -> NP.PP; PP -> .prep NP; VP -> .v NP                   │
│ 2  │ prep │ 6  │                                                                        │
│ 0  │ n    │ 3  │ NP -> n.                                                               │
│ 0  │ det  │ 4  │ NP -> det.n                                                            │
│ 1  │ PP   │ 5  │ S -> S PP.                                                             │
│ 1  │ prep │ 6  │ NP -> .n; NP -> .det n; NP -> .NP PP; PP -> prep.NP                    │
│ 6  │ det  │ 4  │                                                                        │
│ 6  │ n    │ 3  │                                                                        │
│ 2  │ VP   │ 7  │ S -> NP VP.                                                            │
│ 2  │ PP   │ 8  │ NP -> NP PP.                                                           │
│ 2  │ v    │ 9  │ NP -> .n; NP -> .det n; NP -> .NP PP; VP -> v.NP                       │
│ 9  │ det  │ 4  │                                                                        │
│ 9  │ n    │ 3  │                                                                        │
│ 4  │ n    │ 10 │ NP -> det n.                                                           │
│ 6  │ NP   │ 11 │ NP -> NP.PP; PP -> .prep NP; PP -> prep NP.                            │
│ 11 │ PP   │ 8  │                                                                        │
│ 11 │ prep │ 6  │                                                                        │
│ 9  │ NP   │ 12 │ NP -> NP.PP; PP -> .prep NP; VP -> v NP.                               │
│ 12 │ PP   │ 8  │                                                                        │
│ 12 │ prep │ 6  │                                                                        │
└────┴──────┴────┴────────────────────────────────────────────────────────────────────────┘

>>> action_goto_table = generate_action_goto_table(grammar)
>>> print format_action_goto_table(action_goto_table)
┌────┬─────┬─────┬────────┬────┬────┬───┬────┬────┬────┐
│    │ n   │ det │ prep   │ v  │ $  │ S │ NP │ PP │ VP │
├────┼─────┼─────┼────────┼────┼────┼───┼────┼────┼────┤
│ 0  │ S3  │ S4  │        │    │    │ 1 │ 2  │    │    │
│ 1  │     │     │ S6     │    │ A  │   │    │ 5  │    │
│ 2  │     │     │ S6     │ S9 │    │   │    │ 8  │ 7  │
│ 3  │     │     │ R3     │ R3 │ R3 │   │    │    │    │
│ 4  │ S10 │     │        │    │    │   │    │    │    │
│ 5  │     │     │ R2     │    │ R2 │   │    │    │    │
│ 6  │ S3  │ S4  │        │    │    │   │ 11 │    │    │
│ 7  │     │     │ R1     │    │ R1 │   │    │    │    │
│ 8  │     │     │ R5     │ R5 │ R5 │   │    │    │    │
│ 9  │ S3  │ S4  │        │    │    │   │ 12 │    │    │
│ 10 │     │     │ R4     │ R4 │ R4 │   │    │    │    │
│ 11 │     │     │ R6, S6 │ R6 │ R6 │   │    │ 8  │    │
│ 12 │     │     │ R7, S6 │    │ R7 │   │    │ 8  │    │
└────┴─────┴─────┴────────┴────┴────┴───┴────┴────┴────┘

>>> action_goto_table = change_state_indexes(action_goto_table, {3: 4, 4: 3, 7: 8, 8: 9, 9: 7})
>>> print format_action_goto_table(action_goto_table)
┌────┬─────┬─────┬────────┬────┬────┬───┬────┬────┬────┐
│    │ det │ n   │ prep   │ v  │ $  │ S │ NP │ PP │ VP │
├────┼─────┼─────┼────────┼────┼────┼───┼────┼────┼────┤
│ 0  │ S3  │ S4  │        │    │    │ 1 │ 2  │    │    │
│ 1  │     │     │ S6     │    │ A  │   │    │ 5  │    │
│ 2  │     │     │ S6     │ S7 │    │   │    │ 9  │ 8  │
│ 3  │     │ S10 │        │    │    │   │    │    │    │
│ 4  │     │     │ R3     │ R3 │ R3 │   │    │    │    │
│ 5  │     │     │ R2     │    │ R2 │   │    │    │    │
│ 6  │ S3  │ S4  │        │    │    │   │ 11 │    │    │
│ 7  │ S3  │ S4  │        │    │    │   │ 12 │    │    │
│ 8  │     │     │ R1     │    │ R1 │   │    │    │    │
│ 9  │     │     │ R5     │ R5 │ R5 │   │    │    │    │
│ 10 │     │     │ R4     │ R4 │ R4 │   │    │    │    │
│ 11 │     │     │ R6, S6 │ R6 │ R6 │   │    │ 9  │    │
│ 12 │     │     │ R7, S6 │    │ R7 │   │    │ 9  │    │
└────┴─────┴─────┴────────┴────┴────┴───┴────┴────┴────┘
"""
from glr.grammar_parser import GrammarParser
from glr.lr import generate_state_graph, generate_action_goto_table
from glr.utils import *

