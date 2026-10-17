"""Render the song Markdown (ChordPro-like chords inline) to a self-contained HTML page.

Accepted input, which is all the song sources use:

    # 1) ALBUM TITLE                    -> <h1>
    ## SONG TITLE                       -> <h2>, listed under its album title
    [Am]Au villa[E]ge, [Am]sans ...     -> one lyric line; each [Chord] is shown above the lyrics (<ruby>)
    ---\nyouTubeId: xxxx\n---           -> embedded tutorial video (any other `---` is a <hr>)
     * valse                            -> bullet list
    Refrain :   Intro : [Am] ...        -> the keyword (Refrain, Intro, Interlude, Pont, ...) is a badge, set apart from the lyrics
    *Refrain :*                         -> same badge
    Grille : |: Dm . . | A7 . . :|      -> chord grid (green badge, monospace, bar lines dimmed); a line
                                           starting with `|` and holding no [Chord] is a grid too
    <!-- source: chansons/.../x.md -->   -> (written by assembler.py) gives the next song title an "éditer" link to GitHub
    ### Notes                           -> collapsed <details> up to the next `#` / `##` title
    ```  ...  ```                       -> a monospace <pre> block (a tablature), in the lyrics or in the notes

The `### Notes` section closes a song: free comments and links (no chords, no stanzas),
hidden until the reader clicks on "Notes" (a link on the right of the song title, or the
triangle below the score).

Favourites: every song title gets a star button (and the `f` key toggles the current song).
They are kept in the browser (`localStorage`) and collected on `favoris.html`, which behaves as
one more album built in the browser from the anthology page.

A single blank line between two lines is only a separator; two or more blank lines
mark a break between stanzas.
"""
import html
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

ACCORD = re.compile(r'\[([^\]]+)\]([^\s\[<*]*)')  # a chord and the word fragment it sits above
EMPHASE = re.compile(r'\*([^*]+)\*')
# A structure keyword opening a line ("Refrain :", "Intro : [Am] ...", "*Refrain :*"), set apart from the lyrics.
MOT_CLE = re.compile(r'^\*?(Refrain|Intro|Interlude|Pont|Outro|Coda|Solo|Final|Grille)(?:\s*:\*?|\*?\s*$)(.*)$')
# A chord grid written without keyword: it starts with a bar line and has no inline [Chord].
GRILLE = re.compile(r'^\|[^\[\]]*$')
BARRE = re.compile(r':\||\|[:.|]?')  # `|`, `|:`, `:|`, `||`, `|.`
URL = re.compile(r'(https?://\S+)')
ENTETE = re.compile(r'^\w+: \S')  # `key: value` line between two `---` lines
NOTES = '### Notes'  # opens the collapsed notes section at the end of a song
CLOTURE = '```'  # opens and closes a monospace block (a tablature), in the lyrics or in the notes
ARTICLE = re.compile(r"^(?:l['’]|d['’]|(?:le|la|les|un|une|des|du)\s)", re.IGNORECASE)  # ignored when filing a title
SOURCE = re.compile(r'^<!-- source: (.+) -->$')  # path of the song file, written by `assembler.py`
EDITION = 'https://github.com/laurentperrinet/brassens-md/edit/master/{}'  # GitHub editor of a source file
YOUTUBE = 'https://www.youtube.com/watch?v={}'
YOUTUBE_INTEGRE = 'https://www.youtube-nocookie.com/embed/{}'
YOUTUBE_IDENTIFIANT = re.compile(r'^[\w-]{11}$')  # a valid video identifier is 11 characters long

FAVICON_SVG = Path(__file__).parent / 'favicon.svg'  # a cat in front of a guitar


def en_grille(texte):
    """Return the HTML of a chord grid, its bar lines wrapped in a dimmed `<span>`.

    Args:
        texte: the grid as written, e.g. `|: Dm . . | A7 . . :|` (str).

    Returns:
        HTML fragment (str).
    """
    barres = BARRE.sub(lambda m: f'\0{m.group(0)}\1', texte)
    return html.escape(barres).replace('\0', '<span class="barre">').replace('\1', '</span>')


def favicon_uri():
    """Return the favicon as a `data:` URI, usable in a `<link>` or an `<img>`.

    The SVG is inlined, so that the pages stay self-contained and the icon is found
    whatever the depth of the page in `docs/`.

    Returns:
        The data URI (str).
    """
    svg = re.sub(r'<!--.*?-->|\s*\n\s*', '', FAVICON_SVG.read_text(encoding='utf-8'), flags=re.DOTALL)
    return 'data:image/svg+xml,' + quote(svg, safe='/:=')


def favicon():
    """Return the `<link>` tag that gives every page its icon.

    Returns:
        The `<link rel="icon">` tag (str).
    """
    return f'<link rel="icon" type="image/svg+xml" href="{favicon_uri()}">\n'


CSS = """\
body { font-family: Georgia, serif; line-height: 1.5; max-width: 50em; margin: 0 auto; padding: 0 1em; }
nav ul { columns: 2 20em; list-style: none; padding: 0; }
.stanza { margin-bottom: 1.2em; break-inside: avoid; }
.line { margin: 0; line-height: 2.1; }
.section { font-family: ui-sans-serif, system-ui, sans-serif; font-size: 0.8em; font-weight: 700;
           text-transform: uppercase; letter-spacing: 0.08em; padding: 0.1em 0.6em; border-radius: 1em;
           color: light-dark(#1f4e79, #9cc7ee); background: light-dark(#dcebf8, #1c3550); }
ruby { ruby-align: start; ruby-position: over;
       border-left: 1px solid color-mix(in srgb, CanvasText 25%, transparent); }  /* tick down to the character */
rt { font-size: 0.8em; line-height: 1; }
.section.grille { color: light-dark(#1d6b3c, #8fd6a6); background: light-dark(#dcf3e3, #1d3b2a); }
.grille-texte { font-family: ui-monospace, Menlo, Consolas, monospace; white-space: pre-wrap; }
.grille-texte .barre { color: light-dark(#7a8a80, #6f8478); font-weight: 700; }
.notes { margin: 1em 0 2em; }
.notes summary { cursor: pointer; font-weight: bold; }
.notes p, .notes ul { margin: 0.4em 0; }
pre.tab { margin: 0.8em 0; overflow-x: auto; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 0.85em; line-height: 1.25; }
.video iframe { width: min(100%, calc(70vh * 16 / 9)); aspect-ratio: 16 / 9; border: 0; }
.video p { margin: 0.2em 0 1em; font-size: 0.9em; }
b.chord { font-family: ui-monospace, Menlo, Consolas, monospace; font-weight: 700;
          color: light-dark(#5a3a00, #ffd966); background: light-dark(#fff1b8, #4a3a10);
          padding: 0 0.3em; border-radius: 0.25em; }
html { scroll-behavior: smooth; }
h1, h2 { scroll-margin-top: 3.5em; }
h2 { display: flex; align-items: baseline; gap: 0.4em; }
.notes-lien { font: inherit; font-size: 0.6em; margin-left: auto; padding: 0 0.3em; border: 0; background: none;
              color: LinkText; text-decoration: underline; cursor: pointer; white-space: nowrap; }
.editer { font-size: 0.6em; margin-left: auto; padding: 0 0.3em; white-space: nowrap; }
.editer + .notes-lien { margin-left: 0; }
.bar { position: sticky; top: 0; z-index: 1; display: flex; align-items: center; gap: 0.6em;
       padding: 0.4em 0; background: Canvas; border-bottom: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
       touch-action: none; }
.crumbs { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.crumbs a { text-decoration: none; }
.crumbs .sep { opacity: 0.5; padding: 0 0.3em; }
.up { font-size: 1.2em; line-height: 1; padding: 0.2em 0.5em; cursor: pointer; }
.transpose { margin: 0; white-space: nowrap; }
.fav { font: inherit; font-size: 0.8em; padding: 0 0.3em; border: 0; background: none; color: inherit;
       cursor: pointer; opacity: 0.55; }
.fav:hover, .fav[aria-pressed="true"] { opacity: 1; }
.fav[aria-pressed="true"] { color: goldenrod; }
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
/* home page: three levels (albums, songs per album, alphabetical index) */
.entete { display: flex; align-items: center; justify-content: space-between; gap: 1em; }
.pastille { flex: none; width: 3.6em; height: 3.6em; padding: 0.8em; border-radius: 50%;  /* padding >= 0.2 x width keeps the corners of the drawing inside the disc */
            background: color-mix(in srgb, CanvasText 8%, transparent); }
.niveaux { position: sticky; top: 0; z-index: 1; display: flex; flex-wrap: wrap; gap: 0.3em 1.2em; padding: 0.4em 0;
           background: Canvas; border-bottom: 1px solid color-mix(in srgb, CanvasText 20%, transparent); }
.niveaux a, .haut a { text-decoration: none; }
.haut { margin: 0.5em 0 1.5em; font-size: 0.9em; text-align: right; }
table.albums, table.chansons { border-collapse: collapse; width: 100%; margin: 0.5em 0; }
table.albums th, table.albums td, table.chansons th, table.chansons td { padding: 0.2em 0.6em; text-align: left;
           border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent); }
table.albums td:nth-child(1), table.albums td:nth-child(3), table.albums td:nth-child(4),
table.chansons td:nth-child(1) { width: 1%; white-space: nowrap; text-align: right; }
table.albums th:nth-child(1), table.albums th:nth-child(3), table.albums th:nth-child(4),
table.chansons th:nth-child(1) { text-align: right; }
.page { font-size: 0.8em; margin-left: 0.5em; }
h2[id], h3[id] { scroll-margin-top: 3em; }
.lettres a { display: inline-block; min-width: 1.6em; text-align: center; }
.az-index { columns: 2 18em; list-style: none; padding: 0; }
.az-index li { break-inside: avoid; }
html { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }  /* iOS must not inflate text on rotation */
/* Touch devices (phone, tablet) and full-screen mode (`html.ample`, set by the bar's button): fill
   the screen instead of keeping a desktop-width column. The text size follows the viewport width,
   and in landscape the stanzas flow into as many columns as fit. Headings, video, notes and lists
   span all the columns, so reading order stays top to bottom within each section. */
@media (pointer: coarse) {
  body { max-width: none; font-size: clamp(1rem, 0.85rem + 0.9vw, 1.4rem);
         padding-left: max(1em, env(safe-area-inset-left));
         padding-right: max(1em, env(safe-area-inset-right)); }
}
@media (pointer: coarse) and (orientation: landscape) {
  main { column-width: 20em; column-gap: 2.5em; column-rule: 1px solid color-mix(in srgb, CanvasText 15%, transparent); }
  main > h1, main > h2, main > hr, main > ul, main > nav, main > .video, main > .notes, main > pre.tab { column-span: all; }
}
html.ample body { max-width: none; font-size: clamp(1rem, 0.85rem + 0.9vw, 1.4rem);
                  padding-left: max(1em, env(safe-area-inset-left));
                  padding-right: max(1em, env(safe-area-inset-right)); }
@media (orientation: landscape) {
  html.ample main { column-width: 20em; column-gap: 2.5em; column-rule: 1px solid color-mix(in srgb, CanvasText 15%, transparent); }
  html.ample main > h1, html.ample main > h2, html.ample main > hr, html.ample main > ul, html.ample main > nav,
  html.ample main > .video, html.ample main > .notes, html.ample main > pre.tab { column-span: all; }
}
.plein-ecran { padding: 0.2em 0.4em; line-height: 1; cursor: pointer; color: inherit; background: none; border: 0; }
.plein-ecran svg { width: 1.2em; height: 1.2em; display: block; fill: none; stroke: currentColor; stroke-width: 2;
                   stroke-linecap: round; stroke-linejoin: round; }
.plein-ecran .reduire, .plein-ecran[aria-pressed="true"] .agrandir { display: none; }
.plein-ecran[aria-pressed="true"] .reduire { display: block; }
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

  // chords are looked up at each change, since the favourites page fills itself after loading
  select.addEventListener('change', function () {
    var shift = parseInt(select.value, 10);
    Array.prototype.forEach.call(document.querySelectorAll('b.chord'), function (el) {
      if (!el.hasAttribute('data-original')) el.setAttribute('data-original', el.textContent);
      el.textContent = transposeChord(el.getAttribute('data-original'), shift);
    });
  });
  document.getElementById('transpose').hidden = false;  // without JavaScript, stays hidden
})();
"""

# Favourites: a song is identified by its title (anchors such as `a3-s2` change when songs are
# added or reordered). The list lives in `localStorage` and is shared by every page of the site.
# `favoris.html` holds an empty `main[data-source]`: it fetches the anthology page and copies the
# favourite songs from it, in anthology order. Without JavaScript the stars do not appear.
SCRIPT_FAVORIS = """\
(function () {
  var KEY = 'brassens-favoris';
  var main = document.querySelector('main[data-source]');  // set on the favourites page only
  var bar = document.getElementById('bar');
  var source = null, rendered = [];

  function read() {
    try { var v = JSON.parse(localStorage.getItem(KEY)); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }

  function write(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) {}
  }

  function mark(button, on) {
    button.textContent = on ? '★' : '☆';
    button.setAttribute('aria-pressed', on ? 'true' : 'false');
    button.title = on ? 'Retirer des favoris (touche f)' : 'Ajouter aux favoris (touche f)';
  }

  function toggle(title) {
    var list = read(), i = list.indexOf(title);
    if (i < 0) list.push(title); else list.splice(i, 1);
    write(list);
    Array.prototype.forEach.call(document.querySelectorAll('h2[data-titre]'), function (h) {
      mark(h.querySelector('.fav'), list.indexOf(h.getAttribute('data-titre')) >= 0);
    });
    if (main && source) render();
  }

  function decorate(h2) {
    var title = h2.textContent.trim();
    h2.setAttribute('data-titre', title);
    var button = document.createElement('button');
    button.type = 'button'; button.className = 'fav';
    mark(button, read().indexOf(title) >= 0);
    button.addEventListener('click', function () { toggle(title); });
    h2.appendChild(button);

    // Link to the source file of the song on GitHub (set by the renderer as data-fichier).
    var source = h2.getAttribute('data-fichier');
    if (source) {
      var edit = document.createElement('a');
      edit.className = 'editer'; edit.href = source; edit.textContent = 'éditer';
      edit.target = '_blank'; edit.rel = 'noopener';
      edit.title = 'Éditer la source de cette chanson sur GitHub';
      h2.appendChild(edit);
    }

    // A song with notes gets a link on the right of its title that opens them, where they are:
    // after the score. The "Notes" summary below the score keeps working, and both stay in step.
    var details = null;
    for (var n = h2.nextElementSibling; n && !/^H[12]$/.test(n.tagName); n = n.nextElementSibling) {
      if (n.classList.contains('notes')) { details = n; break; }
    }
    if (!details) return;
    var link = document.createElement('button');
    link.type = 'button'; link.className = 'notes-lien';
    function sync() {
      link.textContent = details.open ? 'Notes ▾' : 'Notes ▸';
      link.setAttribute('aria-expanded', details.open ? 'true' : 'false');
    }
    link.addEventListener('click', function () {
      details.open = !details.open;
      if (details.open) details.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    });
    details.addEventListener('toggle', sync);
    sync();
    h2.appendChild(link);
  }

  function render() {
    rendered.forEach(function (node) { node.remove(); });
    rendered = [];
    var wanted = read(), nodes = [], list = document.createElement('ul');
    Array.prototype.forEach.call(source.querySelectorAll('main > h2'), function (h2) {
      if (wanted.indexOf(h2.textContent.trim()) < 0) return;
      var item = document.createElement('li'), link = document.createElement('a');
      link.href = '#' + h2.id; link.textContent = h2.textContent.trim();
      item.appendChild(link); list.appendChild(item);
      for (var n = h2; n && (n === h2 || !/^H[12]$/.test(n.tagName)); n = n.nextElementSibling) {
        nodes.push(document.importNode(n, true));
      }
    });
    document.getElementById('vide').hidden = nodes.length > 0;
    if (nodes.length) {
      var toc = document.createElement('nav');
      toc.className = 'toc'; toc.appendChild(list);
      nodes.unshift(toc);
    }
    nodes.forEach(function (node) {
      main.appendChild(node); rendered.push(node);
      if (node.tagName === 'H2') decorate(node);
    });
    var select = document.getElementById('transpose-select');
    if (select && select.value !== '0') select.dispatchEvent(new Event('change'));
    window.dispatchEvent(new Event('scroll'));  // refreshes the breadcrumb
  }

  Array.prototype.forEach.call(document.querySelectorAll('main > h2'), decorate);

  if (main) {
    fetch(main.getAttribute('data-source'))
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (text) {
        source = new DOMParser().parseFromString(text, 'text/html');
        render();
      })
      .catch(function () {
        document.getElementById('vide').textContent =
          "Impossible de charger l'anthologie (le site doit être ouvert en http, pas en file://).";
      });
  }

  // `f` toggles the song under the sticky bar
  document.addEventListener('keydown', function (e) {
    var tag = e.target.tagName;
    if (e.key !== 'f' || e.ctrlKey || e.metaKey || e.altKey || tag === 'SELECT' || tag === 'INPUT') return;
    var limit = (bar ? bar.offsetHeight : 0) + 8, found = null;
    var songs = document.querySelectorAll('h2[data-titre]');
    for (var i = 0; i < songs.length; i++) {
      if (songs[i].getBoundingClientRect().top > limit) break;
      found = songs[i];
    }
    if (found) toggle(found.getAttribute('data-titre'));
  });
})();
"""

# Full screen: the bar's button hides the browser chrome (Fullscreen API) and sets `html.ample`,
# which gives the text the whole width, like on a touch device. Where the API is missing (iPhone
# Safari) the button still widens the text. `fullscreenchange` keeps the state in step when the
# user leaves with Esc.
SCRIPT_PLEIN_ECRAN = """\
(function () {
  var button = document.getElementById('plein-ecran');
  if (!button) return;
  var root = document.documentElement;
  var request = root.requestFullscreen || root.webkitRequestFullscreen;
  var exit = document.exitFullscreen || document.webkitExitFullscreen;

  function active() { return !!(document.fullscreenElement || document.webkitFullscreenElement); }

  function show(on) {
    root.classList.toggle('ample', on);
    button.setAttribute('aria-pressed', on);
    button.title = on ? 'Quitter le plein écran' : 'Plein écran';
    window.dispatchEvent(new Event('scroll'));  // the breadcrumb depends on the layout
  }

  button.addEventListener('click', function () {
    var on = !root.classList.contains('ample');
    show(on);
    try {
      var done = on ? request && request.call(root) : active() && exit.call(document);
      if (done && done.catch) done.catch(function () {});  // refused: the wide layout stays
    } catch (e) {}
  });
  ['fullscreenchange', 'webkitfullscreenchange'].forEach(function (name) {
    document.addEventListener(name, function () { show(active()); });
  });
  button.hidden = false;  // without JavaScript, stays hidden
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
    var text = heading.getAttribute('data-titre') || heading.textContent;  // without the star
    a.textContent = strip ? text.replace(/^\\d+\\)\\s*/, '') : text;
    target.appendChild(sep); target.appendChild(a);
  }

  function refresh() {
    // looked up at each scroll: the favourites page gets its headings after loading
    var album = passed(document.querySelectorAll('h1[id]')), song = passed(document.querySelectorAll('h2[id]'));
    if (album !== current.album) crumb(crumbAlbum, album, true);
    if (song !== current.song) crumb(crumbSong, song, false);
    current = {album: album, song: song};
  }

  function goUp() {
    if (current.song) {
      if (current.album) current.album.scrollIntoView(); else window.scrollTo(0, 0);
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


def bouton_plein_ecran():
    """Return the HTML of the full-screen button (hidden until the script runs).

    Returns:
        HTML fragment (str).
    """
    trace = 'viewBox="0 0 24 24" aria-hidden="true"'
    return ('<button class="plein-ecran" id="plein-ecran" type="button" hidden aria-pressed="false" '
            'title="Plein écran" aria-label="Plein écran">'
            f'<svg class="agrandir" {trace}><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>'
            f'<svg class="reduire" {trace}><path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/></svg>'
            '</button>')


def en_ligne(texte):
    """Convert one line of text to HTML.

    Args:
        texte: raw line, possibly with `[Chord]` markers, `*emphasis*` and URLs (str).

    Returns:
        HTML fragment where text is escaped and each chord is a `<b class="chord">` shown
        above the word fragment that follows it, in a `<ruby>` (str).
    """
    texte = html.escape(texte, quote=False)
    # The chord goes above the fragment that follows it (<ruby>), so it never shifts the lyrics.
    # A zero-width base keeps the chord alone when no text follows it (end of line, before a space).
    texte = ACCORD.sub(lambda m: f'<ruby>{m.group(2) or "&#8203;"}<rt><b class="chord">{m.group(1)}</b></rt></ruby>',
                       texte)
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
    bloc = None    # lines (HTML-escaped) of the monospace block being collected
    fichier = None  # path of the source file of the next song, from its `<!-- source: -->` marker

    def fermer_bloc():
        nonlocal bloc
        if bloc is not None:
            sortie.append('<pre class="tab">' + '\n'.join(bloc) + '</pre>')
            bloc = None

    def fermer_notes():
        nonlocal notes
        fermer_bloc()
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
        elif bloc is not None:
            # everything up to the closing fence is kept as is (spaces matter in a tablature)
            if ligne == CLOTURE:
                fermer_bloc()
            else:
                bloc.append(html.escape(ligne, quote=False))
        elif SOURCE.match(ligne):
            # invisible marker: remembered for the next song title
            fichier = SOURCE.match(ligne).group(1)
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
            if ligne == CLOTURE:
                bloc = []
            elif ligne.lstrip().startswith(('* ', '- ')):
                sortie.append(f'<ul><li>{en_note(ligne.lstrip()[2:])}</li></ul>')
            elif ligne:
                sortie.append(f'<p>{en_note(ligne)}</p>')
        elif ligne == CLOTURE:
            # a tablature between two stanzas: it breaks the stanza being collected
            fermer_strophe()
            bloc = []
            vides = 0
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
                lien = f' data-fichier="{html.escape(EDITION.format(quote(fichier)))}"' if fichier else ''
                fichier = None
                sortie.append(f'<h2 id="{ancre}"{lien}>{en_ligne(ligne[3:])}</h2>')
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
                mot = MOT_CLE.match(ligne)
                if GRILLE.match(ligne):
                    strophe.append(f'<p class="line"><span class="section grille">Grille</span> '
                                   f'<span class="grille-texte">{en_grille(ligne)}</span></p>')
                elif mot:
                    # The keyword gets its own class so it cannot be mistaken for a sung line.
                    grille = mot.group(1) == 'Grille'
                    reste = en_grille(mot.group(2).strip()) if grille else en_ligne(mot.group(2).strip())
                    if reste and grille:
                        reste = f'<span class="grille-texte">{reste}</span>'
                    strophe.append(f'<p class="line"><span class="section{" grille" if grille else ""}">'
                                   f'{mot.group(1)}</span>{" " + reste if reste else ""}</p>')
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
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{favicon()}<title>{html.escape(titre)}</title>\n<style>\n{CSS}</style>\n</head>\n<body>\n'
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
            # track number on the record: songs follow the order of the album
            chansons.append(f'<li>{len(chansons) + 1}. <a href="#{ancre}">{en_ligne(titre)}</a></li>')
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


def fil_ariane(table, accueil, album, libelle='Anthologie complète'):
    """Return the sticky bar: breadcrumb, "up" button, alphabetical index, full-screen button and transposition menu.

    The first crumb, "Brassens", is the index page, which lists the albums and their songs.
    The album and song crumbs are filled in by `SCRIPT_NAVIGATION` while scrolling.

    Args:
        table: (anchor id, title, level) entries of the page (list of tuples).
        accueil: relative link to the index page (str).
        album: True on the page of a single album, False on a page that holds several albums
            (the complete anthology) or none (the favourites) (bool).
        libelle: text of the crumb naming the current page, shown when `album` is False (str).

    Returns:
        HTML fragment (str).
    """
    albums = [a for a, _, niveau in table if niveau == 1]
    if album:
        # from an album, going up lands on its own table in the index
        haut, attribut_anthologie, page_courante = (f'{accueil}#t{albums[0]}' if albums else accueil), '', ''
    else:
        haut, attribut_anthologie = accueil, ' data-anthologie="1"'
        page_courante = f'<span class="sep">&rsaquo;</span><a href="#">{html.escape(libelle)}</a>'
    return (f'<header class="bar" id="bar" data-haut="{html.escape(haut)}"{attribut_anthologie}>\n'
            f'<span class="crumbs"><a href="{html.escape(accueil)}">Brassens</a>{page_courante}'
            '<span id="crumb-album"></span><span id="crumb-song"></span></span>\n'
            '<button class="up" id="up" type="button" hidden '
            'title="Monter d\'un niveau (touche u, ou balayer vers le haut)" '
            'aria-label="Monter d\'un niveau">&uarr;</button>\n'
            f'{index_alphabetique(table)}\n'
            f'{bouton_plein_ecran()}\n'
            f'{selecteur_transposition()}\n</header>')


def rendre_fichier(source, destination, titre, accueil, album=False):
    """Render a Markdown file to a self-contained HTML page.

    Args:
        source: Markdown file to read (Path).
        destination: HTML file to write (Path).
        titre: text of the HTML `<title>` (str).
        accueil: relative link to the index page (str).
        album: True when the file holds a single album, False for the complete anthology (bool).
    """
    corps, table = rendre_corps(source.read_text(encoding='utf-8').split('\n'))
    # the songs of an album are listed right below its title; the top of the page only lists
    # the albums (anthology)
    for ancre, titre_album, niveau in table:
        if niveau == 1:
            titre_html = f'<h1 id="{ancre}">{en_ligne(titre_album)}</h1>'
            corps = corps.replace(titre_html, f'{titre_html}\n{liste_chansons(table, ancre)}', 1)
    destination.write_text(
        page(titre, f'{fil_ariane(table, accueil, album)}\n'
                    f'<main>\n{liste_albums(table)}{corps}\n</main>',
             script=SCRIPT + SCRIPT_FAVORIS + SCRIPT_PLEIN_ECRAN + SCRIPT_NAVIGATION),
        encoding='utf-8')


ALBUM = re.compile(r'^(\d+)\) (.*?)(?: \((\d{4})\))?$')  # `3) Le pornographe (1958)`


def decouper_album(titre):
    """Split an album heading into its number, name and year.

    Args:
        titre: heading text such as `3) Le pornographe (1958)` (str).

    Returns:
        (number, name, year), where the number and the year are '' when the heading has none
        (tuple of str).
    """
    m = ALBUM.match(titre)
    return m.groups('') if m else ('', titre, '')


def rendre_index(albums, destination, titre):
    """Write the home page, laid out as the three levels of the anthology.

    Navigation links come first, then level 1 (a table of the albums), level 2 (one table of
    songs per album) and level 3 (an alphabetical index of every song). A song links to its
    anchor in the page of its album.

    Args:
        albums: (URL of the album page relative to `destination`, table of the album as returned
            by `rendre_corps`) for each album (list of (str, list of tuples)).
        destination: HTML file to write (Path).
        titre: page title, also used as heading (str).
    """
    fiches = []  # (anchor, number, name, year, page URL, [(song anchor, song title)])
    for url, table in albums:
        entete = next(t for t in table if t[2] == 1)
        numero, nom, annee = decouper_album(entete[1])
        chansons = [(a, t) for a, t, niveau in table if niveau == 2]
        fiches.append((entete[0], numero, nom, annee, url, chansons))

    def lien(url, ancre, texte):
        return f'<a href="{html.escape(url)}#{ancre}">{en_ligne(texte)}</a>'

    haut = '<p class="haut"><a href="#">&uarr; Haut</a></p>'
    navigation = ('<nav class="niveaux" aria-label="Niveaux">'
                  '<a href="#albums">1. Albums</a>'
                  '<a href="#chansons">2. Chansons par album</a>'
                  '<a href="#alphabet">3. Index alphabétique</a>'
                  '<a href="brassens.html">Anthologie complète</a>'
                  '<a href="favoris.html">Favoris</a></nav>')

    niveau1 = ('<h2 id="albums">1. Albums</h2>\n<table class="albums">\n'
               '<thead><tr><th>N°</th><th>Album</th><th>Année</th><th>Chansons</th></tr></thead>\n<tbody>\n'
               + '\n'.join(
                   f'<tr><td>{numero}</td><td><a href="#t{ancre}">{en_ligne(nom)}</a>'
                   f' <a class="page" href="{html.escape(url)}" title="Page de l\'album">page &rarr;</a></td>'
                   f'<td>{annee}</td><td>{len(chansons)}</td></tr>'
                   for ancre, numero, nom, annee, url, chansons in fiches)
               + '\n</tbody></table>')

    niveau2 = '<h2 id="chansons">2. Chansons par album</h2>\n' + '\n'.join(
        f'<h3 id="t{ancre}">{numero}) {en_ligne(nom)}' + (f' <small>({annee})</small>' if annee else '') + '</h3>\n'
        '<table class="chansons"><thead><tr><th>N°</th><th>Titre</th></tr></thead>\n<tbody>\n'
        + '\n'.join(f'<tr><td>{k}</td><td>{lien(url, a, t)}</td></tr>'
                    for k, (a, t) in enumerate(chansons, 1))
        + f'\n</tbody></table>\n{haut}'
        for ancre, numero, nom, annee, url, chansons in fiches)

    par_lettre = {}
    for ancre, numero, nom, annee, url, chansons in fiches:
        for a, t in chansons:
            par_lettre.setdefault(lettre_tri(t), []).append((cle_tri(t), t, url, a, numero))
    lettres = sorted(par_lettre)
    niveau3 = ('<h2 id="alphabet">3. Index alphabétique</h2>\n<p class="lettres">'
               + ' '.join(f'<a href="#l{l if l != "#" else "autres"}">{l}</a>' for l in lettres)
               + '</p>\n' + '\n'.join(
                   f'<h3 id="l{l if l != "#" else "autres"}">{l}</h3>\n<ul class="az-index">\n'
                   + '\n'.join(f'<li>{lien(url, a, t)} <small>(album {numero})</small></li>'
                               for _, t, url, a, numero in sorted(par_lettre[l]))
                   + '\n</ul>' for l in lettres)
               + f'\n{haut}')

    entete = (f'<div class="entete"><h1>{html.escape(titre)}</h1>'
              f'<img class="pastille" src="{favicon_uri()}" alt="" width="64" height="64"></div>')
    corps = '\n'.join([entete, navigation, niveau1, haut, niveau2, niveau3])
    destination.write_text(page(titre, corps), encoding='utf-8')


def rendre_favoris(destination, titre, accueil, anthologie):
    """Write the favourites page: an album filled in the browser with the starred songs.

    The page is static and empty; `SCRIPT_FAVORIS` fetches the anthology and copies the songs
    whose title is in the `localStorage` list.

    Args:
        destination: HTML file to write (Path).
        titre: page title, also used as heading (str).
        accueil: relative link to the index page (str).
        anthologie: URL of the anthology page, relative to `destination` (str).
    """
    contenu = (f'{fil_ariane([], accueil, False, libelle=titre)}\n'
               f'<main data-source="{html.escape(anthologie)}">\n<h1>{html.escape(titre)}</h1>\n'
               '<p id="vide">Aucun favori : cliquez sur l\'étoile à côté du titre d\'une chanson '
               '(ou touche f) pour l\'ajouter ici.</p>\n</main>')
    destination.write_text(page(titre, contenu, script=SCRIPT + SCRIPT_FAVORIS + SCRIPT_PLEIN_ECRAN + SCRIPT_NAVIGATION),
                           encoding='utf-8')
