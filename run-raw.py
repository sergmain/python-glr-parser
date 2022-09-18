# coding=utf-8

from glr.automation import Automation
from glr.utils import *

grammar = u"""
S = 'Б'
"""

text = u"на Б серое"

automation = Automation(grammar, None, 'S')

print( format_grammar(automation.grammar))
print( format_tokens(automation.lexer.scan(text)))
print( format_action_goto_table(automation.parser.action_goto_table))
automation.parser.log_level = 0
parsed = automation.parse(text)
for syntax_tree in parsed:
    print(format_syntax_tree(syntax_tree))

