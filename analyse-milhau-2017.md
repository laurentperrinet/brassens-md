# Analyse de « Brassens, une page, une chanson… » (H. Milhau, 2017-11-29)

Fichier local : `Brassens, une page, une chanson.pdf` (310 pages, non versionné). Aucune licence n'est indiquée : le texte n'est donc **pas** recopié dans le dépôt, il sert à vérifier et à compléter, comme les autres sources.

## Nature et fiabilité

* Export Word. Chaque chanson apparaît deux fois : une page en texte brut (accords sur des lignes séparées, alignés avec des espaces), puis une page en gras sur deux colonnes.
* Les accords sont donc connus **par ligne de paroles, et non par syllabe** (les positions déduites de l'alignement sont approximatives). Ne pas s'en servir pour déplacer un marqueur `[Accord]` ; Beausoleil reste la référence pour cela.
* Les longues chansons sont coupées aux sauts de page (la dernière ligne ou les deux dernières continuent sur la page suivante, par exemple Bonhomme, Le testament, Le gorille).
* Les lignes d'accords sont parfois repliées ou décalées sur la mauvaise ligne de paroles (Bécassine, Auprès de mon arbre, L'ancêtre).
* Comparaison des titres (à la main) : 8 titres du PDF manquaient dans le dépôt (section 1) ; le dépôt a 2 titres absents du PDF (Germaine Tourangelle, Jehan l'Advenu).

## 1. Chansons absentes du dépôt (8)

| Chanson | Accords vus (tonalité du PDF) | Remarques |
|---------|-------------------------------|-----------|
| Altesse (V. Hugo) | `C Am Dm G` / `F E Am` | 8 vers, presque récité |
| Il existe encore des bergères | `G D7 G E7 / Am E7 Am / D D7 / G C G` | **Capo I** (« Ton original »), intro `G D7 G E7 / Am E7 Am / D D7 / G C G` |
| Jean rentre au village | `G/g /b C/c /e`, `C7 F` | marche de basse écrite `/b`, `/e` ; 6 couplets enchaînés |
| La file indienne | `G`, `D7` | 11 couplets, un accord par refrain |
| Le bricoleur | `Em Am B7` ; refrain `Am D7 G D7 B7 Em Em6` | écho « Boîte à outils » après chaque ligne |
| Le chapeau de Mireille | `G7 C A7 Dm Am7 Dm7 B7 Em F` | intro `C G7 C C7M Am6 Ab6` |
| Le myosotis | `Cm D G7 C7 Fm Bb7 Eb Bb Bbm F` | intro `Fm/d Fm/c G7/b G7/g Cm Fm Cm` ; ligne `f eb d G7` |
| Sur la mort d'une cousine de sept ans (H. Moreau) | `C B7 C7M A5+ A7 Dm G7`, puis `Db Db7M Bb5+ Bb7 Ebm Ab7 Gb` | modulation en ré bémol au 4ᵉ quatrain, retour par `Gb Db Ebm Db C7 F G7 C` |

À noter : le dépôt contient déjà des chansons dont seul le titre diffère (par exemple « Embrasse les tous », « Gastibelza ») : rien à faire pour celles-là.

## 2. Intros, capos et notes de tonalité à ajouter aux chansons existantes

* Capo : Les casseuses (capo I), Tempête dans un bénitier (« Ton original : capo I »), L'orphelin (« ton Maxime Le Forestier – ton Bertola : capo II »), Il existe encore des bergères (capo I).
* Intros (candidates à une grille, avec la syntaxe `Grille :`) : Colombine (`C Am7 F G7 / C Am7 D7 G7 / C Am7 F G7 / C Am7 D7 G7 C` ; solo de guitare `Eb Cm7 Ab Bb7 / Eb Cm7 F7 Bb7 / Eb Cm7 Ab Bb7 / Eb G7`), Entre la rue Didot (`C A5+ Dm G7`), La mauvaise herbe (`D Bm Em A7` deux fois), Le vin (`Bm C F#7 Bm`), Les deux oncles (`D C D C C`), Les patriotes (`G7 C E7 Am G7 C E7 Am G7`), Le revenant (`A E7 A E7`), Le testament (`A A5+ F#m A5+`), Marinette (`D D#° Em7 A7` ×3), Marquise (`A A5+ D E7` ×2), Une jolie fleur (`G A B B7 E A7 D`), Les passantes (`Am G Am`), La non-demande en mariage (`Bm`).
* Colombine : le PDF est en do (`Am7`), le dépôt en si (`Am+`, `Am6`, `G7`). Vérifier la transposition et le choix `Am7` contre `Am+ / Am6` avant de rien changer.

## 3. Fragments mélodiques ou de basse (notes en minuscules, accords sur basse)

| Chanson | Fragment |
|---------|----------|
| Au bois de mon cœur | `Am Am/c D D#° E D` (chaque ligne) |
| L'amandier | fin du couplet 1 : `Bm a g f# b a g f#` |
| Pauvre Martin | `Em7 F#7 f# g# a# Bm` |
| La ballade des cimetières | `Am (e f# g#)` après les vers du refrain |
| La marguerite | `A (e f# g#)` à la fin |
| Le temps ne fait rien à l'affaire | `E E5+ A g# f# e` et `Bm E Am g f e a g f e` |
| Les passantes | fin `Am G F G A` |
| L'orphelin | tout le couplet écrit en ligne de basse : `e f# g#Am E7/b Am/c G7/d C/e ...` |
| Stances à un cambrioleur | `Am/a /c /a /c` |
| Jean rentre au village | `G/g /b C/c /e` |

Ce sont les meilleurs candidats pour les « mélodies à ajouter » (blocs de tablature entre deux strophes).

## 4. Vocabulaire d'accords à vérifier dans le rendu

Vérifier que `rendre.py` et le menu de transposition gèrent : les accords augmentés `A5+ D5+ E5+ G5+ Bb5+ E95+`, `A7/5+ C7/5+`, les accords diminués `D#° F° F#° G#° B° C#° D°`, les septièmes majeures `C7M G7M A7M Db7M`, les neuvièmes `D9 E9 B9`, les sixtes `Em6 Am6 Gm6 Bb6 F6`, les accords sur basse `Am/c`, `E7/b`, `Fm/d`, `G/g`, et les notes en minuscules `a g f#`.

## 5. Détails de structure utiles pour le markdown

* Fins de refrain différentes : Grand-père (« 1ère et 2ème fois / 3ème fois, pour finir »), Entre l'Espagne et l'Italie (la 6ᵉ fois se termine par `Bm E7 A`), Le temps ne fait rien à l'affaire (deux fins), Comme hier (« 3ème fois : la même chanson »).
* Couplets facultatifs : Chansonnette à celle qui reste pucelle (« Facultatifs »).
* Couplet instrumental : Ballade des dames du temps jadis (couplet 4, « instrumental 4 vers »).
* `bis` et passages parlés signalés dans les paroles un peu partout (L'amandier, Le roi, La nymphomane).

## Fait depuis cette analyse

1. Les huit chansons manquantes sont dans `chansons/10_chansons-inedites/` (sept d'après le ChordPro de Beausoleil, une d'après le PDF), avec le contexte dans leurs notes. Dates trouvées : La file indienne (début des années 1950, enregistrement privé en 1952), Le myosotis (Sacha Distel, 1954). Les autres dates ne sont pas établies.
2. Capos, intros et fragments de basse ont été ajoutés aux chansons concernées (voir leurs notes) ; Colombine a reçu les repères Intro / Solo / Outro et des notes de structure.
3. `accords_doigtes.py` a écrit un bloc `Accords :` dans chaque chanson (La marine garde le sien, écrit à la main). Un accord n'a pas de doigté : `DO` dans Les ricochets, qui ressemble à une faute de frappe pour `D°` dans la source.
4. `comparer_milhau.py` compare les noms d'accords chanson par chanson, après avoir trouvé le décalage en demi-tons entre le PDF et le dépôt (`comparaison-milhau-2017.md`). Méthode (comme dans Quatre-vingt quinze pour cent) : garder la tonalité du dépôt, transposer le PDF dedans, et corriger la qualité d'un accord là où le PDF est plus précis. `python3 comparer_milhau.py --appliquer` change, partout dans une chanson, une triade `X` en `X7` quand le PDF transposé ne donne que `X7` et que le dépôt ne l'a jamais (25 chansons, listées dans le rapport) ; toutes les autres différences sont seulement signalées. Résultat : 58 chansons identiques, 122 différentes. Beaucoup de différences viennent du PDF lui-même (coupures de page, lignes d'accords décalées) : vérifier à l'oreille avant de modifier une chanson.

## Reste à faire

* Passer en revue une par une les 122 chansons qui diffèrent (le rapport les liste) et décider des accords à changer.
* Les positions des notes en minuscules ajoutées dans L'amandier, Pauvre Martin, La ballade des cimetières et La marguerite sont approximatives.
* Les PDF à la racine du dépôt ne sont pas versionnés ; décider s'il faut les ignorer avec git (droits d'auteur).
