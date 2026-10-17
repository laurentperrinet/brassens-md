# brassens-md
Toutes les partitions de Brassens en un fichier markdown

1. [x] importer de la première source: http://clarckgaybeul.free.fr/brassens.htm
2. [x] trouver un format pour noter les grilles d'accord (police fixe? symboles | / ? https://github.github.com/gfm/#fenced-code-blocks ?)
4. [x] TOC http://ecotrust-canada.github.io/markdown-toc/ + fixed fonts https://github.com/mmistakes/minimal-mistakes/issues/1352#issuecomment-344571525
5. [x] export HTML
3. [ ] re-jouer la totale

## Layout

| Path | Role |
|------|------|
| `chansons/{nn}_{album slug}/_album.md` | album header (`# 1) TITLE`) — **source** |
| `chansons/{nn}_{album slug}/{nn}_{song slug}.md` | one song (`## TITLE`, then lyric lines with inline `[Chord]` markers, ChordPro-like) — **source** |
| `assembler.py` | assembles the sources into `construction/` (git-ignored) and, with `--rendre`, renders the HTML pages in `docs/` |
| `rendre.py` | Markdown to HTML renderer used by `assembler.py`: each `[Chord]` is shown in bold monospace, the lyrics in the normal font |
| `docs/` | generated HTML pages and `index.html` (git-ignored, **never edit by hand**) |
| `.github/workflows/pages.yml` | GitHub Actions workflow: builds `docs/` on the server and deploys it with GitHub Pages |

The site is built and published by the workflow at every push on `master` (or manually from the Actions tab): <https://laurentperrinet.github.io/brassens-md/>.
It needs Settings > Pages > Source set to "GitHub Actions".

```
make assemble   # sources -> construction/*.md
make compile    # also renders docs/*.html, to preview the site locally (Python 3 only, no other dependency)
make publie     # commits the songs, the build scripts and the workflow, and pushes; the server then rebuilds the site
```
