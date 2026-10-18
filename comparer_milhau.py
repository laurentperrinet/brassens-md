"""Compare the chords of the Milhau PDF (2017-11-29) with the songs of `chansons/`.

The PDF is a Word export whose plain-text pages hold chord lines aligned (with spaces)
over the lyric lines. `gs` (Ghostscript, `brew install ghostscript`) extracts that text
with its columns preserved. For every song, the script lists the chord *names* used in
the PDF and in the repository, and reports the differences, after a few spelling
equivalences (`D#°` = `D#dim`, `C7M` = `Cmaj7`) and after testing whether the PDF is
simply transposed.

Usage:
    python3 comparer_milhau.py                 # writes comparaison-milhau-2017.md
    python3 comparer_milhau.py --lignes        # also writes the chord/lyric pairs (positions)
    python3 comparer_milhau.py --appliquer     # also fix triads that the PDF (transposed) gives as sevenths

The PDF is not versioned (no licence): it must sit at the root of the repository.
"""
import argparse
import difflib
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent
PDF = RACINE / 'Brassens, une page, une chanson.pdf'
SORTIE = RACINE / 'comparaison-milhau-2017.md'

NOTE = r'[A-Ga-g][#b]?'
SUFFIXE = r'(?:maj|add|sus|dim|aug|m|M|\d|\+|°|-)*'
# `Am`, `A5+`, `D#°`, `E95+`, `Am/c`, `/b`, `G/g`, `(e`, `g#)`
ACCORD_PDF = re.compile(rf'^\(?(?:{NOTE}{SUFFIXE}(?:/{NOTE})?|/{NOTE})\)?$')
PREFIXE = re.compile(r'^(?:intro|solo guitare|solo)\s*:?\s*', re.I)
ACCORD_DEPOT = re.compile(r'\[([^\]]+)\]')
SEMITONS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
ALIAS = {'gastibelza': 'gastibelza l homme a la carabine', 'le 22 septembre': 'le vingt deux septembre',
         'putain de toi': 'p de toi'}  # PDF title -> repository title (normalised)
NOMS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


def sans_accent(texte):
    """Return `texte` lower-cased, without accents, with straight quotes and single spaces."""
    texte = unicodedata.normalize('NFD', texte.replace('’', "'").replace('œ', 'oe'))
    texte = ''.join(c for c in texte if unicodedata.category(c) != 'Mn').lower()
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', texte).split())


def normaliser(accord):
    """Return a chord name in the spelling of the repository (`D#°` -> `D#dim`).

    Args:
        accord: a chord token as written in the PDF or in a song.
    """
    accord = accord.strip('()')
    accord = accord.replace('°', 'dim').replace('7M', 'maj7').replace('M7', 'maj7')
    return accord


ANALYSE = re.compile(r'^([A-G])([#b]?)(.*?)(?:/([A-Ga-g])([#b]?))?$')


def hauteur(lettre, alteration):
    """Return the pitch class (0-11) of a note name."""
    return (SEMITONS[lettre.upper()] + {'#': 1, 'b': -1, '': 0}[alteration]) % 12


def canonique(accord):
    """Return `(root pitch class, quality, bass pitch class or None)` of an uppercase chord.

    Comparing pitch classes makes `D#dim` and `Ebdim`, or `G#7` and `Ab7`, equal.
    """
    m = ANALYSE.match(accord)
    basse = hauteur(m.group(4), m.group(5)) if m.group(4) else None
    return hauteur(m.group(1), m.group(2)), m.group(3), basse


def nommer(canon, decalage=0):
    """Return the name of a canonical chord shifted by `decalage` semitones."""
    racine, qualite, basse = canon
    nom = NOMS[(racine + decalage) % 12] + qualite
    return nom + (f'/{NOMS[(basse + decalage) % 12]}' if basse is not None else '')


def meilleur_decalage(pdf, depot):
    """Return the shift (0-11 semitones, PDF -> repository) that makes the chord sets closest."""
    cible = {canonique(a) for a in depot}
    def score(k):
        decale = {((r + k) % 12, q, None if b is None else (b + k) % 12) for r, q, b in map(canonique, pdf)}
        return len(cible & decale) - 0.001 * k
    return max(range(12), key=score)


def extraire_pages(destination):
    """Extract the text of every page of the PDF, columns preserved, into `destination`.

    Returns:
        the list of page texts (list of str), in page order.
    """
    subprocess.run(['gs', '-q', '-dNOPAUSE', '-dBATCH', '-sDEVICE=txtwrite',
                    f'-sOutputFile={destination}/p%03d.txt', str(PDF)], check=True)
    return [p.read_text(encoding='utf-8', errors='replace') for p in sorted(Path(destination).glob('p*.txt'))]


def titres_index(pages):
    """Return the titles of the table of contents (pages 3 to 6 of the PDF)."""
    titres = []
    for page in pages[2:6]:
        for ligne in page.split('\n'):
            m = re.match(r'^\s*(.+?)\.{3,}\s*\d+\s*$', ligne)
            if m:
                titres.append(m.group(1).strip())
    return titres


def decouper_chansons(pages):
    """Split the PDF into songs: `{title: [lines]}`, a page without title continuing the previous song."""
    index = {sans_accent(t): t for t in titres_index(pages)}
    chansons, courant = {}, None
    for page in pages[6:]:
        lignes = [l for l in page.split('\n') if l.strip()]
        if not lignes:
            continue
        premiere = sans_accent(lignes[0])
        cible = index.get(premiere) or next(
            (index[k] for k in difflib.get_close_matches(premiere, index, n=1, cutoff=0.85)), None)
        if cible:
            courant = cible
            chansons.setdefault(courant, [])
            lignes = lignes[1:]
        if courant:
            chansons[courant] += [l for l in lignes if not re.match(r'^\s*\d+\s*$', l)]
    return chansons


def segments_accords(ligne):
    """Return the chord tokens of a PDF line, or [] if it holds none.

    Two-column pages put a chord line and the lyrics of the other column on one text line, so
    the line is cut at runs of 3+ spaces and only the segments made of chords only are kept.
    """
    jetons = []
    for segment in re.split(r'\s{3,}', PREFIXE.sub('', ligne.strip())):
        mots = segment.split()
        if not mots or not all(ACCORD_PDF.match(m) for m in mots):
            continue
        if len(mots) == 1 and mots[0] == 'a':  # the verb `a`, not the note
            continue
        jetons += mots
    return jetons


def accords_pdf(lignes):
    """Return (chords, lowercase notes and bare bass notes, [(chord line, lyric line)]) of a PDF song."""
    accords, notes, paires = [], [], []
    for i, ligne in enumerate(lignes):
        jetons = segments_accords(ligne)
        if not jetons:
            continue
        for j in jetons:
            n = normaliser(j)
            liste = accords if n[0].isupper() else notes
            if n not in liste:
                liste.append(n)
        if i + 1 < len(lignes):
            paires.append((ligne.rstrip(), lignes[i + 1].rstrip()))
    return accords, notes, paires


def accords_depot(texte):
    """Return the ordered distinct chords of a song source (inline markers and grid)."""
    accords = []
    corps = texte.split('### Notes')[0]
    for jeton in ACCORD_DEPOT.findall(corps):
        if jeton[0].islower():  # a lone note (`a`, `f#`), not a chord
            continue
        n = normaliser(jeton)
        if n not in accords:
            accords.append(n)
    for ligne in corps.split('\n'):
        if ligne.lstrip().startswith('|') and '[' not in ligne:
            for mot in re.split(r'[\s|:~]+', ligne):
                if mot and mot not in '.%' and ACCORD_PDF.match(mot):
                    n = normaliser(mot)
                    if n not in accords:
                        accords.append(n)
    return accords


def chansons_depot():
    """Return `{title: (path, text)}` for the songs of `chansons/`."""
    resultat = {}
    for chemin in sorted((RACINE / 'chansons').glob('*/[0-9]*.md')):
        texte = chemin.read_text(encoding='utf-8')
        m = re.search(r'^## (.+)$', texte, re.M)
        if m:
            resultat[m.group(1).strip()] = (chemin, texte)
    return resultat


def ameliorations(a_pdf, a_depot, decalage):
    """Return `{chord: chord + '7'}` for triads of the repository that the PDF, once transposed
    into the key of the repository, only gives as dominant sevenths (and the repository never does).

    The correction is only proposed when the shift is trustworthy: at least half of the chords of
    the repository must be found in the transposed PDF.
    """
    pdf = {((r + decalage) % 12, q, None if b is None else (b + decalage) % 12)
           for r, q, b in map(canonique, a_pdf)}
    depot = {canonique(a) for a in a_depot}
    if len(depot & pdf) < 0.5 * len(depot):
        return {}
    remplace = {}
    for accord in a_depot:
        racine, qualite, basse = canonique(accord)
        if qualite == '' and basse is None and (racine, '7', None) in pdf \
                and (racine, '', None) not in pdf and (racine, '7', None) not in depot:
            remplace[accord] = accord + '7'
    return remplace


def appliquer(texte, remplace):
    """Return `texte` with `[X]` replaced by `[X7]` in the lyrics (not in the notes nor in tablatures)."""
    sortie, en_bloc, fini = [], False, False
    for ligne in texte.split('\n'):
        if ligne.strip() == '### Notes':
            fini = True
        if ligne.strip() == '```':
            en_bloc = not en_bloc
        if not fini and not en_bloc:
            ligne = ACCORD_DEPOT.sub(lambda m: f'[{remplace.get(m.group(1), m.group(1))}]', ligne)
        sortie.append(ligne)
    return '\n'.join(sortie)


def comparer(avec_lignes, avec_appliquer=False):
    """Write the comparison report."""
    with tempfile.TemporaryDirectory() as tmp:
        pages = extraire_pages(tmp)
    pdf = decouper_chansons(pages)
    depot = chansons_depot()
    cles_depot = {sans_accent(t): t for t in depot}

    sortie = ['# Chord comparison: Milhau PDF (2017-11-29) vs `chansons/`', '',
              'Generated by `comparer_milhau.py`. Chord *names* only (positions are not compared).',
              '`Only PDF` = chords in the PDF and not in the repository; `Only repo` = the reverse.',
              '`Remark` lists the lowercase notes / bare bass notes of the PDF (not compared).', '',
              '| Song | Only PDF | Only repo | Remark |', '|------|----------|-----------|--------|']
    absentes, identiques, differentes, paires_par_titre, corriges = [], 0, 0, {}, []
    for titre, lignes in pdf.items():
        cle = ALIAS.get(sans_accent(titre), sans_accent(titre))
        cible = cles_depot.get(cle) or next(
            (cles_depot[k] for k in difflib.get_close_matches(cle, cles_depot, n=1, cutoff=0.8)), None)
        a_pdf, notes, paires = accords_pdf(lignes)
        paires_par_titre[titre] = paires
        if not cible:
            absentes.append((titre, a_pdf, notes))
            continue
        a_depot = accords_depot(depot[cible][1])
        decalage = meilleur_decalage(a_pdf, a_depot)
        canon_depot = {canonique(a) for a in a_depot}
        decale = [((r + decalage) % 12, q, None if b is None else (b + decalage) % 12)
                  for r, q, b in map(canonique, a_pdf)]
        if avec_appliquer:
            remplace = ameliorations(a_pdf, a_depot, decalage)
            if remplace:
                chemin = depot[cible][0]
                chemin.write_text(appliquer(depot[cible][1], remplace), encoding='utf-8')
                corriges.append((cible, remplace))
                a_depot = accords_depot(chemin.read_text(encoding='utf-8'))
                canon_depot = {canonique(a) for a in a_depot}
        seuls_pdf = [nommer(c) for c in decale if c not in canon_depot]
        seuls_depot = [a for a in a_depot if canonique(a) not in set(decale)]
        remarque = f'PDF {nommer(canonique(a_pdf[0]))}... = repo {nommer(canonique(a_pdf[0]), decalage)} (shift {decalage:+d})' if decalage and a_pdf else ''
        if notes:
            remarque += (' ; ' if remarque else '') + 'notes: ' + ' '.join(notes)
        if not seuls_pdf and not seuls_depot:
            identiques += 1
            continue
        differentes += 1
        sortie.append(f'| {cible} | {" ".join(seuls_pdf)} | {" ".join(seuls_depot)} | {remarque} |')
    sortie += ['', f'Same chord names: {identiques} songs. Different: {differentes} songs.', '',
               '## Songs of the PDF absent from the repository', '']
    for titre, a_pdf, notes in absentes:
        sortie.append(f'* {titre}: {" ".join(a_pdf)}' + (f' (notes: {" ".join(notes)})' if notes else ''))
    sortie += ['', '## Songs of the repository absent from the PDF', '']
    vus = {sans_accent(t) for t in pdf}
    for titre in depot:
        if sans_accent(titre) not in vus and not difflib.get_close_matches(sans_accent(titre), vus, n=1, cutoff=0.8):
            sortie.append(f'* {titre}')
    if corriges:
        sortie += ['', '## Triads changed to sevenths (`--appliquer`)', '']
        sortie += [f'* {t}: ' + ', '.join(f'{a} -> {b}' for a, b in r.items()) for t, r in corriges]
    if avec_lignes:
        sortie += ['', '## Chord lines of the PDF with their lyric line', '']
        for titre, paires in paires_par_titre.items():
            sortie += [f'### {titre}', '', '```']
            for accords, paroles in paires:
                sortie += [accords, paroles]
            sortie += ['```', '']
    SORTIE.write_text('\n'.join(sortie) + '\n', encoding='utf-8')
    print(f'{SORTIE.name}: {identiques} identical, {differentes} different, {len(absentes)} absent from the repository')


if __name__ == '__main__':
    analyseur = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    analyseur.add_argument('--lignes', action='store_true', help='also write the chord/lyric line pairs')
    analyseur.add_argument('--appliquer', action='store_true', help='fix triads that the PDF gives as sevenths')
    arguments = analyseur.parse_args()
    comparer(arguments.lignes, arguments.appliquer)
