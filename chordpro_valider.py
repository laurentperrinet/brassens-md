"""Check the songs of `chansons/` against the ChordPro 6 notation, and export them as strict `.pro`.

The songs are Markdown files whose lyric lines are ChordPro (`[Am]paroles`). This script reads
every song and reports what a ChordPro parser would reject or misread: a chord that is not a chord
name, an unbalanced bracket, a fence or a section left open, a malformed grid row, a fingering that
is not six strings long, a chord with no fingering (or the other way round), a bare `Refrain` with
no `Refrain :` before it...

It needs no dependency: the rules follow the ChordPro specification (https://www.chordpro.org),
summarised in the README. The regular expressions of `rendre.py` are reused, so the checker and
the renderer agree on what a keyword or a grid row is.

Usage:
    python3 chordpro_valider.py                # report on stdout and in validation-chordpro.md
    python3 chordpro_valider.py --pro DIR      # also write one strict .pro file per song into DIR
"""
import argparse
import re
import sys
from pathlib import Path

from diagrammes_accords import FICHE
from rendre import BARRE, ENTETE, GRILLE, MOT_CLE, NOTES, SOURCE, YOUTUBE_IDENTIFIANT

RACINE = Path(__file__).resolve().parent
CHANSONS = RACINE / 'chansons'
RAPPORT = RACINE / 'validation-chordpro.md'

CROCHET = re.compile(r'\[([^\]]*)\]')
# A chord: root, quality, extensions and alterations, optional bass (`Em/C`, `D7/F#`); a single
# lowercase note (bass or melody: `a`, `f#`, `eb`) or a bass alone (`/b`) is accepted too.
ACCORD_VALIDE = re.compile(
    r'^(?:[A-G][#b]?(?:m(?!aj)|maj|M|dim|aug|sus|add|°|\+)?(?:\d+|[#b+°-]|M|dim|aug|sus|add|maj)*'
    r'(?:/(?:[A-Ga-g][#b]?|\d(?:\+|-)?))?'
    r'|[a-g][#b]?|/[A-Ga-g][#b]?)$')
SYMBOLES_GRILLE = {'.', '%'}  # besides chords: `.` extends the previous chord, `%` repeats the previous bar
SECTIONS_AVEC_DEFINITION = ('Refrain', 'Interlude')  # a bare keyword plays again what was defined before
CORDES = 6


def accord_valide(nom):
    """Return True when `nom` is a chord name accepted by the notation (bool).

    Args:
        nom: text between square brackets or a grid token, e.g. `Bb7`, `D7/F#` or `C~G` (str).
    """
    return all(ACCORD_VALIDE.match(partie) for partie in nom.split('~'))


def doigte_valide(doigte):
    """Return True when a fingering names exactly six strings (bool).

    Args:
        doigte: fingering from the 6th to the 1st string; `x` is muted, `(10)` a fret above 9 (str).
    """
    return len(re.findall(r'x|\d|\(\d+\)', doigte)) == CORDES


def verifier_ligne_grille(ligne, probleme):
    """Report the problems of one grid row.

    Args:
        ligne: the row, e.g. `|: Dm . | A7 :|` (str).
        probleme: callback taking the message of a problem.
    """
    barres = list(BARRE.finditer(ligne))
    if len(barres) < 2:
        probleme(f'ligne de grille avec moins de deux barres : « {ligne} »')
        return
    for gauche, droite in zip(barres, barres[1:]):
        mots = ligne[gauche.end():droite.start()].split()
        if not mots:
            probleme(f'mesure vide dans la grille : « {ligne} »')
        for mot in mots:
            if mot not in SYMBOLES_GRILLE and not accord_valide(mot):
                probleme(f'accord inconnu « {mot} » dans la grille : « {ligne} »')
    if mots_avant := ligne[:barres[0].start()].strip():
        probleme(f'texte avant la première barre de la grille : « {mots_avant} »')


def verifier(texte):
    """Return the problems found in one song.

    Args:
        texte: content of a song file (str).

    Returns:
        List of (line number, message) (list of tuples).
    """
    problemes = []
    lignes = texte.split('\n')
    definis = {}      # chord name -> number of fingerings written in `Accords :`
    utilises = {}     # chord name -> first line where it is played
    dans_bloc = False  # inside a ``` fence
    dans_notes = False
    definies = set()  # keywords already defined by `Refrain :`, `Interlude :`...
    titres = 0
    i = 0
    while i < len(lignes):
        ligne = lignes[i].rstrip()
        n = i + 1

        def probleme(message):
            problemes.append((n, message))

        if ligne.startswith('```'):
            dans_bloc = not dans_bloc
        elif dans_bloc:
            pass  # a tablature: spaces and bars are its own
        elif SOURCE.match(ligne):
            pass
        elif ligne == '---':
            # front matter: `---` / `key: value` / `---`, otherwise a stanza separator
            if i + 2 < len(lignes) and ENTETE.match(lignes[i + 1]) and lignes[i + 2].rstrip() == '---':
                cle, _, valeur = lignes[i + 1].partition(':')
                if cle == 'youTubeId' and not YOUTUBE_IDENTIFIANT.match(valeur.strip()):
                    probleme(f'youTubeId invalide « {valeur.strip()} » (11 caractères attendus)')
                elif cle != 'youTubeId':
                    probleme(f'clé d\'en-tête inconnue « {cle} »')
                i += 2
        elif ligne == NOTES:
            dans_notes = True
        elif dans_notes:
            pass  # free comments: chords are not interpreted there
        elif ligne.startswith('## '):
            titres += 1
            if titres > 1:
                probleme('plus d\'un titre « ## » dans le fichier')
        elif ligne.startswith('# '):
            probleme('titre d\'album « # » dans un fichier de chanson')
        elif FICHE.match(ligne):
            nom, doigte = FICHE.match(ligne).groups()
            definis[nom] = definis.get(nom, 0) + 1
            if not accord_valide(nom):
                probleme(f'accord inconnu « {nom} » dans Accords :')
            if not doigte_valide(doigte):
                probleme(f'doigté « {doigte} » de {nom} : {CORDES} cordes attendues')
        elif re.match(r'^ \* (?:Capo)\b', ligne):
            if not re.match(r'^ \* Capo [1-9]\d?\b', ligne):
                probleme(f'capo mal écrit : « {ligne.strip()} »')
        elif ligne.startswith(' * ') and ' : ' in ligne and re.match(r'^ \* [A-Ga-g]\S* : ', ligne):
            probleme(f'ligne d\'accord illisible (doigté attendu) : « {ligne.strip()} »')
        elif ligne:
            mot = MOT_CLE.match(ligne)
            if GRILLE.match(ligne):
                verifier_ligne_grille(ligne, probleme)
            elif mot and mot.group(1) == 'Grille':
                reste = mot.group(2).strip()
                if reste:
                    verifier_ligne_grille(reste, probleme)
            elif mot and mot.group(1) != 'Accords':
                if mot.group(2).strip() == '' and ligne.rstrip('*').rstrip().endswith(':') is False:
                    # a bare keyword: it plays again a section defined before
                    if mot.group(1) in SECTIONS_AVEC_DEFINITION and mot.group(1) not in definies:
                        probleme(f'« {mot.group(1)} » joué sans « {mot.group(1)} : » défini avant')
                else:
                    definies.add(mot.group(1))
            # brackets and chords of the line
            if ligne.count('[') != ligne.count(']'):
                probleme(f'crochets non équilibrés : « {ligne} »')
            for m in CROCHET.finditer(ligne):
                nom = m.group(1)
                if nom.startswith('*'):
                    continue  # annotation
                if not accord_valide(nom):
                    probleme(f'accord inconnu « [{nom}] »')
                else:
                    utilises.setdefault(nom, n)
            if not GRILLE.match(ligne) and re.search(r'\[\s*\]', ligne):
                probleme('crochets vides')
        i += 1
    if dans_bloc:
        problemes.append((len(lignes), 'bloc ``` jamais fermé'))
    if titres == 0:
        problemes.append((1, 'pas de titre « ## »'))
    for nom, n in sorted(utilises.items(), key=lambda t: t[1]):
        if definis and nom not in definis and re.match(r'^[A-G]', nom):
            problemes.append((n, f'accord « {nom} » joué mais absent de Accords :'))
    for nom in definis:
        if utilises and nom not in utilises:
            problemes.append((1, f'accord « {nom} » dans Accords : mais jamais joué'))
    return sorted(problemes)


def en_pro(texte):
    """Convert a song to a strict ChordPro file.

    Args:
        texte: content of a song file (str).

    Returns:
        The ChordPro text (str).
    """
    sortie = []
    section = None   # directive suffix of the section being written (`chorus`, `grid`, `tab`...)
    dans_notes = False
    lignes = texte.split('\n')
    i = 0

    def fermer():
        nonlocal section
        if section:
            sortie.append('{end_of_%s}' % section)
            section = None

    while i < len(lignes):
        ligne = lignes[i].rstrip()
        if SOURCE.match(ligne):
            pass
        elif ligne.startswith('```'):
            if section == 'tab':
                fermer()
            else:
                fermer()
                sortie.append('{start_of_tab}')
                section = 'tab'
        elif section == 'tab':
            sortie.append(ligne)
        elif ligne == '---' and i + 2 < len(lignes) and ENTETE.match(lignes[i + 1]) and lignes[i + 2].rstrip() == '---':
            cle, _, valeur = lignes[i + 1].partition(':')
            sortie.append('{meta: %s %s}' % (cle, valeur.strip()))
            i += 2
        elif ligne == NOTES:
            fermer()
            dans_notes = True
        elif dans_notes:
            if ligne.strip():
                sortie.append('{comment: %s}' % ligne.strip().lstrip('*-').strip())
        elif ligne.startswith('## '):
            fermer()
            sortie.append('{title: %s}' % ligne[3:])
        elif FICHE.match(ligne):
            nom, doigte = FICHE.match(ligne).groups()
            cases = re.findall(r'x|\d|\(\d+\)', doigte)
            frets = ' '.join('x' if c == 'x' else '0' if c == '0' else c.strip('()') for c in cases)
            sortie.append('{define: %s base-fret 1 frets %s}' % (nom, frets))
        elif re.match(r'^ \* Capo [1-9]', ligne):
            sortie.append('{capo: %s}' % re.match(r'^ \* Capo (\d+)', ligne).group(1))
        elif GRILLE.match(ligne):
            if section != 'grid':
                fermer()
                sortie.append('{start_of_grid}')
                section = 'grid'
            sortie.append(ligne)
        elif not ligne.strip():
            if section == 'grid' and sortie[-1] != '{start_of_grid}':
                fermer()  # a blank line ends a grid, unless it only follows the `Grille :` label
            elif section != 'grid':
                sortie.append('')
        else:
            mot = MOT_CLE.match(ligne)
            if mot and mot.group(1) == 'Grille':
                fermer()
                sortie.append('{start_of_grid}')
                section = 'grid'
                if mot.group(2).strip():
                    sortie.append(mot.group(2).strip())
            elif mot and mot.group(1) == 'Refrain' and not mot.group(2).strip():
                sortie.append('{chorus}')
            elif mot and mot.group(1) != 'Accords':
                fermer()
                suite = mot.group(2).strip()
                if mot.group(1) == 'Refrain':
                    sortie.append('{start_of_chorus}')
                    section = 'chorus'
                else:
                    sortie.append('{start_of_%s: %s}' % ('bridge' if mot.group(1) == 'Pont' else 'verse', mot.group(1)))
                    section = 'bridge' if mot.group(1) == 'Pont' else 'verse'
                if suite:
                    sortie.append(suite)
            elif not mot:
                sortie.append(ligne)  # a lyric line; the `Accords :` label has no ChordPro equivalent
        i += 1
    fermer()
    return '\n'.join(sortie) + '\n'


def chansons():
    """Return the song files of `chansons/` (sorted list of Path)."""
    return sorted(p for p in CHANSONS.glob('*/*.md') if not p.name.startswith('_'))


def main():
    """Check every song, print and write the report, optionally export `.pro` files.

    Returns:
        Exit status: 0 when no problem is found, 1 otherwise (int).
    """
    parseur = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parseur.add_argument('--pro', metavar='DIR', help='write one strict .pro file per song into DIR')
    args = parseur.parse_args()
    rapport, total = [], 0
    for fichier in chansons():
        texte = fichier.read_text(encoding='utf-8')
        problemes = verifier(texte)
        total += len(problemes)
        chemin = fichier.relative_to(RACINE).as_posix()
        rapport += [f'{chemin}:{n}: {message}' for n, message in problemes]
        if args.pro:
            destination = Path(args.pro) / fichier.parent.name / fichier.with_suffix('.pro').name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(en_pro(texte), encoding='utf-8')
    corps = '\n'.join(rapport) if rapport else 'Aucun problème.'
    RAPPORT.write_text(f'# Validation ChordPro\n\n{len(chansons())} chansons, {total} problèmes.\n\n'
                       f'```\n{corps}\n```\n', encoding='utf-8')
    print(corps)
    print(f'{len(chansons())} chansons, {total} problèmes (rapport : {RAPPORT.name})', file=sys.stderr)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
