# coding=utf-8

from glr.automation import Automation
from glr.utils import *

grammar = u"""
        S = FULL_YEAR_DATE
            Word = word
            Word = noun
                FULL_YEAR_DATE = DAY_MONTH word<regex=^(\d{4})$>
                FULL_YEAR_DATE = DAY_MONTH YEAR_AND_NAME
                DAY_MONTH = word<regex=^([0-9][0-9])$> MONTH
                YEAR_AND_NAME = word<regex=^(\d{4})$> Word<regex=^(гг.|год[а]?|г.)$>
"""

dictionaries = {
    u"MONTH": [u"декабрь"]
}

text = u"20 декабря 2018 года"

automation = Automation(grammar, dictionaries, 'S')

print( format_grammar(automation.grammar))
print( format_tokens(automation.lexer.scan(text)))
print( format_action_goto_table(automation.parser.action_goto_table))
automation.parser.log_level = 0
parsed = automation.parse(text)
if not parsed:
    raise 'nothing was found'

for syntax_tree in parsed:
    print(format_syntax_tree(syntax_tree))

