import sys

fname = sys.argv[1]
print(fname)


# READ
lines = []
with open(fname,'r') as f:
    for line in f:
        lines.append(line)

def removeOneTag(text, tag, div_class=None):
    if not div_class is None:
        opt = f' class="{div_class}"'
    else:
        opt = ''
    start = text.find("<"+tag + opt)
    end = text.find("</"+tag+">") + len(tag) + 3
    # print(start, end)
    return text[:start] + text[end:]

tags = ['svg', 'circle', 'line', 'text', 'button'] # 'div class="diagram"',
div_classes = ["diagram-container", "diagram-content-container", "content-scroll", "diagram"]
stripped_lines = []
for i_line, line in enumerate(lines):
    print('i_line=', i_line)
    print(f'before:{len(line)=}')
    for tag in tags:
        while("<"+tag in line):
            #print(line)
            line = removeOneTag(line, tag)
    for div_class in div_classes:
        while(f'<div class="{div_class}"' in line):
            #print(line)
            line = removeOneTag(line, 'div', div_class=div_class)
    print(f'after:{len(line)=}')
    stripped_lines.append(line)

# WRITE
with open(fname,'w') as f:
    for line in stripped_lines:
        f.write(line)
