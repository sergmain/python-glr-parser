# coding=utf-8

import StringIO

from glr.stack import SyntaxTree


def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def format_table(table):
    buf = StringIO.StringIO()

    col_widths = [0] * len(table[0])
    for row in table:
        for j, cell in enumerate(row):
            col_widths[j] = max(col_widths[j], len(unicode(cell)))

    def print_row(i, chars, row=None):
        if i > 0 and i % 2 == 0:
            buf.write('\033[48;5;236m')
        for j, cell in enumerate(row or col_widths):
            if j == 0:
                buf.write(chars[0:2])

            if row:
                buf.write(unicode(cell).ljust(col_widths[j]))
            else:
                buf.write(chars[1] * col_widths[j])

            if j < len(col_widths) - 1:
                buf.write(chars[1:4])
            else:
                buf.write(chars[3:5])

        buf.write('\033[m')
        buf.write('\n')

    for i, row in enumerate(table):
        if i == 0:
            print_row(i, u'┌─┬─┐')
        elif i == 1:
            print_row(i, u'├─┼─┤')
        if True:
            print_row(i, u'│ │ │', row)
        if i == len(table) - 1:
            print_row(0, u'└─┴─┘')
    # TODO: do I need to close buffer?
    return buf.getvalue()


def format_action_goto_table(action_goto_table):
    table = []
    symbols = unique(k for row in action_goto_table for k in row.keys())

    def sort_key(symbol):
        actions = [a for row in action_goto_table if symbol in row for a in row[symbol]]
        has_goto = any(a.type == 'G' for a in actions)
        min_state = min([a.state for a in actions if a.state] or [1000])
        return has_goto, min_state

    symbols = sorted(symbols, key=sort_key)
    table.append([''] + symbols)
    for i, row in enumerate(action_goto_table):
        res = [i]
        for k in symbols:
            res.append(', '.join('%s%s%s' % (a if a != 'G' else '', s or '', r or '') for a, s, r in row[k]) if k in row else '')
        table.append(res)
    return format_table(table)


def format_rule(rule):
    right_symbols = [s + ('<%s>' % rule.params[i] if rule.params and rule.params[i] else '') for i, s in enumerate(rule.right_symbols)]
    return '#%d: %s -> %s %s' % (
        rule.index,
        rule.left_symbol,
        ' '.join(right_symbols),
        '(%s)' % rule.weight if rule.weight != 1.0 else '')


def format_grammar(grammar):
    max_symbol_len = max(len(s) for s in grammar.nonterminals)
    lines = []
    for r in grammar.rules:
        right_symbols = [s + ('<%s>' % r.params[i] if r.params[i] else '') for i, s in enumerate(r.right_symbols)]
        lines.append('%2d | %s -> %s   %s' % (
            r.index,
            r.left_symbol.ljust(max_symbol_len),
            ' '.join(right_symbols),
            '(%s)' % r.weight if r.weight != 1.0 else ''))
    return '\n'.join(lines)


def format_tokens(tokens):
    table = [('Sym', 'Value', 'Input', 'Params')]
    for token in tokens:
        table.append((token.symbol, token.value, token.input_term, token.params))
    return format_table(table)


def format_item(item, grammar):
    rule = grammar[item.rule_index]
    right_symbols = ''.join('.' + s if i == item.dot_position else ' ' + s for i, s in enumerate(rule.right_symbols))
    return '%s -> %s%s' % (rule.left_symbol, right_symbols.strip(), '.' if item.dot_position == len(rule.right_symbols) else '')


def format_itemset(itemset, grammar):
    return '; '.join(format_item(item, grammar) for item in itemset)


def format_states(states, grammar):
    table = [['Go', 'to', 'St', 'Closure']]

    state_index = set((state.parent_state_index, state.parent_lookahead, state.index) for state in states)
    for i, state in enumerate(states):

        table.append([
            state.parent_state_index or 0,
            state.parent_lookahead or '',
            state.index,
            format_itemset(state.itemset, grammar)
        ])

        for parent_lookahead, child_state_indexes in state.follow_dict.items():
            for child_state_index in child_state_indexes:
                if (i, parent_lookahead, child_state_index) not in state_index:
                    table.append([i, parent_lookahead, child_state_index, ''])
    format_table(table)


def format_stack_item(stack_item, second_line_prefix=''):
    def get_pathes(stack_item):
        if stack_item.prev:
            for prev in stack_item.prev:
                for p in get_pathes(prev):
                    yield p + [stack_item]
        else:
            yield [stack_item]

    if stack_item.prev:
        pathes = []
        for path in get_pathes(stack_item):
            pathes.append(' > '.join(repr(i) for i in path))
        length = max(len(p) for p in pathes)

        results = []
        for i, path in enumerate(pathes):
            result = '' if i == 0 else second_line_prefix
            result += path.rjust(length)
            if len(pathes) > 1:
                if i == 0:
                    result += ' ╮'
                elif i != len(pathes) - 1:
                    result += ' │'
                else:
                    result += ' ╯'
            results.append(result)

        return '\n'.join(results)
    else:
        return '0'


def generate_syntax_tree_lines(syntax_tree, last=False, prefix=''):
    line = prefix[:-1]
    if prefix:
        if not last:
            line += u'├──'
        else:
            line += u'╰──'
    else:
        line = '  '

    if syntax_tree.is_leaf():
        yield line + syntax_tree.symbol, syntax_tree.token.input_term
    else:
        yield line + syntax_tree.symbol, ''
        for i, r in enumerate(syntax_tree.children):
            last = i == len(syntax_tree.children) - 1
            for line, value in generate_syntax_tree_lines(r, last, prefix + ('   ' if last else u'  │')):
                yield line, value


def format_syntax_tree(syntax_tree):
    assert isinstance(syntax_tree, SyntaxTree)
    ast = list(generate_syntax_tree_lines(syntax_tree))
    depth = max(len(l) for l, v in ast)
    lines = []
    for l, v in ast:
        lines.append('%s %s' % (l.ljust(depth, '.' if v else ' '), v))
    return '\n'.join(lines)


def change_state_indexes(table, mapping):
    """
    Keeps table logically same, but updates rule indexes by switching mapping pairs
    :param table:
    :param mapping:
    :return:
    """
    from lr import Action

    reverse_map = dict((v, k) for k, v in mapping.items())
    result = [table[reverse_map.get(i, i)] for i in range(len(table))]
    for row in result:
        for symbol, actions in row.items():
            for i, action in enumerate(actions):
                if action.state in mapping:
                    actions[i] = Action(action.type, mapping[action.state], action.rule_index)
    return result


def flatten_syntax_tree(syntax_tree, symbol):
    """
    Recursively traverse syntax tree until finds searched symbol.
    If found does not go deeper.
    """
    if syntax_tree.symbol == symbol:
        yield syntax_tree
        return

    if syntax_tree.children:
        for child in syntax_tree.children:
            for res in flatten_syntax_tree(child, symbol):
                yield res
