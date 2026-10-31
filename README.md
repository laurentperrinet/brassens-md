<img src="favicon.svg" align="right" width="96" alt="A cat in front of a guitar, smoking a pipe">

# brassens-md: Toutes les partitions de Brassens en fichiers markdowns


## TODO 

- [ ] ajouter des accords alternatifs (refrain du gorille par exemple)
- [ ] détecter les refrains et leur donner une figure de fond jaune clair
- [ ] indiquer un lien vers la source dans l’aide
- [x] délimiter les strophes (cadre bleu) et indiquer le sens de lecture (numéros dans un cercle)
- [ ] rendre les grilles d'accord et les notes des tablatures (utiliser lylipond?)
- [ ] utiliser explicitement https://github.com/ChordPro/chordpro
- [ ] ajouter un bouton pour cacher tous les accords / les redondants / n’en cacher aucun
- [ ] GitHub actions
- [x] mettre une ligne continue autour de chaque strophe, fond bleu transparent, numérotation de lecture



## Sources

Trois références pour comparer les accords et les paroles :

 * <http://beausoleil.free.fr> (« Georges Brassens, le Pornographe », Christophe, mis à jour le 11 février 2023) : **source principale**. Environ 237 transcriptions en liste alphabétique, chacune téléchargeable en Word, PDF et **ChordPro** (`download.php?fic=chordpro/{Titre}.pro`). Ce ChordPro utilise la même notation que ce dépôt (`[Dm]paroles`, accords en lettres). Le site propose aussi un forum et des pages sur la construction des accords. Aucune licence n'est indiquée.
 * <http://clarckgaybeul.free.fr/brassens.htm> : un site de fan statique (« Made by Joulss », 2001), qui reprend les accords et les textes de beausoleil. C'est un instantané ancien (177 titres, dont des titres tronqués) : tous ses titres existent chez beausoleil. Son seul apport est le classement par album.

 * « Brassens, une page, une chanson… » (Hervé Milhau, 2017-11-29), fichier local `Brassens, une page, une chanson.pdf` : recueil de 310 pages, environ 180 chansons (paroles et accords), non versionné dans ce dépôt. **Source d'origine introuvable** : seule une copie scrapée (`Brassens, une page, une chanson.doc`) circule sur [pdfcoffee.com](https://pdfcoffee.com/brassens-une-page-une-chansondoc-pdf-free.html), qui n'indique ni site d'origine ni licence. Les accords sont sur une ligne distincte, alignée aux espaces sur les paroles (positions approximatives). Il a servi à comparer les accords (`comparer_milhau.py` → `comparaison-milhau-2017.md`), à ajouter l'album « Chansons inédites » (huit chansons absentes de Beausoleil ou du dépôt), des intros, des capos et des lignes de basse. Analyse : [`analyse-milhau-2017.md`](analyse-milhau-2017.md).

La comparaison des accords avec beausoleil se fait à la demande, par Claude, sans script : les fichiers `.pro` ne sont pas recopiés dans ce dépôt. Beausoleil sert de référence pour la position des accords sur les syllabes, et chaque chanson concernée la cite dans ses `### Notes`.

Structure du site clarckgaybeul, pour qui voudrait malgré tout comparer ou importer :

 * `brassens.htm` est un index de 10 albums (les deux derniers, « Dernières chansons », sont de J. Bertola). Chaque chanson pointe vers une ancre de `{n}.htm` (`1.htm` à `10.htm`, une page par album).
 * Les pages ne sont servies qu'en HTTP simple, en `windows-1252`, et ont été écrites avec FrontPage 4.0.
 * Les accords ne sont **pas en ligne** dans le texte : chaque ligne de paroles est précédée d'une ligne distincte de noms d'accords, dans un `<font>` gris, alignée sur les paroles par des suites de `&nbsp;`. Ils sont notés en solfège français (`Rém`, `Do7`, `Sib`, `Solm`, `Fa`) et non en lettres.
 * Aucune licence n'est indiquée sur la page : son contenu ne doit pas être recopié tel quel dans ce dépôt.

## Layout

| Path | Role |
|------|------|
| `chansons/{nn}_{album slug}/_album.md` | album header (`# 1) TITLE`) — **source** |
| `chansons/{nn}_{album slug}/{nn}_{song slug}.md` | one song (`## TITLE`, then lyric lines with inline `[Chord]` markers, ChordPro-like) — **source** |
| `assembler.py` | assembles the sources into `construction/` (git-ignored) and, with `--rendre`, renders the HTML pages in `docs/` |
| `rendre.py` | Markdown to HTML renderer used by `assembler.py`: each `[Chord]` is shown above the lyrics, in an amber badge with a thin outline (bold monospace; one palette for the light mode, one for the dark mode, both readable on the blue stanza cards); each stanza is a card (continuous blue outline, translucent blue background, rounded corners) numbered in a disc at its top-left corner (italic Palatino); the number of columns is computed in the browser (largest count, up to 6, in which no sung line wraps, balanced so that no stanza is alone on the last row; recomputed when the window, text size or full screen change), the count restarting at every song, which shows the reading order (left to right, then top to bottom); a chord grid is a card of its own, unnumbered, in first position of its place in the flow; the settings menu (⚙) holds full screen, theme, text size, **compact mode** ("Paroles seules": hides the chords above the lyrics of the stanzas and tightens the lines; the grids keep theirs; remembered in the browser) and transposition; the `Accords :` block of a song is drawn as a row of diagrams after the lyrics |
| `chansons/10_chansons-inedites/` | album « Chansons inédites » : chansons de Brassens absentes des albums officiels (chansons pour les autres, poèmes mis en musique) |
| `accords_doigtes.py` | écrit en tête de chaque chanson le bloc `Accords :` (doigtés calculés, `python3 accords_doigtes.py`) ; ne touche pas aux blocs déjà présents |
| `diagrammes_accords.py` | draws one SVG chord diagram per (chord, fingering) written in the `Accords :` blocks, into `accords/` (`make diagrammes`) |
| `accords/{chord}_{fingering}.svg` | chord diagrams (`Dm_xx0231.svg`, `Dm_x57765.svg`: one file per variant, `#` is spelled `dies`, `/` is `_sur_`) — generated, but **versioned**: the site copies them to `docs/accords/` |
| `comparer_milhau.py` | compare les accords du PDF de Milhau aux chansons (nécessite `gs`), écrit `comparaison-milhau-2017.md` |
| `favicon.svg` | site icon (a cat in front of a guitar), inlined by `rendre.py` as a data URI in every page — **source** |
| `docs/` | generated HTML pages and `index.html` (git-ignored, **never edit by hand**) |
| `.github/workflows/pages.yml` | GitHub Actions workflow: builds `docs/` on the server and deploys it with GitHub Pages |

A song may end with a `### Notes` line followed by free comments, links or bullet items (` * ...`), up to the next `##` title. Chords are not interpreted there, and the rendered page keeps the section collapsed under the score (triangle "Notes"), and adds a "Notes ▸" link on the right of the song title that opens it. A block between two ```` ``` ```` lines is kept as is, in a monospace font (to write a tablature, spaces matter); it can also sit between two stanzas of the lyrics, where the tablature is played, and then spans the whole page width.

Vidéo d'apprentissage : un en-tête (front matter) `youTubeId` placé entre deux lignes `---`, juste sous le titre, intègre dans la page le lecteur YouTube de la vidéo, avec un lien de secours si l'intégration est refusée. On y met de préférence le tuto de la chaîne [Brassens à la guitare](https://www.youtube.com/@Brassensàlaguitare), et les autres versions vont en puces dans les `### Notes`.

```markdown
## La marine

---
youTubeId: 7m2njJXYabA
---
```

Favourites: every song title in the HTML pages has a star (or press `f` for the song under the top bar). The list is stored in the browser (`localStorage`, one list per browser and device, no synchronisation) and shown as the "Favoris" album on `docs/favoris.html`, which is filled in from the anthology page when it loads. It therefore needs the site to be served over http(s); opened as a `file://` page, it only shows a message.

```markdown
### Notes

 * Tablature : https://tabs.ultimate-guitar.com/tab/georges-brassens/la-marine-chords-2504772
```

## Song format (ChordPro subset)

[ChordPro](https://www.chordpro.org) is a plain-text format where a chord name in square brackets is written inline, right before the syllable on which it is played: `La femme qui pos[G]sède` puts `G` on "sède". The lyric lines of this repository are valid ChordPro as they stand (several chords per line, chords inside a word, suffixes such as `B7`, `Am`, `E7`).

The files are however **not strict `.pro` files**: they are Markdown with ChordPro lyric lines.

| Element | Here | Strict ChordPro |
|---------|------|-----------------|
| title | `## TITLE` | `{title: TITLE}` |
| chord | `[Am]` inline, in English letters (`Dm`, `Bb`, `E7`) | same |
| chorus | plain text such as `Refrain :`, repeated by a bare `Refrain` | `{start_of_chorus}` … `{end_of_chorus}` |
| chord grid | `Grille : \|: Dm . . \| A7 . . :\|`, or a line starting with `\|` | `{start_of_grid}` … `{end_of_grid}` |
| comments | `### Notes` section, not interpreted | `{comment: ...}` or `#` lines |
| tablature | fenced block between two ```` ``` ```` lines | `{start_of_tab}` … `{end_of_tab}` |
| recurring tablature | `Interlude :` followed by the fenced block, then a bare `Interlude` wherever it is played again | `{start_of_tab}` … `{end_of_tab}`, repeated |

### Chords with a fingering, capo, lowercase notes

 * `Accords :` followed by ` * Dm : xx0231` lines gives the fingerings (6th to 1st string, `x` = muted). The chord names are shown as chords and follow the transposition menu; the fingerings are hidden when transposed, since they only suit the original key.
 * ` * Capo 1` under the title gives the capo of the original key.
 * A ChordPro annotation `[*2 mesures]` is shown above the lyrics as a grey remark, without being a chord (it does not follow the transposition menu).
 * A single bass or melody note is written in lowercase, `[a] [g] [f#]` or `[eb]`; a slash chord may carry a lowercase bass (`Am/c`) or no root at all (`/b`). Transposition keeps them lowercase. Other symbols handled by the transposition: `A5+`, `D#°` or `D#dim`, `C7M`, `E95+`, `A7/5+`.

### Chord grids and bar lines

Inline `[Chord]` markers carry no notion of time. Where the bars matter (an introduction, a bridge, an instrumental), write a chord grid with the ChordPro 6 grid symbols, on a line of its own:

```
Grille :

|: Dm . | C . | Bb7 A7 | Dm . :|
| D7 . | Gm . | C7 . | F . |.
```

| Symbol | Meaning |
|--------|---------|
| `\|` | bar line |
| `\|:` and `:\|` | start and end of a repeat |
| `\|\|` | double bar line |
| `\|.` | final bar line |
| `.` | the previous chord goes on for one beat |
| `%` | repeat the previous bar |
| `~` | two chords on the same beat (`C~G`) |

A grid is recognised in the lyrics when a line starts with `Grille :` (like `Refrain :`) or with a bar line `|` and holds no `[Chord]`. Consecutive rows form one block: the rendered page shows a card of its own, the same size as a stanza and unnumbered, with a green "Grille" badge, then one box per bar, so the bars line up from row to row. A chord followed by `.` lasts one more beat (`Dm . .` is one chord of three beats), several chords in a bar share its beats, and the repeat, double and final bar lines are drawn as such. The chords are clickable like those of the lyrics: they follow the transposition menu. Text after the last bar of a row is shown as a margin note. A tablature stays in a fenced block, where its own `|` are left alone.

Conversion to a strict `.pro` file only needs these headings to be turned into directives (a grid goes between `{start_of_grid}` and `{end_of_grid}`). Beausoleil's `.pro` files (see Sources) use the same inline notation, so lines can be compared or pasted both ways.

## ChordPro reference

Summary of the [ChordPro](https://www.chordpro.org/chordpro/) notation (version 6), as a reminder for writing or converting songs. The last column tells what this repository does with each element. Full specification: <https://www.chordpro.org/chordpro/chordpro-directives/>.

### Lyrics and chords

| Notation | Meaning | Here |
|----------|---------|------|
| `La femme qui pos[G]sède` | chord `G` played on the syllable that follows | same |
| `[Am]` alone at the end of a line | chord with no lyric under it (instrumental) | same |
| `[Am/G]`, `[C7M]`, `[D#dim]`, `[A7/5+]` | slash chord, extension, alteration | same; transposed |
| `[*texte]` | annotation: a remark above the lyrics, not a chord | shown in grey, not transposed |
| `[a]`, `[eb]` | single note (bass or melody), lowercase | same; transposed, kept lowercase |
| `# comment` | comment line, ignored | not used (use `### Notes`) |
| blank line | separates two blocks (verses) | same: a stanza is a card, the numbering follows the blocks |

### Directives

A directive is a line `{name}` or `{name: value}`. Most have a short form.

| Directive (short) | Meaning | Here |
|-------------------|---------|------|
| `{title: T}` (`{t:}`) | title | `## T` |
| `{subtitle: S}` (`{st:}`) | subtitle, e.g. the author | not used |
| `{artist: A}`, `{composer: C}`, `{lyricist: L}`, `{album: A}`, `{year: Y}` | metadata | album = folder; the rest is not used |
| `{key: Am}` | key of the song | not used (the transposition menu changes the key) |
| `{capo: 2}` | capo position | ` * Capo 2` under the title |
| `{tempo: 120}`, `{time: 4/4}`, `{duration: 3:20}` | tempo, time signature, duration | not used |
| `{comment: text}` (`{c:}`), `{comment_italic:}` (`{ci:}`), `{comment_box:}` (`{cb:}`) | text shown to the singer | `### Notes` section |
| `{define: Am base-fret 1 frets x 0 2 2 1 0}` | chord fingering | ` * Am : x02210` under `Accords :` |
| `{chord: Am}` | chord shown in the text | not used |
| `{transpose: 2}` | transposes all the chords of the song | menu "Transposer" in the page |
| `{new_song}` (`{ns}`) | starts a new song in the same file | one file per song |
| `{new_page}`, `{column_break}` (`{colb}`), `{columns: 2}` (`{col:}`) | page layout | columns are computed by the browser |
| `{meta: name value}`, `{youtube: id}` | free metadata | front matter `youTubeId` between `---` |

### Sections

A section is a block between a start and an end directive; a section can be given a label with `: label`.

| Section | Short | Here |
|---------|-------|------|
| `{start_of_verse}` … `{end_of_verse}` | `{sov}` `{eov}` | a block of lyric lines, i.e. a stanza |
| `{start_of_chorus}` … `{end_of_chorus}` | `{soc}` `{eoc}` | `Refrain :`, repeated by a bare `Refrain` |
| `{chorus}` | plays the chorus again | bare `Refrain` |
| `{start_of_bridge}` … `{end_of_bridge}` | `{sob}` `{eob}` | `Pont :` |
| `{start_of_tab}` … `{end_of_tab}` | `{sot}` `{eot}` | fenced block between two ```` ``` ```` lines |
| `{start_of_grid}` … `{end_of_grid}` | `{sog}` `{eog}` | `Grille :` then rows starting with `\|` |
| `{start_of_abc}`, `{start_of_ly}`, `{start_of_svg}`, `{start_of_textblock}` | embedded ABC, Lilypond, SVG, text | not used |
| `{start_of_X: label}` | any other name `X` is a custom section | `Intro :`, `Interlude :`, `Solo :`, `Coda :`, `Final :` |

### Grids (ChordPro 6)

Inside a grid section, each row is made of bars separated by `|`. `|:` and `:|` open and close a repeat, `||` is a double bar, `|.` the final bar. A `.` extends the previous chord by one beat, `%` repeats the previous bar, `~` puts two chords on one beat (`C~G`). The first and last cells may hold text: a margin note before and after the bars. See "Chord grids and bar lines" above for the rendering.

### Formatting directives (not used here)

`{textfont: ...}`, `{textsize: ...}`, `{textcolour: ...}` and the same with `chord`, `chorus`, `tab`, `title`, `footer`, `toc`, `grid`, `diagram` … set fonts, sizes and colours; `{image: src=... width=...}` inserts a picture; `{diagrams: off}` hides the chord diagrams; `{pagetype: a4}`, `{titles: left}`, `{footer: ...}`, `{header: ...}` and `{pagecontrol: ...}` set the page. The site chooses its own fonts and colours (light and dark themes), so these are ignored.

### Conditionals and chord names (not used here)

A directive can be restricted by a selector suffix, `{define-guitar: ...}` or `{comment-ukulele: ...}`, or by `{name-instrument}`; `{define: ... diagram off}` hides a diagram. Chord names are written in letters (`C D E F G A B`, `#` or `b`, then `m`, `7`, `maj7`, `sus4`, `dim`, `aug` …); solfège (`Do Ré Mi`) or Roman/Nashville notations need `{chord-notation: ...}` in a strict ChordPro file, which is why the sources here use letters only.

The site is built and published by the workflow at every push on `master` (or manually from the Actions tab): <https://laurentperrinet.github.io/brassens-md/>.
It needs Settings > Pages > Source set to "GitHub Actions".

```
make assemble   # sources -> construction/*.md
make compile    # also renders docs/*.html, to preview the site locally (Python 3 only, no other dependency)
make publie     # commits the songs, the build scripts and the workflow, and pushes; the server then rebuilds the site
```
