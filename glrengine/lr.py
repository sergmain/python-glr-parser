# -*- coding: utf-8 -*-
from collections import defaultdict, OrderedDict
from collections import namedtuple
from itertools import ifilter, imap, izip

from glrengine import GLRScanner
from glrengine.rules import RuleSet

Item = namedtuple('Item', ['rule_index', 'dot_position'])


def expand_item(item, R):
    rule = R[item[0]]
    return rule[1], item[1], rule[0]


def expand_itemset(itemset, R):
    return imap(lambda x: expand_item(x, R), itemset)


def expand_itemset2(itemset, R):
    for item in itemset:
        rule = R[item[0]]
        yield item[0], rule[1], item[1], rule[0]


def itemstr(item, R):
    e, i, n = expand_item(item, R)
    return ("[%s -> %s . %s" % (n, ' '.join(e[:i]), ' '.join(e[i:]))).strip() + ']'


def itemsetstr(itemset, R, label=''):
    items = map(lambda x: itemstr(x, R), sorted(itemset))
    width = reduce(lambda a, b: max(a, len(b)), items, 3)
    label = label and '[' + unicode(label) + ']' or ''
    build = ["+-%s%s-+" % (label, '-' * (width - len(label)))]
    build.extend("| %-*s |" % (width, item) for item in items)
    build.append("+-" + "-" * width + '-+')
    return '\n'.join(build)


def iterate_lookaheads(itemset, rules):
    for item in itemset:
        rule = rules[item.rule_index]

        if item.dot_position == len(rule.elements):
            # dot is in the end, there is no look ahead symbol
            continue

        lookahead = rule.elements[item.dot_position]

        yield item, lookahead


def first(itemset, rules):
    """
        Set of the tokens at the right of each dot in this item set
    """
    result = set()
    for item, lookahead in iterate_lookaheads(itemset, rules):
        if not lookahead in rules:
            result.add(lookahead)
    return result

def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def follow(itemset, rules):
    """
        All transitions from an item set in a dictionary [token]->item set
    """
    result = OrderedDict()
    for item, lookahead in iterate_lookaheads(itemset, rules):
        tmp = closure([Item(item.rule_index, item.dot_position + 1)], rules)

        if lookahead not in result:
            result[lookahead] = []
        result[lookahead].extend(tmp)

    for lookahead, itemset in result.iteritems():
        yield lookahead, unique(itemset)


def closure(itemset, rules):
    """
        The epsilon-closure of this item set
    """
    items_to_process = itemset
    visited_lookaheads = set()
    while True:
        for item in items_to_process:
            yield item

        nested_to_process = []
        for item, lookahead in iterate_lookaheads(items_to_process, rules):
            if lookahead in rules and lookahead not in visited_lookaheads:
                visited_lookaheads.add(lookahead)
                for rule_index in rules[lookahead]: # TODO: get_by_symbol
                    nested_to_process.append(Item(rule_index, 0))

        if not nested_to_process:
            # no changes
            return

        items_to_process = nested_to_process


Node = namedtuple('Node', ['index', 'itemset', 'follow_dict', 'parent_rule_index', 'parent_lookahead'])
Action = namedtuple('Action', ['action', 'rule_index'])

def generate_graph(rules):
    assert isinstance(rules, RuleSet)

    nodes = []
    node_by_itemset = {}

    first_itemset = closure([Item(0, 0)], rules)
    first_itemset = tuple(sorted(first_itemset))
    stack = [(None, None, first_itemset)]
    while stack:
        parent_node_index, parent_lookahead, itemset = stack.pop(0)

        node = Node(len(nodes), itemset, defaultdict(set), parent_node_index, parent_lookahead)
        nodes.append(node)
        node_by_itemset[node.itemset] = node

        print '%2s | %9s | %2d | %s' % (parent_node_index or 0, parent_lookahead or '', node.index, node.itemset)

        if parent_node_index is not None:
            nodes[parent_node_index].follow_dict[parent_lookahead].add(node.index)

        for lookahead, itemset in follow(node.itemset, rules):
            itemset = tuple(sorted(itemset))
            if itemset not in node_by_itemset:
                # Add new state, follow links will be added when it popped from the stack
                stack.append((node.index, lookahead, itemset))
            else:
                # State already exist, just add follow link
                child_node = node_by_itemset[itemset]
                node.follow_dict[lookahead].add(child_node.index)
                print '%2s | %9s | %2d | %s' % (node.index, lookahead, child_node.index, '')
    return nodes


def generate_followers(rules):
    symbols = unique(e for r in rules.values() if not isinstance(r, set) for e in r.elements)
    nonterminals = set(s for s in symbols if s in rules)

    def get_starters(symbol):
        result = []
        for rule_index in rules[symbol]:  # TODO: use get_by_symbol
            rule = rules[rule_index]
            if rule.elements[0] in nonterminals:
                if rule.elements[0] != symbol:
                    result.extend(get_starters(rule.elements[0]))
            else:
                result.append(rule.elements[0])
        return result

    starters = dict((s, set(get_starters(s))) for s in nonterminals)

    def get_followers(symbol):
        result = []
        for rule in rules.values():
            if isinstance(rule, set):  # TODO: remove warkaround
                continue

            if symbol not in rule.elements:
                continue

            index = rule.elements.index(symbol)
            if index + 1 == len(rule.elements):
                if rule.name != symbol:
                    result.extend(get_followers(rule.name))
            else:
                next = rule.elements[index+1]
                if next in nonterminals:
                    result.extend(starters[next])
                else:
                    result.append(next)
        return result

    followers = dict((s, set(get_followers(s))) for s in nonterminals)
    return followers


def generate_tables(rules):
    nodes = generate_graph(rules)
    followers = generate_followers(rules)

    result = []
    for node in nodes:
        actions = defaultdict(list)

        # Reduces
        for item in node.itemset:
            rule = rules[item.rule_index]
            if item.dot_position == len(rule.elements):
                if rule.name == '@':
                    actions['$'].append(Action('A', 0))
                else:
                    for follower in followers[rule.name]:
                        actions[follower].append(Action('R', item.rule_index))
                    actions['$'].append(Action('R', item.rule_index))

        # Shifts
        for lookahead, node_indexes in node.follow_dict.items():
            for node_index in node_indexes:
                child_node = nodes[node_index]
                actions[lookahead].append(Action('' if lookahead in followers else 'S', child_node.index))

        result.append(actions)
    return result



def old(rules):
    nodes = []
    node_by_itemset = {}

    first_node = Node(0, closure([Item(0, 0)], rules), {})

    LR0 = set()
    x = closure([Item(0, 0)], rules)
    stack = [tuple(sorted(x))]
    while stack:
        x = stack.pop()
        LR0.add(x)
        F = follow(x, rules)
        for t, s in F.iteritems():
            s = tuple(sorted(s))
            if s not in LR0:
                stack.append(s)
    LR0 = list(sorted(LR0))

    LR0_idx = {}
    for i, s in enumerate(LR0):
        LR0_idx[s] = i

    GOTO = []
    for s in LR0:
        f = {}
        for tok, dest in follow(s, rules).iteritems():
            f[tok] = LR0_idx[tuple(sorted(closure(dest, rules)))]
        GOTO.append(f)


    ACTION = []
    for s, g in izip(LR0, GOTO):
        action = defaultdict(list)

        # свертки
        for item in ifilter(lambda item: item.dot_position == len(rules[item.rule_index].elements), s):
            if not item.rule_index:
                action['$'].append(('A', 0))
            # else:
            #     for kw in self.following_tokens(item):
            #         action[kw].append(('R', item.rule_index))

        # переносы
        for tok, dest in g.iteritems():
            action[tok].append(('S', dest))

        # commit
        ACTION.append(action)

    return ACTION, GOTO, LR0

def kernel(itemset):
    """
        The kernel items in this item set
    """
    return set(ifilter(lambda (r, i): not r or i, itemset))



dictionaries = {
    u"VARIABLES": [u"A", u"B", u"C"]
}

grammar = u"""
S = Sums
Sums = Sums 'plus' Products
Sums = Products
Products = Products 'mul' Value
Products = Value
Value = number
Value = VARIABLES
"""

class GrammarParser(object):
    DEFAULT_PARSER = {
        "word": r"[\w\d_-]+",
        "number": r"[\d]+",
        "space": r"[\s]+",
        "newline": r"[\n]+",
        "dot": r"[\.]+",
        "comma": r"[,]+",
        "colon": r"[:]+",
        "percent": r"[%]+",
        "quote": r"[\"\'«»`]+",
        "brace": r"[\(\)\{\}\[\]]+",
    }

    DEFAULT_PARSER_DISCARD_NAMES = ["space"]

    DEFAULT_GRAMMAR = """
        Word = word
        Word = noun
        Word = adj
        Word = verb
        Word = pr
        Word = dpr
        Word = num
        Word = adv
        Word = pnoun
        Word = prep
        Word = conj
        Word = prcl
        Word = lat
    """

    def parse_grammar(self, grammar, dictionaries):
        grammar_rules = u"%s\n%s" % (grammar, self.DEFAULT_GRAMMAR)
        if dictionaries:
            # превращает {k: [a, b, c]} -> "k = 'a' | 'b' | 'c'"
            for dict_name, dict_words in dictionaries.items():
                morphed = []
                for word in dict_words:
                    # morphed.append(morph_parser.normal(word))
                    morphed.append(word)
                grammar_rules += u"\n%s = '%s'" % (dict_name, "' | '".join(morphed))

        parser_rules = self.DEFAULT_PARSER
        parser_rules.update({"discard_names": self.DEFAULT_PARSER_DISCARD_NAMES})
        return parser_rules

parser_rules = GrammarParser().parse_grammar(grammar, dictionaries)

# for k,v in parser_rules.items():
#     print k , v

scanner = GLRScanner(**parser_rules)
rules = RuleSet(grammar, set(scanner.tokens.keys()).union({'$'}), 'S')

nodes = generate_graph(rules)
t = generate_tables(rules)

symbols = sorted(unique(k for row in t for k in row.keys()))
print '\n # |',
for k in symbols:
    print '%-9s|' % k,
for i, row in enumerate(t):
    print '\n%2d |' % i,
    for k in symbols:
        print '%-9s|' % (', '.join('%s%s' % a for a in row[k]) if k in row else ''),

folowers = generate_followers(rules)
print folowers