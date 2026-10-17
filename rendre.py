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
import unicodedata

ACCORD = re.compile(r'\[([^\]]+)\]')
EMPHASE = re.compile(r'\*([^*]+)\*')
URL = re.compile(r'(https?://\S+)')
ENTETE = re.compile(r'^\w+: \S')  # `key: value` line between two `---` lines
NOTES = '### Notes'  # opens the collapsed notes section at the end of a song
ARTICLE = re.compile(r"^(?:l['’]|d['’]|(?:le|la|les|un|une|des|du)\s)", re.IGNORECASE)  # ignored when filing a title
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
html { scroll-behavior: smooth; }
h1, h2 { scroll-margin-top: 3.5em; }
.bar { position: sticky; top: 0; z-index: 1; display: flex; align-items: center; gap: 0.6em;
       padding: 0.4em 0; background: Canvas; border-bottom: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
       touch-action: none; }
.crumbs { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.crumbs a { text-decoration: none; }
.crumbs .sep { opacity: 0.5; padding: 0 0.3em; }
.up { font-size: 1.2em; line-height: 1; padding: 0.2em 0.5em; cursor: pointer; }
.transpose { margin: 0; white-space: nowrap; }
.az summary { cursor: pointer; font-weight: bold; white-space: nowrap; }
.az-panel { position: absolute; top: 100%; right: 0; width: min(100%, 32em); max-height: 70vh; overflow-y: auto;
            box-sizing: border-box; padding: 0.5em 0.8em; background: Canvas;
            border: 1px solid color-mix(in srgb, CanvasText 20%, transparent); box-shadow: 0 0.4em 1em rgb(0 0 0 / 0.2); }
.az-letters { margin: 0 0 0.4em; line-height: 1.9; }
.az-letters button { font: inherit; min-width: 1.8em; margin: 0 0.1em 0.1em 0; cursor: pointer; }
.az-letters button[aria-pressed="true"] { font-weight: bold; background: Highlight; color: HighlightText; }
.az-group h3 { margin: 0.3em 0 0; }
.az-group ul { columns: 1; margin: 0; padding-left: 1.2em; list-style: none; }
.az-panel[data-js] .az-group[hidden] { display: none; }
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

# Hierarchy navigation: Index > Anthology > Album > Song. The anthology holds every album, so
# going up from a song means scrolling to its album heading, and going up from an album means
# scrolling to the top (anthology) or leaving for the anthology (album page). The current album
# and song are the last `h1` / `h2` scrolled past the sticky bar. A swipe up on the bar (the
# page itself keeps its normal scrolling), the "↑" button or the `u` key go up one level.
SCRIPT_NAVIGATION = """\
(function () {
  var bar = document.getElementById('bar');
  if (!bar) return;
  var albums = Array.prototype.slice.call(document.querySelectorAll('h1[id]'));
  var songs = Array.prototype.slice.call(document.querySelectorAll('h2[id]'));
  var crumbAlbum = document.getElementById('crumb-album');
  var crumbSong = document.getElementById('crumb-song');
  var up = document.getElementById('up');
  var current = {album: null, song: null};

  function passed(list) {
    var limit = bar.offsetHeight + 8, found = null;
    for (var i = 0; i < list.length; i++) {
      if (list[i].getBoundingClientRect().top > limit) break;
      found = list[i];
    }
    return found;
  }

  function crumb(target, heading, strip) {
    target.textContent = '';
    if (!heading) return;
    var sep = document.createElement('span');
    sep.className = 'sep'; sep.textContent = '\u203a';
    var a = document.createElement('a');
    a.href = '#' + heading.id;
    a.textContent = strip ? heading.textContent.replace(/^\\d+\\)\\s*/, '') : heading.textContent;
    target.appendChild(sep); target.appendChild(a);
  }

  function refresh() {
    var album = passed(albums), song = passed(songs);
    if (album !== current.album) crumb(crumbAlbum, album, true);
    if (song !== current.song) crumb(crumbSong, song, false);
    current = {album: album, song: song};
  }

  function goUp() {
    if (current.song && current.album) {
      current.album.scrollIntoView();
    } else if (current.album && bar.getAttribute('data-anthologie')) {
      window.scrollTo(0, 0);
    } else {
      window.location.href = bar.getAttribute('data-haut');
    }
  }

  var pending = false;
  window.addEventListener('scroll', function () {
    if (pending) return;
    pending = true;
    requestAnimationFrame(function () { pending = false; refresh(); });
  }, {passive: true});

  up.addEventListener('click', goUp);
  document.addEventListener('keydown', function (e) {
    var tag = e.target.tagName;
    if (e.key === 'u' && !e.ctrlKey && !e.metaKey && !e.altKey && tag !== 'SELECT' && tag !== 'INPUT') goUp();
  });

  // Alphabetical index: one letter at a time, so that a long list stays short on a phone
  var az = document.getElementById('az');
  if (az) {
    var panel = document.getElementById('az-panel');
    var buttons = Array.prototype.slice.call(panel.querySelectorAll('button[data-lettre]'));
    var groups = Array.prototype.slice.call(panel.querySelectorAll('.az-group'));
    var show = function (letter) {
      groups.forEach(function (g) { g.hidden = g.getAttribute('data-lettre') !== letter; });
      buttons.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-lettre') === letter); });
    };
    buttons.forEach(function (b) { b.addEventListener('click', function () { show(b.getAttribute('data-lettre')); }); });
    panel.setAttribute('data-js', '1');
    if (buttons.length) show(buttons[0].getAttribute('data-lettre'));
    panel.addEventListener('click', function (e) { if (e.target.tagName === 'A') az.open = false; });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') az.open = false; });
    document.addEventListener('click', function (e) { if (az.open && !az.contains(e.target)) az.open = false; });
    panel.querySelector('.az-letters').hidden = false;  // without JavaScript, every group is listed
  }

  var x0 = 0, y0 = 0, inPanel = false;
  bar.addEventListener('touchstart', function (e) {
    x0 = e.touches[0].clientX; y0 = e.touches[0].clientY;
    inPanel = !!(az && az.contains(e.target));  // scrolling the index must not count as a swipe up
  }, {passive: true});
  bar.addEventListener('touchend', function (e) {
    if (inPanel) return;
    var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    if (dy < -30 && Math.abs(dy) > Math.abs(dx)) goUp();
  }, {passive: true});

  up.hidden = false;  // without JavaScript, only the static links remain
  refresh();
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
    return ('<span class="transpose" id="transpose" hidden>'
            '<label for="transpose-select">Transposer : </label>'
            f'<select id="transpose-select">\n{options}\n</select></span>')


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
        (HTML body, list of (anchor id, title, level) for the table of contents; the level
        is 1 for an album, 2 for a song). Anchors are `a{n}` for album n (from its `n)`
        prefix) and `a{n}-s{k}` for its k-th song, hence the same on every page.
    """
    sortie, table = [], []
    album, chanson = 0, 0  # number of the current album, rank of the current song in it
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
                chanson += 1
                ancre = f'a{album}-s{chanson}'
                table.append((ancre, ligne[3:], 2))
                sortie.append(f'<h2 id="{ancre}">{en_ligne(ligne[3:])}</h2>')
            elif ligne.startswith('# '):
                fermer_strophe()
                numero = re.match(r'(\d+)\)', ligne[2:])
                album = int(numero.group(1)) if numero else album + 1
                chanson = 0
                ancre = f'a{album}'
                table.append((ancre, ligne[2:], 1))
                sortie.append(f'<h1 id="{ancre}">{en_ligne(ligne[2:])}</h1>')
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


def liste_chansons(table, ancre_album):
    """Return the HTML list of the songs of one album.

    Args:
        table: (anchor id, title, level) entries, as returned by `rendre_corps` (list of tuples).
        ancre_album: anchor id of the album heading (str).

    Returns:
        HTML fragment, `<nav class="toc">` holding the list (str).
    """
    chansons, dedans = [], False
    for ancre, titre, niveau in table:
        if niveau == 1:
            dedans = ancre == ancre_album
        elif dedans:
            chansons.append(f'<li><a href="#{ancre}">{en_ligne(titre)}</a></li>')
    return '<nav class="toc"><ul>' + ''.join(chansons) + '</ul></nav>'


def liste_albums(table):
    """Return the HTML list of the albums of a page, or '' when it holds a single one.

    Args:
        table: (anchor id, title, level) entries, as returned by `rendre_corps` (list of tuples).

    Returns:
        HTML fragment (str).
    """
    albums = [(a, t) for a, t, niveau in table if niveau == 1]
    if len(albums) <= 1:
        return ''
    return ('<nav class="toc"><ul>'
            + ''.join(f'<li><a href="#{a}">{en_ligne(t)}</a></li>' for a, t in albums)
            + '</ul></nav>\n')


def cle_tri(titre):
    """Return the sort key of a song title: lowercase, without accents, articles or punctuation.

    La Marine is filed as `marine`, so it sits under M between Marinette's neighbours.

    Args:
        titre: song title as written in the Markdown (str).

    Returns:
        Sort key (str); empty when the title holds no letter.
    """
    texte = unicodedata.normalize('NFKD', titre.replace('*', '')).encode('ascii', 'ignore').decode()
    texte = re.sub(r'^[^A-Za-z]+', '', texte)
    texte = ARTICLE.sub('', texte)
    return re.sub(r'^[^A-Za-z]+', '', texte).lower()


def lettre_tri(titre):
    """Return the letter under which a song title is filed in the alphabetical index.

    Args:
        titre: song title as written in the Markdown (str).

    Returns:
        An uppercase letter A-Z, or '#' when the title holds none (str).
    """
    return cle_tri(titre)[:1].upper() or '#'


def index_alphabetique(table):
    """Return the alphabetical index of the songs of a page, for the sticky bar.

    Args:
        table: (anchor id, title, level) entries, as returned by `rendre_corps` (list of tuples).

    Returns:
        HTML fragment, a `<details>` menu (str); '' when the page holds no song.
    """
    par_lettre = {}
    for ancre, titre, niveau in table:
        if niveau == 2:
            par_lettre.setdefault(lettre_tri(titre), []).append((titre, ancre))
    if not par_lettre:
        return ''
    lettres = sorted(par_lettre)
    boutons = ''.join(f'<button type="button" data-lettre="{l}">{l}</button>' for l in lettres)
    groupes = '\n'.join(
        f'<section class="az-group" data-lettre="{l}"><h3>{l}</h3><ul>'
        + ''.join(f'<li><a href="#{a}">{en_ligne(t)}</a></li>'
                  for t, a in sorted(par_lettre[l], key=lambda e: cle_tri(e[0])))
        + '</ul></section>' for l in lettres)
    return ('<details class="az" id="az"><summary title="Index alphabétique des chansons">A–Z</summary>\n'
            f'<div class="az-panel" id="az-panel"><p class="az-letters" hidden>{boutons}</p>\n{groupes}</div>'
            '</details>')


def fil_ariane(table, accueil, anthologie):
    """Return the sticky bar: breadcrumb, "up" button, alphabetical index and transposition menu.

    The album and song crumbs are filled in by `SCRIPT_NAVIGATION` while scrolling.

    Args:
        table: (anchor id, title, level) entries of the page (list of tuples).
        accueil: relative link to the index page (str).
        anthologie: relative link to the anthology page, or None on the anthology itself (str).

    Returns:
        HTML fragment (str).
    """
    albums = [a for a, _, niveau in table if niveau == 1]
    if anthologie:
        haut = f'{anthologie}#{albums[0]}' if albums else anthologie
        attribut_anthologie, lien = '', haut
    else:
        haut, attribut_anthologie, lien = accueil, ' data-anthologie="1"', '#'
    return (f'<header class="bar" id="bar" data-haut="{html.escape(haut)}"{attribut_anthologie}>\n'
            f'<span class="crumbs"><a href="{html.escape(accueil)}">Index</a>'
            f'<span class="sep">&rsaquo;</span><a href="{html.escape(lien)}">Anthologie</a>'
            '<span id="crumb-album"></span><span id="crumb-song"></span></span>\n'
            '<button class="up" id="up" type="button" hidden '
            'title="Monter d\'un niveau (touche u, ou balayer vers le haut)" '
            'aria-label="Monter d\'un niveau">&uarr;</button>\n'
            f'{index_alphabetique(table)}\n'
            f'{selecteur_transposition()}\n</header>')


def rendre_fichier(source, destination, titre, accueil, anthologie=None):
    """Render a Markdown file to a self-contained HTML page.

    Args:
        source: Markdown file to read (Path).
        destination: HTML file to write (Path).
        titre: text of the HTML `<title>` (str).
        accueil: relative link to the index page (str).
        anthologie: relative link to the anthology page, or None when rendering the anthology
            itself (str).
    """
    corps, table = rendre_corps(source.read_text(encoding='utf-8').split('\n'))
    # the songs of an album are listed right below its title; the top of the page only lists
    # the albums (anthology)
    for ancre, titre_album, niveau in table:
        if niveau == 1:
            titre_html = f'<h1 id="{ancre}">{en_ligne(titre_album)}</h1>'
            corps = corps.replace(titre_html, f'{titre_html}\n{liste_chansons(table, ancre)}', 1)
    destination.write_text(
        page(titre, f'{fil_ariane(table, accueil, anthologie)}\n{liste_albums(table)}{corps}',
             script=SCRIPT + SCRIPT_NAVIGATION),
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
