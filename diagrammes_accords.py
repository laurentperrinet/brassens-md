"""Draw one SVG chord diagram per (chord name, fingering) found in the `Accords :` blocks of `chansons/`.

A song lists the chords it uses with their fingering, from the 6th (low E) to the 1st string,
`x` meaning a muted string and `0` an open one:

     * Dm : xx0231
     * Dm : x57765          <- another song, same name, other fingering

Only the fingerings written in the scores are drawn, so a chord that has variants gets one image
per variant, named `{chord}_{fingering}.svg` (`Dm_xx0231.svg`, `Dm_x57765.svg`). The images are
static files kept in `accords/`; `rendre.py` only references them.

Each diagram is a 6-string grid read as on a chord chart: muted (x) and open (o) marks above the
nut, a thick nut when the shape starts at the first fret, otherwise the number of its first fret
on the left, and a bar for a barre. Colours come from a `<style>` inside the SVG, which follows
the light or dark theme of the system even when the file is used as an `<img>`.

Usage:
    python3 diagrammes_accords.py             # write the missing or outdated images
    python3 diagrammes_accords.py --a-blanc   # only report, write nothing
"""
import argparse
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent
CHANSONS = RACINE / 'chansons'
ACCORDS = RACINE / 'accords'

# ` * Dm : x57765`: a chord and its fingering (the space before the colon is optional)
FICHE = re.compile(r'^ \* ([^\s:]+)\s*:\s*([x\d()-]+)\s*$')
DOIGTE = re.compile(r'^[x\d]{6}$')  # six strings, one character each (frets up to 9)

# geometry in SVG user units (the image is scaled by CSS, in em)
ECART_CORDES = 8.4    # distance between two strings
ECART_CASES = 11      # distance between two frets
GAUCHE = 13           # left margin: room for the number of the first fret
HAUT = 17             # top of the grid (below the muted/open marks)
LARGEUR = GAUCHE + 5 * ECART_CORDES + 8
CASES_MIN = 4         # a diagram always shows at least this many frets

STYLE = ('.t{stroke:#555;fill:none;stroke-width:.8}.n{stroke:#555;stroke-width:2.4}'
         '.p{fill:#5a3a00}.v{fill:none;stroke:#555;stroke-width:1}.m{stroke:#555;stroke-width:1.2}'
         '.l{fill:#555;font:700 7.5px ui-sans-serif,system-ui,sans-serif}'
         '@media (prefers-color-scheme:dark){.t{stroke:#bbb}.n{stroke:#bbb}.p{fill:#ffd966}'
         '.v{stroke:#bbb}.m{stroke:#bbb}.l{fill:#bbb}}')


def nom_fichier(nom, doigte):
    """Return the file name of a diagram.

    `#` and `/` are not safe in a URL path, hence `F#m` -> `Fdiesm`, `Em/C` -> `Em_sur_C`.

    Args:
        nom: chord name as written in the songs (`Dm`, `F#m`, `Em/C`).
        doigte: fingering, six characters from the 6th to the 1st string (`x57765`).

    Returns:
        File name with its extension (str).
    """
    return f"{nom.replace('#', 'dies').replace('/', '_sur_')}_{doigte}.svg"


def dessiner(doigte):
    """Return the SVG of a fingering.

    Args:
        doigte: six characters, from the 6th to the 1st string: `x` muted, `0` open,
            `1`-`9` the fret to press (str).

    Returns:
        The SVG document (str), or None when the fingering is not six characters of `x` and digits.
    """
    if not DOIGTE.match(doigte):
        return None
    frettes = [None if c == 'x' else int(c) for c in doigte]
    appuyees = [f for f in frettes if f]
    premiere = 1 if not appuyees or max(appuyees) <= CASES_MIN + 1 else min(appuyees)
    cases = max(CASES_MIN, (max(appuyees) - premiere + 1) if appuyees else CASES_MIN)
    bas = HAUT + cases * ECART_CASES

    def x(corde):
        return GAUCHE + corde * ECART_CORDES

    def y(fret):  # centre of the row of a fret
        return HAUT + (fret - premiere + 0.5) * ECART_CASES

    elements = []
    for k in range(cases + 1):  # frets
        classe = 'n' if (k == 0 and premiere == 1) else 't'
        elements.append(f'<line class="{classe}" x1="{x(0)}" y1="{HAUT + k * ECART_CASES}" '
                        f'x2="{x(5)}" y2="{HAUT + k * ECART_CASES}"/>')
    for corde in range(6):
        elements.append(f'<line class="t" x1="{x(corde):.1f}" y1="{HAUT}" x2="{x(corde):.1f}" y2="{bas}"/>')
    if premiere > 1:
        elements.append(f'<text class="l" x="{GAUCHE - 4}" y="{y(premiere) + 2.6:.1f}" text-anchor="end">{premiere}</text>')

    for corde, fret in enumerate(frettes):  # marks above the nut
        if fret is None:
            elements.append(f'<path class="m" d="M{x(corde) - 2.4:.1f} 5.6l4.8 4.8m0-4.8l-4.8 4.8"/>')
        elif fret == 0:
            elements.append(f'<circle class="v" cx="{x(corde):.1f}" cy="8" r="2.6"/>')

    if appuyees:
        # a barre: the lowest pressed fret on two or more strings, with nothing open or muted between
        bas_fret = min(appuyees)
        cordes = [c for c, f in enumerate(frettes) if f == bas_fret]
        if len(cordes) > 1 and all(frettes[c] and frettes[c] >= bas_fret for c in range(cordes[0], cordes[-1] + 1)):
            elements.append(f'<rect class="p" x="{x(cordes[0]) - 3.6:.1f}" y="{y(bas_fret) - 3.6:.1f}" '
                            f'width="{x(cordes[-1]) - x(cordes[0]) + 7.2:.1f}" height="7.2" rx="3.6"/>')
        for corde, fret in enumerate(frettes):
            if fret:
                elements.append(f'<circle class="p" cx="{x(corde):.1f}" cy="{y(fret):.1f}" r="3.6"/>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGEUR:.1f} {bas + 3:.1f}" '
            f'role="img" aria-label="{doigte}"><style>{STYLE}</style>\n' + '\n'.join(elements) + '\n</svg>\n')


def fiches_des_chansons():
    """Return every (chord name, fingering) written in the `Accords :` blocks of the songs.

    Returns:
        Sorted list of distinct (name, fingering) pairs (list of tuples).
    """
    trouvees = set()
    for fichier in CHANSONS.glob('*/[0-9]*.md'):
        for ligne in fichier.read_text(encoding='utf-8').split('\n'):
            m = FICHE.match(ligne.rstrip())
            if m:
                trouvees.add(m.groups())
    return sorted(trouvees)


def ecrire(a_blanc=False):
    """Write the diagram of every fingering used in the songs.

    Args:
        a_blanc: if True, only report what would be written (bool).

    Returns:
        (number of files written or to write, fingerings that cannot be drawn, stale files).
    """
    ACCORDS.mkdir(exist_ok=True)
    ecrits, impossibles, voulus = 0, [], set()
    for nom, doigte in fiches_des_chansons():
        svg = dessiner(doigte)
        if svg is None:
            impossibles.append((nom, doigte))
            continue
        cible = ACCORDS / nom_fichier(nom, doigte)
        voulus.add(cible.name)
        if not cible.exists() or cible.read_text(encoding='utf-8') != svg:
            ecrits += 1
            if not a_blanc:
                cible.write_text(svg, encoding='utf-8')
    perimes = sorted(p.name for p in ACCORDS.glob('*.svg') if p.name not in voulus)
    return ecrits, impossibles, perimes


if __name__ == '__main__':
    analyseur = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    analyseur.add_argument('--a-blanc', action='store_true', help='only report, write nothing')
    arguments = analyseur.parse_args()
    n, impossibles, perimes = ecrire(arguments.a_blanc)
    print(f'{n} diagram(s) {"to write" if arguments.a_blanc else "written"}')
    for nom, doigte in impossibles:
        print(f'cannot draw {nom} : {doigte}')
    for nom in perimes:
        print(f'stale (no song uses it): accords/{nom}')
