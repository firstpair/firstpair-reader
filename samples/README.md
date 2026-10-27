# Sample vaults

Five small Obsidian vaults for trying FirstPair Reader and FirstPair
Triptych. Each folder below is a complete vault: open it in Obsidian with
**Open folder as vault**. Without the plugins, every vault still reads as
ordinary Markdown notes.

| Vault | Plugin | Format | Shows |
| --- | --- | --- | --- |
| `shelf/` | Reader | three `firstpair-reader.v2` books in peer folders | the shelf, aligned Chinese with pinyin and glosses, a Russian interface, a plain English book |
| `single-book/` | Reader | one aligned v2 book at the vault root | two translations into one language, interlinear layers |
| `library/` | Reader | `_data/mobile-library.json` with three editions | editions grouped by family, pages cut from Part notes |
| `code-book/` | Reader | `_data/fragments.json` beside `Chapters/` | fragment cards over a small program |
| `triptych/` | Triptych | `triptych-reader.json` (schema 4) and fenced `triptych` notes | three drafts of an essay compared pane by pane, diffs, metrics, review |

## Installing a plugin into a sample

From the repository root:

```sh
sh samples/build/install-plugins.sh samples/shelf            # FirstPair Reader
sh samples/build/install-plugins.sh samples/triptych         # FirstPair Triptych
```

The script copies the plugin's release files (`manifest.json`, `main.js`,
`styles.css`) from `plugins/<id>/` into `<vault>/.obsidian/plugins/<id>/` and
enables it in `.obsidian/community-plugins.json`. Then open the folder as a
vault, turn off Restricted mode when Obsidian asks, and open `Home.md`.

To do it by hand, make `<vault>/.obsidian/plugins/firstpair-reader/` (or
`firstpair-triptych/`), copy those three files into it, and enable the plugin
under Settings → Community plugins. `.obsidian/` and `Preferences/` (where
the plugins keep notes and decisions) are ignored by git here.

## What to try

### `shelf/`: several books in one vault

The vault has no index of its own; `Analects/`, `Diary of a Madman/`, and
`Gettysburg Address/` each hold a `_data/reader.json`. **Open the Reader**
from `Home.md` and it opens on the **shelf**, listing each book with its
author, subtitle, and language pair.

- **A Madman's Diary** (Lu Xun, 狂人日记): Chinese to English. The source is
  optional and hidden at first (`sourceLanguage.optional`,
  `defaultVisible: false`), so the book reads as English; switch on 中文 for
  a study column. Then cycle the word-layer button through Text, + Reading
  (pinyin above each word), and + Gloss (an English gloss below). The title
  is a `cover` unit and the entry number a `heading` unit.
- **Лунь юй** (论语 1.1–1.4): Chinese to Russian and English, with
  `ui_lang: "ru"`, so the Reader's interface is in Russian for this book only.
  The primary glosses are Russian (`interlinear.glossLang: "ru"`) and every
  unit adds `glosses.en`. Show English alone and the glosses follow it into
  English; use the gloss-language picker (or **Next gloss language**) to fix
  one, **Auto** to follow the columns again.
- **The Gettysburg Address**: a plain English book. One note,
  `Book/Address.md`, holds the text, and the v2 index cuts three pages out
  of it at `<!-- page:… -->` markers (`pages[].marker`).

Also try: each book keeps its own page, Back history, and languages; Up from
a book's contents returns to the shelf; opening a book's static notes
(`Home`, `Book/Contents`, a part note) opens the Reader at that place; ← and →
turn pages on a keyboard.

### `single-book/`: one aligned book

道德经 chapters 1–3 at the vault root (index paths without a folder prefix),
with the Chinese shown and two English translations: a new one and James
Legge's of 1891. Both are English, so the English column has a header to
**rotate** between them and you can add a **second English column** to read
them side by side. Legge's rhymed passages are kept as separate lines. Try
the layouts (Auto, Columns, Stacked), the interlinear layers, and a phone or
narrow window, where columns become tabs.

### `library/`: editions by family

A library index (`_data/mobile-library.json`) lists three editions of the
same chapters: the new translation and Legge's under *English translations*,
the Chinese text under *Original*. The Reader opens on the library; pick an
edition and read it. Each edition's pages are cut from its single Part note
at `<!-- lmr-page-start:… -->` / `<!-- lmr-page-end:… -->` markers. The
library's **Sources** open in the Reader's note mode: a note on the texts and
an anthology table of chapter 1 in all three.

### `code-book/`: a book about a program

`Tone Marks/` is a three-chapter book about `tone_marks.py`, a forty-line
Python program that turns `ni3 hao3` into `nǐ hǎo`. Chapters cite the code
with ` ```firstpair-fragment ` blocks; the ledger `_data/fragments.json`
gives each fragment's symbol, file, lines, and summary. Each card has **Show
code** (the numbered lines inline) and **Open file** (the code note, with
those lines marked).

### `triptych/`: three drafts compared

`The Ferry Crossing/` holds three drafts of a short essay, *The Ferry at Low
Water*, in two comparison sets: *All drafts* (three panes) and *Last
revision* (Draft 2 against the Final, a pair), each in two Parts. The drafts
differ by word choice, punctuation, dropped, added, and moved sentences, and
a closing page found only in the Final. Open `Home.md`, then the Triptych
Reader. `triptych/README.md` describes the vault in detail.

- Panes side by side with the **Rosetta rail**: bars, a 0–100 divergence
  score, and the feature vector.
- **Diff** (`_data/triptych-diffs.json`, v2): with two panes, what the earlier
  draft lost and the later gained, filtered by kind of change, moved text
  naming the page it went to; with three, words unique to a pane or shared
  with one other, and the **History** lens. **Review** shows the edit
  **rules** (recurring one-word substitutions) with Accept and Reject.
- **Metrics** (`_data/triptych-metrics.json`) as chips on each pane and under
  **Review → Ranked pages**.
- Up: fragment → part → set → contents.
- Editorial tools: **prefer this** on a pane, **Sentence & words** for
  sentence choices and Good/Bad/Edit on phrases, span notes (typed or
  voice), the **Edition** menu for one draft alone, and **Review** with the
  digest. Decisions are written to `Preferences/` in the vault.

The Reader's optional **Editing tools** (Settings → Editing tools) work in any
of the Reader vaults too.

## Sources

| Text | Edition used | Public-domain basis |
| --- | --- | --- |
| Lu Xun, 狂人日记 (*A Madman's Diary*): the preface and the first entry | first published in 新青年 (*New Youth*), 1918; simplified characters | published 1918; the author died in 1936 |
| 论语 (*Analects*), 学而 1.1–1.4 | the received text, simplified characters | ancient text |
| 道德经 (*Dao De Jing*), chapters 1–3 | the received text with Wang Bi's commentary, simplified characters | ancient text |
| James Legge, *The Texts of Taoism* (*Sacred Books of the East* 39), chapters 1–3 of the *Tao Teh King* | Oxford, 1891 | published 1891; the translator died in 1897 |
| Abraham Lincoln, the Gettysburg Address | the Bliss copy, 1864 | a nineteenth-century public document |

**Every other translation and every word gloss was written for these
samples** and is released with them under the repository's MIT licence: the
English translations of 狂人日记, 论语, and 道德经, the Russian translation of
论语, the English and Russian interlinear glosses, and the essay in the
Triptych sample. Word
splits and pinyin were generated with jieba and pypinyin (the classical texts
were split by hand) and checked by eye. `tone_marks.py` was written for the
code-book sample.

## Rebuilding and checking

```sh
uv run --with jieba --with pypinyin python samples/build/segment.py   # only after changing a Chinese text
python3 samples/build/build.py                                        # the four Reader vaults
python3 samples/build/build_triptych.py                               # the Triptych vault
node samples/check.mjs                                                # or: node samples/check.mjs samples/shelf
```

`build/` holds the generator:

- `texts.py`: the source texts, translations, and glosses (one gloss per
  word, written `a / b / c`);
- `segment.py`: word splits and pinyin into `segmented.json` (needs jieba and
  pypinyin; everything else needs only Python 3);
- `build.py`: the Reader vaults; `code_book.py` and `tone_marks.py`: the code
  book;
- `manifest.json`: the files each Reader vault was built with. A rebuild
  rewrites only changed files and removes only files an earlier build wrote,
  so `.obsidian/` and anything you add survive;
- `build_triptych.py`: the Triptych vault, and `check-triptych.mjs`, a
  detailed check of it;
- `install-plugins.sh`: the installer above.

`check.mjs` reads every vault with the Reader's own `contract.js`
(`discoverAll`, and `loadEdition` for library editions), prints each book's
format, title, pages, and parts, and opens everything the books point at:
aligned chapters (every unit has its source and translations; words spell
the source; each word has a reading and gloss; `glosses.<lang>` match the
words), marker pages, library editions, and code fragments against their
code note. The Triptych vault is checked with the Triptych plugin's own index,
payload, diff, and metrics parsers. It exits non-zero on any error. The plugins are taken
from `plugins/` in this repository (or a folder named by
`FIRSTPAIR_PLUGINS`).

## Formats without a sample

The Reader contract also reads these; they have no sample here:

- `_data/parallel-reader.json`: an aligned edition indexed on its own
  (the older form of v2's `aligned` block);
- `_data/reader.json` as a bare page array (Reader 1.x);
- `Reader/reader-index.json`, schema `firstpair.reader.v1`;
- Cicero-style `_data/reader.json` with `schema_version: 1` and inline page
  Markdown, with its Latin dictionaries and quote index;
- v2 options left out of these samples: `cover` (an image), `start_page`,
  inline `markdown` pages, `editions`, `dictionaries` and `words` (prefix-
  sharded `firstpair-reader-dictionary-v1` files for tap-a-word lookup),
  `quotes` (the reviewed quote index behind **Find the source of the selected
  quote** and source rails), and `metrics` (metric chips in the Reader).

In Triptych, the lineage, transformation, and comparison-hub notes are not
sampled.
