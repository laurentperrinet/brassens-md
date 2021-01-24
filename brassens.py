# script pour inclure les accords dans la ligne

# READ
lines = []
with open('README.md','r') as f:
    for line in f:
        lines.append(line)


# WRITE
with open('tmp.md','w') as f:
    for line in lines:
        f.write(line)
