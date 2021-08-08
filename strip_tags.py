import sys

fname = sys.argv[1]

verbose = True
verbose = False
if verbose : print(f'{fname=}')

# READ
lines = []
with open(fname,'r') as f:
    for line in f:
        lines.append(line)

def removeOneTag(text, tag, opt=''):
    start = text.find("<"+tag + opt)
    length = text[start:].find("</"+tag+">") + len(tag) + 3
    # print(start, length)
    return text[:start] + text[(start+length):]

tags = ['line', 'circle', 'text', 'button', 'svg', ]
tags = ['svg', ]
div_classes = ["diagram", "diagram-content-container", ] #, "content-scroll", "diagram-container"]# in reverse hierarchical order
stripped_lines = []
for i_line, line in enumerate(lines):
    if verbose: print('i_line=', i_line)
    if verbose: print(f'before:{len(line)=}')
    for tag in tags:
        if verbose: print(f'{tag=}')
        while("<"+tag in line):
            line = removeOneTag(line, tag)
            #print(f'now:{len(line)=}')
    for div_class in div_classes:
        opt = f' class="{div_class}"'
        if verbose: print(f'{div_class=}, {opt=}')
        while('<div' + opt in line):
            line = removeOneTag(line, 'div', opt=opt)
            # print(f'now:{len(line)=}')
    # while(f'<div>' in line):
    #         line = removeOneTag(line, 'div', opt = '>')
    if verbose: print(f'after:{len(line)=}')
    stripped_lines.append(line)

# WRITE
with open(fname,'w') as f:
    for line in stripped_lines:
        f.write(line)
