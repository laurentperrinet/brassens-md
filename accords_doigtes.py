"""Add an `Accords :` block (chord fingerings) to every song of `chansons/`.

Each song gets, right under its title (after any ` * capo 1` or front matter), the list of the
distinct chords it uses, in order of first appearance, with a fingering written from the 6th
(low E) to the 1st string, `x` meaning a muted string:

    Accords :

     * Dm : xx0231
     * Bb7 : x13131

Fingerings are *computed*, not typed: `doigte` searches the neck for the easiest shape whose
lowest note is the root (or the bass of a slash chord) and whose notes are all chord tones, so
every fingering can be checked by ear or with `notes_du_doigte`. Songs that already have an
`Accords :` block (such as La marine, written by hand) are left alone.

Usage:
    python3 accords_doigtes.py              # write the blocks
    python3 accords_doigtes.py --a-blanc    # only report, write nothing
    python3 accords_doigtes.py --rafraichir # also rewrite generated blocks that no longer match the chords
"""
import argparse
import itertools
import re
from functools import lru_cache
from pathlib import Path

RACINE = Path(__file__).resolve().parent
CORDES = [4, 9, 2, 7, 11, 4]  # pitch classes of the open strings, 6th to 1st (E A D G B E)
HAUTEURS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

# quality -> (intervals above the root, intervals that must be present)
QUALITES = {
    '': ({0, 4, 7}, {0, 4}), 'm': ({0, 3, 7}, {0, 3}), '7': ({0, 4, 7, 10}, {0, 4, 10}),
    'm7': ({0, 3, 7, 10}, {0, 3, 10}), 'maj7': ({0, 4, 7, 11}, {0, 4, 11}),
    '6': ({0, 4, 7, 9}, {0, 4, 9}), 'm6': ({0, 3, 7, 9}, {0, 3, 9}),
    'dim': ({0, 3, 6, 9}, {0, 3, 6}), '7dim': ({0, 3, 6, 9}, {0, 3, 6}),
    '5+': ({0, 4, 8}, {0, 4, 8}), '+': ({0, 4, 8}, {0, 4, 8}), 'm5+': ({0, 3, 8}, {0, 3, 8}),
    '9': ({0, 4, 7, 10, 2}, {0, 4, 10, 2}), '5': ({0, 7}, {0, 7}),
    '7M': ({0, 4, 7, 11}, {0, 4, 11}), 'm+': ({0, 3, 8}, {0, 3, 8}),
    '7/5+': ({0, 4, 8, 10}, {0, 4, 8, 10}), '95+': ({0, 4, 8, 10, 2}, {0, 4, 8, 10}),
}
ANALYSE = re.compile(r'^([A-G])([#b]?)(.*?)(?:/([A-Ga-g])([#b]?))?$')
ACCORD = re.compile(r'\[([^\]]+)\]')
FICHE = re.compile(r'^ \* [^\s:]+\s*:\s*[x\d()-]+\s*$')


def hauteur(lettre, alteration):
    """Return the pitch class (0-11) of a note name (`F`, `#`)."""
    return (HAUTEURS[lettre] + {'#': 1, 'b': -1, '': 0}[alteration]) % 12


def analyser(accord):
    """Return `(root, quality, bass or None)` as pitch classes, or None if not supported.

    Args:
        accord: chord name as written in the songs (`Am`, `D#dim`, `A5+`, `Em/C`).
    """
    m = ANALYSE.match(accord)
    if not m or m.group(3) not in QUALITES:
        return None
    basse = hauteur(m.group(4).upper(), m.group(5)) if m.group(4) else None
    return hauteur(m.group(1), m.group(2)), m.group(3), basse


def frettes_de(doigte):
    """Return the frets of a fingering string (`x32010` or `x-10-12-12-11-10`), None = muted."""
    jetons = doigte.split('-') if '-' in doigte else list(doigte)
    return [None if j == 'x' else int(j) for j in jetons]


def notes_du_doigte(doigte):
    """Return the sounded pitch classes of a fingering string (`x32010` -> [0, 4, 7, 0, 4])."""
    return [(CORDES[i] + f) % 12 for i, f in enumerate(frettes_de(doigte)) if f is not None]


def doigts_necessaires(frettes):
    """Return the number of fingers needed, or None if the shape is physically impossible.

    The lowest pressed fret may be a barre (one finger over several strings), but not above an
    open string. Other frets need one finger per run of adjacent strings.
    """
    appuyees = {i: f for i, f in enumerate(frettes) if f}
    if not appuyees:
        return 0
    bas = min(appuyees.values())
    cordes_bas = [i for i, f in appuyees.items() if f == bas]
    doigts = 1
    if len(cordes_bas) >= 2 and any(frettes[i] == 0 for i in range(cordes_bas[0], cordes_bas[-1] + 1)):
        return None
    for fret in set(appuyees.values()) - {bas}:
        cordes = [i for i, f in appuyees.items() if f == fret]
        doigts += 1 + sum(1 for a, b in zip(cordes, cordes[1:]) if b != a + 1)
    return doigts


@lru_cache(maxsize=None)
def chercher(racine, qualite, basse):
    """Return the easiest fingering of a chord as a list of frets (None = muted), or None.

    Easiest = highest fret within the first 4 frets (more is penalised), then most sounded strings,
    then lowest highest-fret, then fewest fingers.
    """
    autorises, requis = QUALITES[qualite]
    basse = racine if basse is None else basse
    autorises = {(racine + i) % 12 for i in autorises} | {basse}
    requis = {(racine + i) % 12 for i in requis}
    meilleur, cote_min = None, None
    for base in range(0, 10):
        choix = [[None, 0] + list(range(max(base, 1), base + 4)) for _ in CORDES]
        for frettes in itertools.product(*choix):
            sonnantes = [i for i, f in enumerate(frettes) if f is not None]
            if len(sonnantes) < 4 or sonnantes[-1] - sonnantes[0] + 1 != len(sonnantes):
                continue  # at least 4 strings, no muted string inside the chord
            notes = [(CORDES[i] + frettes[i]) % 12 for i in sonnantes]
            if notes[0] != basse or not set(notes) <= autorises or not requis <= set(notes):
                continue
            doigts = doigts_necessaires(frettes)
            if doigts is None or doigts > 4:
                continue
            appuyees = [f for f in frettes if f]
            cote = (max(0, max(appuyees, default=0) - 4), -len(sonnantes), max(appuyees, default=0), doigts, sum(appuyees))
            if cote_min is None or cote < cote_min:
                meilleur, cote_min = frettes, cote
        if meilleur is not None and cote_min[0] == 0 and base >= 1:
            break
    return meilleur


def doigte(accord):
    """Return the fingering string of a chord (`Dm` -> `xx0231`), or None if there is none."""
    analyse = analyser(accord)
    frettes = chercher(*analyse) if analyse else None
    if frettes is None:
        return None
    if max(f for f in frettes if f is not None) >= 10:
        return '-'.join('x' if f is None else str(f) for f in frettes)
    return ''.join('x' if f is None else str(f) for f in frettes)


def accords_de(texte):
    """Return the distinct chords of a song source, in order of first appearance."""
    accords, en_bloc = [], False
    for ligne in texte.split('\n'):
        if ligne.strip() == '### Notes':
            break
        if ligne.strip() == '```':
            en_bloc = not en_bloc
            continue
        if en_bloc:
            continue
        for jeton in ACCORD.findall(ligne):
            if jeton[0].isupper() and jeton not in accords:
                accords.append(jeton)
        if ligne.lstrip().startswith('|'):
            for mot in re.split(r'[\s|:~]+', ligne):
                if re.match(r'^[A-G][#b]?[\w+/#°]*$', mot) and mot not in accords:
                    accords.append(mot)
    return accords


def position_insertion(lignes):
    """Return the index where the `Accords :` block goes: after the title, front matter and bullets."""
    i = 1
    while i < len(lignes):
        ligne = lignes[i]
        if not ligne.strip() or ligne.startswith(' * '):
            i += 1
        elif ligne == '---' and i + 2 < len(lignes) and lignes[i + 2] == '---':
            i += 3
        else:
            break
    return i


BLOC = re.compile(r'(Accords :\n\n(?: \* [^\n]+ : [x\d()-]+\n)+)\n*')


def ajouter(chemin, a_blanc, rafraichir=False):
    """Insert the `Accords :` block in a song file. Returns the chords without fingering (list)."""
    texte = chemin.read_text(encoding='utf-8')
    lignes = texte.split('\n')
    if any(l.strip().rstrip(':').strip() == 'Accords' for l in lignes):
        if rafraichir and not a_blanc:
            bloc = BLOC.search(texte)
            suite = texte[bloc.end():].split('\n', 1)[0]
            if bloc and not suite.startswith(' * ') and all(re.fullmatch(r' \* \S+ : [x\d()-]+', l) for l in bloc.group(1).split('\n')[2:-1]):
                # only a block in the generated format (a hand-written one, like La marine's, is kept)
                fiches = [f' * {a} : {doigte(a)}' for a in accords_de(texte) if doigte(a)]
                neuf = 'Accords :\n\n' + '\n'.join(fiches) + '\n'
                if neuf != bloc.group(1):
                    chemin.write_text(texte[:bloc.start()] + neuf + '\n' + texte[bloc.end():], encoding='utf-8')
        return None
    fiches, sans = [], []
    for accord in accords_de(texte):
        d = doigte(accord)
        (fiches if d else sans).append(f' * {accord} : {d}' if d else accord)
    if fiches and not a_blanc:
        i = position_insertion(lignes)
        while i > 1 and not lignes[i - 1].strip():
            i -= 1  # right after the last non-blank line
        bloc = ['', 'Accords :', ''] + fiches + ['']
        lignes[i:i] = bloc
        texte = '\n'.join(lignes)
        # a single blank line between the block and what follows
        texte = re.sub(r'(Accords :\n\n(?: \* [^\n]+ : [x\d()-]+\n)+)\n*', lambda m: m.group(1) + '\n', texte, count=1)
        chemin.write_text(texte, encoding='utf-8')
    return sans


if __name__ == '__main__':
    analyseur = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    analyseur.add_argument('--a-blanc', action='store_true', help='report only, write nothing')
    analyseur.add_argument('--rafraichir', action='store_true', help='rewrite stale generated blocks')
    arguments = analyseur.parse_args()
    sans_doigte = {}
    for chemin in sorted((RACINE / 'chansons').glob('*/[0-9]*.md')):
        manquants = ajouter(chemin, arguments.a_blanc, arguments.rafraichir)
        if manquants:
            sans_doigte[chemin.name] = manquants
    for nom, accords in sans_doigte.items():
        print(f'{nom}: no fingering for {" ".join(accords)}')
