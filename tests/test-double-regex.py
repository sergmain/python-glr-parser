# coding=utf-8

from glr.automation import Automation
from glr.utils import *

grammar = u"""
            S = DAY_MONTH
            DAY_MONTH = word<regex=^([0-9][0-9])$> word<regex=^([a-z]+)$>
"""

text = u"12345 12 abc 2022 987654321"

automation = Automation(grammar, None, 'S')

print( format_grammar(automation.grammar))
print( format_tokens(automation.lexer.scan(text)))
print( format_action_goto_table(automation.parser.action_goto_table))
automation.parser.log_level = 0
parsed = automation.parse(text)
if not parsed:
    raise 'nothing was found'

for syntax_tree in parsed:
    print(format_syntax_tree(syntax_tree))

