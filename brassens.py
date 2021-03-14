# script pour inclure les accords dans la ligne

# READ
lines = []
with open('README.md','r') as f:
    for line in f:
        lines.append(line)

# WRITE
def write(lines, fname='index.md'):
    with open(fname,'w') as f:
        for line in lines:
            f.write(line)

# print(len(lines))
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

import os
os.makedirs('albums', exist_ok=True)

album_count = 0 # Album counter

lines_index = ["""

# Anthologie Georges Brassens

"""]
lines_tmp = []
for i, line in enumerate(lines):
    if line[0]=='#' : # a header
        if line[:2]=='# ' : # un nouvel album
            if len(lines_tmp) > 0 :
                # on sauve l'album précédemment écrit
                album_name = f'albums/brassens_{album_count}.md' # albums/brassens_1.md
                album_name_html = f'albums/brassens_{album_count}.html' # albums/brassens_1.html
                write(lines_tmp, fname=album_name)
                lines_index.append(f' * [{album_title}]({album_name_html}) \n')

            album_title = line[2:-1]
            # on recommence à collecter un nouvel album
            lines_tmp = []
            album_count += 1
        line_tmp = line
    elif line=='\n':
        line_tmp = line #+ '\n'
    else:
        words = line[:-1].split(' ')
        threshold = sum([word=='' for word in words])
        if not threshold>1:
            if ' *' in line or '---' in line or 'youTubeId' in line :
                line_tmp = line + '\n'
            else:
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

write(lines_index, fname='index.md')
