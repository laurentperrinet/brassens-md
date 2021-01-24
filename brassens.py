# script pour inclure les accords dans la ligne

# READ
lines = []
with open('README.md','r') as f:
    for line in f:
        lines.append(line)

# WRITE
def write(lines):
    with open('tmp.md','w') as f:
        for line in lines:
            f.write(line)

write(lines)

# Transformations
# 1/ remove special character
for i, line in enumerate(lines):
    lines[i] = line.replace(u'\xa0', u' ')

write(lines)

chords = []
lines_tmp = []
for i, line in enumerate(lines):
    words = line[:-1].split(' ')
    threshold = sum([word=='' for word in words])
    if threshold>1:
        line_tmp = f'{threshold:3d}' + '|' + line
        lines_tmp.append(line_tmp)

write(lines_tmp)
