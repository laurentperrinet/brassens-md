# brassens-md: Toutes les partitions de Brassens en fichiers markdowns


## Sources

Deux références pour comparer les accords et les paroles :

 * <http://clarckgaybeul.free.fr/brassens.htm>, un site de fan statique (« Made by Joulss », 2001) ;
 * <http://beausoleil.free.fr>, le site d'où viennent, selon ce premier site, les accords et les textes qu'il reprend. Je n'ai pas encore analysé son contenu.

Structure du premier site, pour qui voudrait comparer ou importer :

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
| `rendre.py` | Markdown to HTML renderer used by `assembler.py`: each `[Chord]` is shown above the lyrics, in a pale yellow badge (bold monospace) |
| `docs/` | generated HTML pages and `index.html` (git-ignored, **never edit by hand**) |
| `.github/workflows/pages.yml` | GitHub Actions workflow: builds `docs/` on the server and deploys it with GitHub Pages |

A song may end with a `### Notes` line followed by free comments, links or bullet items (` * ...`), up to the next `##` title. Chords are not interpreted there, and the rendered page keeps the section collapsed under the score (triangle "Notes"), and adds a "Notes ▸" link on the right of the song title that opens it. A block between two ```` ``` ```` lines is kept as is, in a monospace font (to write a tablature, spaces matter); it can also sit between two stanzas of the lyrics, where the tablature is played, and then spans the whole page width.

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
| comments | `### Notes` section, not interpreted | `{comment: ...}` or `#` lines |
| tablature | fenced block between two ```` ``` ```` lines | `{start_of_tab}` … `{end_of_tab}` |

Conversion to a strict `.pro` file only needs these headings to be turned into directives. Beausoleil's `.pro` files (see Sources) use the same inline notation, so lines can be compared or pasted both ways.

The site is built and published by the workflow at every push on `master` (or manually from the Actions tab): <https://laurentperrinet.github.io/brassens-md/>.
It needs Settings > Pages > Source set to "GitHub Actions".

```
make assemble   # sources -> construction/*.md
make compile    # also renders docs/*.html, to preview the site locally (Python 3 only, no other dependency)
make publie     # commits the songs, the build scripts and the workflow, and pushes; the server then rebuilds the site
```
