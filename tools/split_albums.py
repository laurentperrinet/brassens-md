"""One-off migration: split `albums/brassens_N.md` into one Markdown file per song.

Layout produced (the files under `songs/` are the hand-edited sources):

    songs/{album nn}/_album.md        album header (`# 1) TITLE`) and any preamble
    songs/{album nn}/{song nn}_{slug}.md   one song, starting at its `## TITLE` line

Text is split on lines starting with `## ` and kept byte-for-byte, so that
concatenation (see `build.py`) reproduces the original album exactly.
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def slugify(title):
    """Return an ASCII, lowercase, hyphenated version of `title`.

    Args:
        title: song title, possibly accented (str).
    """
    ascii_ = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', ascii_.lower()).strip('-')


def split_album(src, dst_root):
    """Split one album file into `_album.md` and numbered song files.

    Args:
        src: path of the album Markdown file (Path).
        dst_root: directory receiving the `songs/` tree (Path).
    """
    lines = src.read_text(encoding='utf-8').splitlines(keepends=True)
    album_nn = int(re.search(r'brassens_(\d+)', src.name).group(1))
    out_dir = dst_root / f'{album_nn:02d}'
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks, current = [], []
    for line in lines:
        if line.startswith('## ') and current is not None:
            chunks.append(current)
            current = []
        current.append(line)
    chunks.append(current)

    preamble, songs = chunks[0], chunks[1:]
    (out_dir / '_album.md').write_text(''.join(preamble), encoding='utf-8')
    for i, chunk in enumerate(songs, start=1):
        title = chunk[0][3:].strip()
        name = f'{i:02d}_{slugify(title)}.md'
        (out_dir / name).write_text(''.join(chunk), encoding='utf-8')
    return len(songs)


if __name__ == '__main__':
    total = 0
    for src in sorted((ROOT / 'albums').glob('brassens_*.md')):
        total += split_album(src, ROOT / 'songs')
    print(f'{total} songs written to songs/', file=sys.stderr)
