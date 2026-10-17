# brassens-md
Toutes les partitions de Brassens en un fichier markdown

1. [x] importer de la première source: http://clarckgaybeul.free.fr/brassens.htm
2. [x] trouver un format pour noter les grilles d'accord (police fixe? symboles | / ? https://github.github.com/gfm/#fenced-code-blocks ?)
4. [x] TOC http://ecotrust-canada.github.io/markdown-toc/ + fixed fonts https://github.com/mmistakes/minimal-mistakes/issues/1352#issuecomment-344571525
5. [x] export HTML
6. [x] https://github.com/music-markdown/music-markdown
3. [ ] re-jouer la totale

## Layout

| Path | Role |
|------|------|
| `songs/{album nn}/_album.md` | album header (`# 1) TITLE`) — **source** |
| `songs/{album nn}/{nn}_{slug}.md` | one song (`## TITLE`, `c1:` chord lines, `l1:` lyric lines) — **source** |
| `build.py` | assembles the sources into `build/` (git-ignored) and, with `--render`, renders HTML with `musicmd` |
| `docs/` | generated HTML and `index.md` (versioned, served by GitHub Pages) — **never edit by hand** |
| `tools/` | `strip_tags.py` (lightens the HTML), `split_albums.py` (one-off migration) |

```
make assemble   # sources -> build/*.md and docs/index.md (no Node.js needed)
make compile    # also renders docs/*.html (requires `npm i -g markdown-it-music`)
```
