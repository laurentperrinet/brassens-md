"""Merge each `c1:` chord line and its following lyric line into one ChordPro-like line.

    c1: Am           E    Am
    l1: Au village, sans prétention, ...      ->   [Am]Au village, [E]sans [Am]prétention, ...

Each chord is inserted into the lyrics at the column where it was written above them
(possibly in the middle of a word, to keep the syllable it falls on). Chords written
beyond the end of the lyrics (instrumental endings) are appended after the text.
A chord line with no lyrics becomes a line of chords only: `[Am] [E] [Am]`.
Lyric lines without chords (`l1:`) lose their prefix too.

Usage:
    python3 tools/inline_chords.py [file ...]    # default: every file under songs/
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREFIX_LEN = len('c1: ')  # `c1: ` and `l1: ` have the same width, so columns stay aligned
STRUCTURAL = ('c1:', 'l1:', '#', '---', 'youTubeId', ' *')


def merge(chords, lyrics):
    """Insert the chords of a chord line into a lyric line.

    Args:
        chords: chord line without its `c1: ` prefix; chords separated by spaces (str).
        lyrics: lyric line without its prefix, or '' if there is none (str).

    Returns:
        The merged line, without trailing whitespace (str).
    """
    lyrics = lyrics.rstrip()
    inside, tail = [], []
    for m in re.finditer(r'\S+', chords):
        (inside if m.start() < len(lyrics) else tail).append((m.start(), m.group()))
    out = lyrics
    for col, chord in reversed(inside):  # right to left, so earlier columns stay valid
        out = out[:col] + f'[{chord}]' + out[col:]
    if tail:
        out = (out + ' ' if out else '') + ' '.join(f'[{c}]' for _, c in tail)
    return out


def convert(text):
    """Convert the `c1:`/`l1:` lines of one song file.

    Args:
        text: content of a song file (str).

    Returns:
        The converted content (str).
    """
    lines = text.split('\n')
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('c1:'):
            nxt = lines[i + 1] if i + 1 < len(lines) else ''
            if nxt.startswith('l1:'):
                lyrics, step = nxt[PREFIX_LEN:], 2
            elif nxt.strip() and not nxt.startswith(STRUCTURAL):  # lyric line missing its `l1:`
                lyrics, step = nxt, 2
            else:
                lyrics, step = '', 1
            out.append(merge(line[PREFIX_LEN:], lyrics))
            i += step
        elif line.startswith('l1:'):
            out.append(line[PREFIX_LEN:].rstrip())
            i += 1
        else:
            out.append(line)
            i += 1
    return '\n'.join(out)


if __name__ == '__main__':
    files = [Path(a) for a in sys.argv[1:]] or sorted(ROOT.glob('songs/*/[0-9]*.md'))
    for f in files:
        f.write_text(convert(f.read_text(encoding='utf-8')), encoding='utf-8')
    print(f'{len(files)} files converted', file=sys.stderr)
