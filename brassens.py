# script pour inclure les accords dans la ligne

# READ
lines = []
with open('README.md','r') as f:
    for line in f:
        lines.append(line)

# WRITE
def write(lines, fname='tmp.md'):
    with open(fname,'w') as f:
        for line in lines:
            f.write(line)

write(lines)

# Transformations
# # 1/ remove special character
# for i, line in enumerate(lines):
#     lines[i] = line.replace(u'\xa0', u' ')
#
# write(lines, 'README.md')

chords = []
lines_tmp = []
for i, line in enumerate(lines):
    words = line[:-1].split(' ')
    threshold = sum([word=='' for word in words])
    if threshold>1:
        for word in words:
            if (not word in chords) :
                if word!='':
                    chords.append(word)

print(f'{chords=}')

# lines_tmp = []
# for i, line in enumerate(lines):
#     words = line[:-1].split(' ')
#     threshold = sum([word=='' for word in words])
#     if not threshold>1:
#         line_tmp = f'{threshold:3d}' + '|' + line
#         lines_tmp.append(line_tmp)
#
# write(lines_tmp)

# render
# https://markdown-it-py.readthedocs.io/en/latest/using.html
from markdown_it import MarkdownIt
from markdown_it.extensions.front_matter import front_matter_plugin
from markdown_it.extensions.footnote import footnote_plugin

md = (
    MarkdownIt()
    .use(front_matter_plugin)
    .use(footnote_plugin)
    .enable('table')
)
text = ("""
---
a: 1
---

a | b
- | -
1 | 2

A footnote [^1]

[^1]: some details
""")

write(md.render(text), 'index.html')
