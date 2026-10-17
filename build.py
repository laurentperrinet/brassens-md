"""Assemble the per-song sources in `songs/` and render them to HTML in `docs/`.

Pipeline:
    songs/{nn}/_album.md + songs/{nn}/*.md  ->  build/albums/brassens_{n}.md
    build/albums/*.md                       ->  build/brassens.md  (anthology)
    build/**/*.md  --musicmd-->  docs/**/*.html  --tools/strip_tags.py-->  lighter HTML
    docs/index.md                           (table of contents, written here)

Usage:
    python3 build.py              # assemble only (no Node.js needed)
    python3 build.py --render     # assemble, then render HTML with `musicmd`
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SONGS = ROOT / 'songs'
BUILD = ROOT / 'build'
DOCS = ROOT / 'docs'


def album_dirs():
    """Return the album directories of `songs/`, sorted by number (list of Path)."""
    return sorted(p for p in SONGS.iterdir() if p.is_dir() and p.name.isdigit())


def assemble_album(album_dir):
    """Concatenate an album header and its songs.

    Args:
        album_dir: a `songs/{nn}` directory (Path).

    Returns:
        (album number, album title, Markdown text).
    """
    header = (album_dir / '_album.md').read_text(encoding='utf-8')
    title = re.search(r'^# (.+)$', header, re.M).group(1)
    songs = sorted(p for p in album_dir.glob('*.md') if not p.name.startswith('_'))
    text = header + ''.join(p.read_text(encoding='utf-8') for p in songs)
    return int(album_dir.name), title, text


def assemble():
    """Write `build/albums/*.md`, `build/brassens.md` and `docs/index.md`."""
    shutil.rmtree(BUILD, ignore_errors=True)
    (BUILD / 'albums').mkdir(parents=True)
    DOCS.mkdir(exist_ok=True)

    anthology = ''
    index = ['\n\n# Anthologie Georges Brassens\n\n',
             ' * [Anthologie en un fichier](brassens.html) \n\n']
    for album_dir in album_dirs():
        n, title, text = assemble_album(album_dir)
        (BUILD / 'albums' / f'brassens_{n}.md').write_text(text, encoding='utf-8')
        anthology += text
        index.append(f' * [{title}](albums/brassens_{n}.html) \n')
    # trailing marker kept from the original anthology
    (BUILD / 'brassens.md').write_text(anthology + '# fin\n', encoding='utf-8')
    (DOCS / 'index.md').write_text(''.join(index), encoding='utf-8')


def render():
    """Render each assembled Markdown file to HTML in `docs/` with `musicmd`."""
    if shutil.which('musicmd') is None:
        sys.exit('musicmd not found: run `npm i -g markdown-it-music`')
    (DOCS / 'albums').mkdir(parents=True, exist_ok=True)
    for md in [BUILD / 'brassens.md', *sorted((BUILD / 'albums').glob('*.md'))]:
        html = DOCS / md.relative_to(BUILD).with_suffix('.html')
        subprocess.run(['musicmd', str(md), '-o', str(html)], check=True)
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'strip_tags.py'), str(html)],
                       check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--render', action='store_true', help='also render HTML with musicmd')
    args = parser.parse_args()
    assemble()
    if args.render:
        render()
