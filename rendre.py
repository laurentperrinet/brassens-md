"""Render the song Markdown (ChordPro-like chords inline) to a self-contained HTML page.

Accepted input, which is all the song sources use:

    # 1) ALBUM TITLE                    -> <h1>
    ## SONG TITLE                       -> <h2>, listed in the table of contents
    [Am]Au villa[E]ge, [Am]sans ...     -> one lyric line; each [Chord] is a bold monospace <b>
    ---\nyouTubeId: xxxx\n---           -> embedded tutorial video (any other `---` is a <hr>)
     * valse                            -> bullet list
    *Refrain :*                         -> <em>
    ### Notes                           -> collapsed <details> up to the next `#` / `##` title

The `### Notes` section closes a song: free comments and links (no chords, no stanzas),
hidden until the reader clicks on "Notes".

A single blank line between two lines is only a separator; two or more blank lines
mark a break between stanzas.
"""
import html
import re
import sys

ACCORD = re.compile(r'\[([^\]]+)\]')
EMPHASE = re.compile(r'\*([^*]+)\*')
URL = re.compile(r'(https?://\S+)')
ENTETE = re.compile(r'^\w+: \S')  # `key: value` line between two `---` lines
NOTES = '### Notes'  # opens the collapsed notes section at the end of a song
YOUTUBE = 'https://www.youtube.com/watch?v={}'
YOUTUBE_INTEGRE = 'https://www.youtube-nocookie.com/embed/{}'
YOUTUBE_IDENTIFIANT = re.compile(r'^[\w-]{11}$')  # a valid video identifier is 11 characters long

CSS = """\
body { font-family: Georgia, serif; line-height: 1.5; max-width: 50em; margin: 0 auto; padding: 0 1em; }
nav ul { columns: 2 20em; list-style: none; padding: 0; }
.stanza { margin-bottom: 1.2em; break-inside: avoid; }
.line { margin: 0; }
.notes { margin: 1em 0 2em; }
.notes summary { cursor: pointer; font-weight: bold; }
.notes p, .notes ul { margin: 0.4em 0; }
.video iframe { width: 100%; aspect-ratio: 16 / 9; border: 0; }
.video p { margin: 0.2em 0 1em; font-size: 0.9em; }
b.chord { font-family: ui-monospace, Menlo, Consolas, monospace; font-weight: bold; }
.transpose { position: sticky; top: 0; z-index: 1; padding: 0.4em 0; background: Canvas; }
"""

# Transposition runs in the browser: the site is static, so no server can recompute chords.
# Every chord keeps its original spelling in `data-original`, hence going back to "Original"
# (or chaining several transpositions) never accumulates rounding of sharps and flats.
# Notes are spelled C C# D Eb E F F# G Ab A Bb B, as guitarists write them, except that minor
# and diminished chords use the sharp spelling (C#m, D#m, G#m, A#m), as in the song sources.
SCRIPT = """\
(function () {
  var select = document.getElementById('transpose-select');
  if (!select) return;
  var SEMITONES = {C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11};
  var MAJOR = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'];
  var MINOR = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  var NOTE = /^([A-G])([#b]?)/;

  function pitch(name) {
    var m = NOTE.exec(name);
    var accidental = m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0;
    return (SEMITONES[m[1]] + accidental + 12) % 12;
  }

  function spell(pc, sharp) {
    return (sharp ? MINOR : MAJOR)[(pc % 12 + 12) % 12];
  }

  // `Bb7sus4`, `F#m7`, `Ab6/9`, `G#dim/F`: a root, a quality, then an optional bass note
  function transposeChord(chord, shift) {
    var m = NOTE.exec(chord);
    if (!m) return chord;
    var root = m[0], rest = chord.slice(root.length);
    var sharp = /^(m(?!aj)|dim)/.test(rest);
    var bass = /\\/([A-G][#b]?)$/.exec(rest);
    var out = spell(pitch(root) + shift, sharp) + rest.replace(/\\/([A-G][#b]?)$/, '');
    if (bass) out += '/' + spell(pitch(bass[1]) + shift, sharp);
    return out;
  }

  var chords = Array.prototype.slice.call(document.querySelectorAll('b.chord'));
  chords.forEach(function (el) { el.setAttribute('data-original', el.textContent); });

  select.addEventListener('change', function () {
    var shift = parseInt(select.value, 10);
    chords.forEach(function (el) {
      el.textContent = transposeChord(el.getAttribute('data-original'), shift);
    });
  });
  document.getElementById('transpose').hidden = false;  // without JavaScript, stays hidden
})();
"""

# Menu labels: the shift in semitones, written in tones (one tone = two semitones).
TRANSPOSITIONS = range(-6, 7)


def etiquette_transposition(demi_tons):
    """Return the menu label of a transposition.

    Args:
        demi_tons: shift (semitones, signed int); 0 is the original key.

    Returns:
        Label such as `-2 tons`, `-1 ton ½`, `Original` or `+½ ton` (str).
    """
    if demi_tons == 0:
        return 'Original'
    tons, reste = divmod(abs(demi_tons), 2)
    signe = '−' if demi_tons < 0 else '+'
    if not tons:
        return f'{signe}½ ton'
    return f'{signe}{tons} ton{"s" if tons >= 2 else ""}' + (' ½' if reste else '')


def selecteur_transposition():
    """Return the HTML of the transposition menu (hidden until the script runs).

    Returns:
        HTML fragment (str).
    """
    options = '\n'.join(
        f'<option value="{n}"{" selected" if n == 0 else ""}>{etiquette_transposition(n)}</option>'
        for n in TRANSPOSITIONS)
    return ('<p class="transpose" id="transpose" hidden>'
            '<label for="transpose-select">Transposer : </label>'
            f'<select id="transpose-select">\n{options}\n</select></p>')


def en_ligne(texte):
    """Convert one line of text to HTML.

    Args:
        texte: raw line, possibly with `[Chord]` markers, `*emphasis*` and URLs (str).

    Returns:
        HTML fragment where text is escaped and chords are wrapped in `<b class="chord">` (str).
    """
    texte = html.escape(texte, quote=False)
    texte = ACCORD.sub(r'<b class="chord">\1</b>', texte)
    texte = EMPHASE.sub(r'<em>\1</em>', texte)
    return URL.sub(r'<a href="\1">\1</a>', texte)


def en_note(texte):
    """Convert one line of a notes section to HTML.

    Unlike `en_ligne`, square brackets stay literal: notes hold prose, not chords.

    Args:
        texte: raw line, possibly with `*emphasis*` and URLs (str).

    Returns:
        HTML fragment (str).
    """
    texte = html.escape(texte, quote=False)
    texte = EMPHASE.sub(r'<em>\1</em>', texte)
    return URL.sub(r'<a href="\1">\1</a>', texte)


def video(identifiant):
    """Return the HTML of a tutorial video to learn a song.

    The player is loaded lazily, so a page only contacts YouTube when the video is scrolled
    into view. A link to YouTube is always given, in case embedding is refused.

    Args:
        identifiant: YouTube identifier of the video (str).

    Returns:
        HTML fragment (str).
    """
    lien = (f'<p><a href="{YOUTUBE.format(identifiant)}">'
            'Vidéo pour apprendre la chanson (YouTube)</a></p>')
    if not YOUTUBE_IDENTIFIANT.match(identifiant):
        print(f'warning: invalid YouTube identifier {identifiant!r}, no player embedded',
              file=sys.stderr)
        return f'<div class="video">{lien}</div>'
    return (f'<div class="video">\n<iframe src="{YOUTUBE_INTEGRE.format(identifiant)}" '
            f'title="Vidéo pour apprendre la chanson" loading="lazy" '
            f'allow="encrypted-media; picture-in-picture" allowfullscreen></iframe>\n'
            f'{lien}\n</div>')


def rendre_corps(lignes):
    """Convert the lines of a Markdown document to HTML.

    Args:
        lignes: lines of the document, without line terminators (list of str).

    Returns:
        (HTML body, list of (anchor id, song title) for the table of contents).
    """
    sortie, table = [], []
    strophe = []   # lines of the stanza being collected (HTML strings)
    vides = 0      # consecutive blank lines seen
    sauter = 0     # number of lines already consumed as part of a header block
    notes = False  # inside a `### Notes` section

    def fermer_notes():
        nonlocal notes
        if notes:
            sortie.append('</details>')
            notes = False

    def fermer_strophe():
        if strophe:
            sortie.append('<div class="stanza">\n' + '\n'.join(strophe) + '\n</div>')
            strophe.clear()

    for i, ligne in enumerate(lignes):
        ligne = ligne.rstrip()
        if sauter:
            sauter -= 1
        elif (ligne == '---' and i + 2 < len(lignes) and ENTETE.match(lignes[i + 1])
              and lignes[i + 2].rstrip() == '---'):
            # `---` / `key: value` / `---` header; any other `---` is a stanza separator
            cle, _, valeur = lignes[i + 1].partition(':')
            if cle == 'youTubeId':
                sortie.append(video(valeur.strip()))
            sauter = 2
        elif ligne == NOTES:
            fermer_strophe()
            fermer_notes()
            sortie.append('<details class="notes">\n<summary>Notes</summary>')
            notes = True
        elif notes and not ligne.startswith(('# ', '## ')):
            if ligne.lstrip().startswith(('* ', '- ')):
                sortie.append(f'<ul><li>{en_note(ligne.lstrip()[2:])}</li></ul>')
            elif ligne:
                sortie.append(f'<p>{en_note(ligne)}</p>')
        elif ligne == '---':
            fermer_strophe()
            sortie.append('<hr>')
            vides = 0
        elif not ligne:
            vides += 1
            if vides >= 2:
                fermer_strophe()
        else:
            if vides >= 2:
                fermer_strophe()
            vides = 0
            if ligne.startswith(('# ', '## ')):
                fermer_notes()
            if ligne.startswith('## '):
                fermer_strophe()
                ancre = f's{len(table) + 1}'
                table.append((ancre, ligne[3:]))
                sortie.append(f'<h2 id="{ancre}">{en_ligne(ligne[3:])}</h2>')
            elif ligne.startswith('# '):
                fermer_strophe()
                sortie.append(f'<h1>{en_ligne(ligne[2:])}</h1>')
            elif ligne.startswith(' * '):
                fermer_strophe()
                sortie.append(f'<ul><li>{en_ligne(ligne[3:])}</li></ul>')
            else:
                strophe.append(f'<p class="line">{en_ligne(ligne)}</p>')
    fermer_strophe()
    fermer_notes()
    return '\n'.join(sortie), table


def page(titre, contenu, script=''):
    """Wrap an HTML body in a self-contained page (with its CSS).

    Args:
        titre: text of the HTML `<title>` (str).
        contenu: HTML to put inside `<body>` (str).
        script: JavaScript to run once the body is loaded, or '' for none (str).

    Returns:
        The complete HTML document (str).
    """
    balise = f'<script>\n{script}</script>\n' if script else ''
    return ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{html.escape(titre)}</title>\n<style>\n{CSS}</style>\n</head>\n<body>\n'
            f'{contenu}\n{balise}</body>\n</html>\n')


def rendre_fichier(source, destination, titre, accueil=None):
    """Render a Markdown file to a self-contained HTML page.

    Args:
        source: Markdown file to read (Path).
        destination: HTML file to write (Path).
        titre: text of the HTML `<title>` (str).
        accueil: relative link to the table of contents page, or None for no link (str).
    """
    corps, table = rendre_corps(source.read_text(encoding='utf-8').split('\n'))
    nav = ''.join(f'<li><a href="#{a}">{en_ligne(t)}</a></li>' for a, t in table)
    retour = f'<p><a href="{accueil}">&larr; Index</a></p>\n' if accueil else ''
    destination.write_text(
        page(titre, f'{retour}{selecteur_transposition()}\n<nav><ul>{nav}</ul></nav>\n{corps}',
             script=SCRIPT),
        encoding='utf-8')


def rendre_index(entrees, destination, titre):
    """Write the home page: a list of links to the other pages.

    Args:
        entrees: (link text, relative URL) of each page to list (list of (str, str)).
        destination: HTML file to write (Path).
        titre: page title, also used as heading (str).
    """
    elements = '\n'.join(f'<li><a href="{html.escape(url)}">{html.escape(texte)}</a></li>'
                         for texte, url in entrees)
    destination.write_text(
        page(titre, f'<h1>{html.escape(titre)}</h1>\n<ul>\n{elements}\n</ul>'),
        encoding='utf-8')
