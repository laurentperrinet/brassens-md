# script pour inclure les accords dans la ligne

# READ
lines = []
with open('README.md','r') as f:
    for line in f:
        lines.append(line)

# WRITE
def write(lines, fname='brassens_mm.md'):
    with open(fname,'w') as f:
        for line in lines:
            f.write(line)

print(len(lines))
# for testing
# write(lines)

# Transformations
# # 1/ remove special character
# for i, line in enumerate(lines):
#     lines[i] = line.replace(u'\xa0', u' ')
#
# write(lines, 'README.md')


accords = []
lines_tmp = []
for i, line in enumerate(lines):
    words = line[:-1].split(' ')
    threshold = sum([word=='' for word in words])
    if threshold>1:
        for word in words:
            if (not word in accords) :
                if word !='':
                    accords.append(word)

print(f'{accords=}')

# converting to english chords
notesdict = {'Do':'C',
        'Ré':'D',
        'Mi':'E',
        'Fa':'F',
        'Sol':'G',
        'La':'A',
        'Si':'B',
        }
# chords = []
chordsdict = {}
for accord in accords:
    chord = accord
    for note in notesdict.keys():
        if note in chord:
            chord = chord.replace(note, notesdict[note])
            extra_space = len(note) - len(notesdict[note])
            if extra_space>0:
                chord += ' '*extra_space
            # chords.append(chord)
            chordsdict[accord] = chord
# print(f'{chords=}')
print(f'{chordsdict=}')

lines_tmp = []
for i, line in enumerate(lines):
    if line[0]=='#' : # a header
        line_tmp = line
    elif line=='\n':
        line_tmp = line + '---\n'
    else:
        words = line[:-1].split(' ')
        threshold = sum([word=='' for word in words])
        if not threshold>1:
            # line_tmp = f'{threshold:3d}' + '|' + line
            line_tmp = 'l1: ' + line + '\n'
        else:
            words_tmp = []
            for word in words:
                for accord in chordsdict.keys():
                    if word == accord:
                        word = chordsdict[accord]
                    #    line = line.replace(accord, chordsdict[accord])
                words_tmp.append(word)
            line = ''
            for word in words_tmp: line += word + ' '
            line_tmp = 'c1: ' + line  + '\n'
            #print(line_tmp)
    lines_tmp.append(line_tmp)

if False:
    line = lines[4]
    print(line)
    words = line[:-1].split(' ')
    print(words)
    for c in chordsdict.keys():
        line = line.replace(c, chordsdict[c])
    print(line)

    print(len(lines_tmp))

write(lines_tmp)

if False:
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
    # text = ("""
    # ---
    # a: 1
    # ---
    #
    # a | b
    # - | -
    # 1 | 2
    #
    # A footnote [^1]
    #
    # [^1]: some details
    # """)
    #
    # write(md.render(text), 'index.html')

    text = ''
    for line in lines:
        text += line
    write(md.render(text), 'index.html')
