# coding=utf-8
def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def print_table(table, buf):
    col_widths = [0] * len(table[0])
    for row in table:
        for j, cell in enumerate(row):
            col_widths[j] = max(col_widths[j], len(str(cell)))

    def print_row(i, chars, row=None):
        if i > 0 and i % 2 == 0:
            buf.write('\033[48;5;236m')
        for j, cell in enumerate(row or col_widths):
            if j == 0:
                buf.write(chars[0:2])

            if row:
                buf.write(str(cell).ljust(col_widths[j]))
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
            print_row(i, u'└─┴─┘')


def gen_printable_table(action_table):
    table = []
    symbols = unique(k for row in action_table for k in row.keys())

    def sort_key(symbol):
        actions = [a for row in action_table if symbol in row for a in row[symbol]]
        has_goto = any(a.type == 'G' for a in actions)
        min_state = min([a.state for a in actions if a.state] or [1000])
        return (has_goto, min_state)

    symbols = sorted(symbols, key=sort_key)
    table.append([''] + symbols)
    for i, row in enumerate(action_table):
        res = [i]
        for k in symbols:
            res.append(', '.join('%s%s%s' % (a if a != 'G' else '', s or '', r or '') for a, s, r in row[k]) if k in row else '')
        table.append(res)
    return table


def print_stack_item(stack_item, second_line_prefix=''):
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


def gen_ast(node, last=False, prefix=''):
    line = prefix[:-1]
    if prefix:
        if not last:
            line += u'├──'
        else:
            line += u'╰──'
    else:
        line = '  '
    line += node.token.symbol
    yield line, node.token.value

    if node.reduced:
        for i, r in enumerate(node.reduced):
            last = i == len(node.reduced) - 1
            for line, value in gen_ast(r, last, prefix + ('   ' if last else u'  │')):
                yield line, value


def print_ast(node):
    ast = list(gen_ast(node))
    depth = max(len(l) for l, v in ast)
    for l, v in ast:
        print l.ljust(depth, u'.' if v else u' '), v


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
