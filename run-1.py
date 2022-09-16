# coding=utf-8

from glr.automation import Automation
from glr.utils import *

# TODO: validate symbols matching in tokenizer and grammar
# TODO: calculate overall probability of syntax tree from rule weight
# TODO: support multiple tokens per position (to resolve morph ambiguity and dictionary ambiguity)
# TODO: support token lattice (resolve combined and split tokens ambiguity)

dictionaries = {
    u"CLOTHES": [u"куртка", u"пальто", u"шубы"]
}

grammar = u"""
S = r1
S = r2
r1 = CLOTHES adj<agr-gnc=-1>
r2 = adj<agr-gnc=1> CLOTHES
"""

text = u"на вешалке висят пять красивых курток и вонючая шуба, а также пальто серое"

automation = Automation(grammar, dictionaries, 'S')

print( format_grammar(automation.grammar))
print( format_tokens(automation.lexer.scan(text)))
print( format_action_goto_table(automation.parser.action_goto_table))
automation.parser.log_level = 0
parsed = automation.parse(text)
for syntax_tree in parsed:
    print(format_syntax_tree(syntax_tree))

