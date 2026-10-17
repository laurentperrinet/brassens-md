"""Assemble the per-song sources in `chansons/` and render them to HTML in `docs/`.

Pipeline:
    chansons/{nn}_{album}/_album.md + chansons/{nn}_{album}/*.md  ->  construction/albums/brassens_{n}.md
    construction/albums/*.md                ->  construction/brassens.md  (anthology)
    construction/**/*.md  --rendre.py-->  docs/**/*.html  (chords in bold monospace)
    docs/index.html                         (list of the pages, written here)

`docs/` is not versioned: the GitHub Actions workflow `.github/workflows/pages.yml`
runs `assembler.py --rendre` on the server and publishes `docs/` with GitHub Pages.

Usage:
    python3 assembler.py              # assemble only
    python3 assembler.py --rendre     # assemble, then render the HTML pages in `docs/`
"""
import argparse
import re
import shutil
from pathlib import Path

import rendre

RACINE = Path(__file__).resolve().parent
CHANSONS = RACINE / 'chansons'
CONSTRUCTION = RACINE / 'construction'
DOCS = RACINE / 'docs'


def dossiers_albums():
    """Return the album directories of `chansons/` (`{nn}_{slug of the title}`).

    They are sorted by number (list of Path).
    """
    return sorted(p for p in CHANSONS.iterdir() if p.is_dir() and re.match(r'\d+_', p.name))


def assembler_album(dossier_album):
    """Concatenate an album header and its songs.

    Args:
        dossier_album: a `chansons/{nn}_{album}` directory (Path).

    Returns:
        (album number, album title, Markdown text).
    """
    entete = (dossier_album / '_album.md').read_text(encoding='utf-8')
    titre = re.search(r'^# (.+)$', entete, re.M).group(1)
    fichiers = sorted(p for p in dossier_album.glob('*.md') if not p.name.startswith('_'))
    texte = entete + ''.join(p.read_text(encoding='utf-8') for p in fichiers)
    return int(dossier_album.name.split('_')[0]), titre, texte


def assembler():
    """Write `construction/albums/*.md` and `construction/brassens.md`.

    Returns:
        (link text, URL relative to `docs/`) of every page of the site, for the index
        (list of (str, str)).
    """
    shutil.rmtree(CONSTRUCTION, ignore_errors=True)
    (CONSTRUCTION / 'albums').mkdir(parents=True)

    anthologie = ''
    entrees = [('Anthologie en un fichier', 'brassens.html')]
    for dossier_album in dossiers_albums():
        n, titre, texte = assembler_album(dossier_album)
        (CONSTRUCTION / 'albums' / f'brassens_{n}.md').write_text(texte, encoding='utf-8')
        anthologie += texte
        entrees.append((titre, f'albums/brassens_{n}.html'))
    (CONSTRUCTION / 'brassens.md').write_text(anthologie, encoding='utf-8')
    return entrees


def rendre_site(entrees):
    """Render the index and each assembled Markdown file to HTML in `docs/`.

    Args:
        entrees: pages to list in the index, as returned by `assembler()` (list of (str, str)).
    """
    (DOCS / 'albums').mkdir(parents=True, exist_ok=True)
    rendre.rendre_index(entrees, DOCS / 'index.html', titre='Anthologie Georges Brassens')
    rendre.rendre_fichier(CONSTRUCTION / 'brassens.md', DOCS / 'brassens.html',
                          titre='Anthologie Georges Brassens', accueil='index.html')
    for md in sorted((CONSTRUCTION / 'albums').glob('*.md')):
        titre = re.search(r'^# (.+)$', md.read_text(encoding='utf-8'), re.M).group(1)
        rendre.rendre_fichier(md, DOCS / 'albums' / md.with_suffix('.html').name,
                              titre=titre, accueil='../index.html')


if __name__ == '__main__':
    analyseur = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    analyseur.add_argument('--rendre', action='store_true',
                           help='also render the HTML pages in docs/')
    arguments = analyseur.parse_args()
    pages = assembler()
    if arguments.rendre:
        rendre_site(pages)
