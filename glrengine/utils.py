# coding=utf-8
from glrengine.lr import unique


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
    symbols = sorted(symbols, key=lambda x: (x[0].isupper(), x))
    table.append([''] + symbols)
    for i, row in enumerate(action_table):
        res = [i]
        for k in symbols:
            res.append(', '.join('%s%s%s' % (a,s or '',r or '') for a,s,r in row[k]) if k in row else '')
        table.append(res)
    return table



def gen_ast(node, last=False, prefix = ''):
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
            last = i==len(node.reduced)-1
            for line, value in gen_ast(r, last, prefix + ('   ' if last else u'  │')):
                yield line, value


def print_ast(node):
    ast = list(gen_ast(node))
    depth = max(len(l) for l, v in ast)
    for l, v in ast:
        print l.ljust(depth,u'─' if v else u' '), v