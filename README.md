# FirstPair Reader

Two [Obsidian](https://obsidian.md) community plugins for reading and reviewing
books kept as vaults, on desktop and on phones:

- **FirstPair Reader** (`plugins/firstpair-reader`, id `firstpair-reader`) is
  an offline book reader. It finds the vault's reading-order indexes and opens
  them in one dedicated view, with one navigation rail (Previous, Up, Back,
  Forward, Top, TOC, Next), a contents view, and a shelf when the vault holds
  several books. Aligned editions show the source and its translations side by
  side or stacked, with dictionaries, interlinear word layers, and phone
  tabs. Footnotes and links stay inside the Reader. It makes no network
  requests and writes nothing unless you switch on its optional span notes.
  With the plugin disabled, the vault's Markdown notes remain a complete book.
- **FirstPair Triptych** (`plugins/firstpair-triptych`, id
  `firstpair-triptych`) is an editorial reader for comparing editions or
  translations of one text side by side: pinned navigation, sentence and word
  choices, proposed edits, span notes and voice notes, and a durable,
  source-bound decision ledger with a Markdown digest for a later editorial
  pass.

Both are plain JavaScript, bundled into a single `main.js` each, with no
runtime dependencies beyond Obsidian itself.

## What the Reader reads

The Reader discovers its indexes at the vault root and in each top-level
folder (one book per folder; paths in an index are vault-relative):

- `_data/reader.json` with schema `firstpair-reader.v2`: parts and pages, each
  page a Markdown note or an aligned chapter, plus optional `aligned`,
  `ui_lang`, `author`, `subtitle`, and cover;
- `_data/parallel-reader.json` (`firstpair-parallel-reader-v1`): an aligned
  edition whose pages are `firstpair-aligned-chapter-v1` JSON files of units
  with `source` lines, `translations` by language, and optional `words`
  (`[text, reading, gloss]`) and `glosses`;
- dictionaries `firstpair-reader-dictionary-v1`, or a sharded
  `firstpair-reader-dictionary-index-v1`;
- older layouts: 1.x page lists, schema-1 `reader.json` files with inline page
  Markdown, `Reader/reader-index.json`, mobile edition libraries, and code
  books (`_data/fragments.json` beside a `Chapters/` folder).

[`plugins/firstpair-reader/README.md`](plugins/firstpair-reader/README.md)
describes the reading features and settings,
[`plugins/firstpair-reader/FEATURES.md`](plugins/firstpair-reader/FEATURES.md)
maps every feature against the readers this one replaced, and
[`plugins/firstpair-reader/contract.js`](plugins/firstpair-reader/contract.js)
is the authoritative parser and validator for every format. The Triptych's
vault layout is in
[`plugins/firstpair-triptych/README.md`](plugins/firstpair-triptych/README.md).

## Layout

```text
plugins/firstpair-reader/    Reader sources (main-source.js and modules,
                             styles-source.css) and its release files
plugins/firstpair-triptych/  Triptych sources and release files
plugins/shared/              modules both plugins embed (history, page keys,
                             span editor, ledger store, voice notes, metrics,
                             edition diffs)
scripts/                     bundlers and the release helper
tests/                       node:test suites, a small headless DOM and
                             Markdown renderer for them, opt-in QA tools
samples/                     sample vaults (see samples/README.md)
```

## Build

Requirements: Node.js 20 or newer and Python 3. There is nothing to install.

Edit `main-source.js`, its modules, `../shared/*.js`, or `styles-source.css`;
never edit `main.js` or `styles.css` by hand. Then bundle:

```sh
npm run build
# or one plugin at a time
python3 scripts/bundle-obsidian-plugin.py plugins/firstpair-reader
python3 scripts/bundle-firstpair-triptych.py
```

The bundler embeds every relative module a plugin reaches into one
deterministic `main.js` (Obsidian on iOS cannot resolve relative `require`),
records each source's SHA-256 in its header, and expands `@import`s of
`styles-source.css` into `styles.css`.

## Test

```sh
npm test
```

This checks that both bundles and stylesheets are current (`--check`), runs
`node --check` on both `main.js` files, and runs every suite under `tests/`
with `node --test`. The DOM suites open the real bundled plugins against
temporary fixture vaults, using a mocked `obsidian` module
(`tests/obsidian-mock.cjs`) and a small dependency-free DOM and Markdown
renderer (`tests/support/`).

Two opt-in tools are not part of `npm test`:

- `npm run qa:vaults -- <vault> [<vault> ...]` opens the Reader against real
  vaults on disk (read only) and prints a JSON report;
- `tests/reader-harness/` runs the Reader in Chromium at desktop and phone
  sizes for layout checks; it needs Playwright (see its README).

## Install into a vault

Each plugin installs as three files in the vault's
`.obsidian/plugins/<plugin id>/` folder:

| Plugin | Copy these files | Into |
| --- | --- | --- |
| FirstPair Reader | `plugins/firstpair-reader/manifest.json`, `main.js`, `styles.css` | `.obsidian/plugins/firstpair-reader/` |
| FirstPair Triptych | `plugins/firstpair-triptych/manifest.json`, `main.js`, `styles.css` | `.obsidian/plugins/firstpair-triptych/` |

```sh
mkdir -p "<vault>/.obsidian/plugins/firstpair-reader"
cp plugins/firstpair-reader/{manifest.json,main.js,styles.css} "<vault>/.obsidian/plugins/firstpair-reader/"
```

The plugin's `README.md` may be copied alongside. Then enable the plugin under
Settings → Community plugins. Keep the vault's own
`.obsidian/plugins/<id>/data.json`: it holds the reader's settings and places.
`npm run release` runs the checks and lists each plugin's release files with
their SHA-256.

## Samples

Small sample vaults for trying the plugins are described in
[`samples/README.md`](samples/README.md).

## Provenance and license

This code was extracted from the FirstPair publishing repository
(`firstpair/firstpair`) at commit `fa5c705`, without its history; this
repository is now its canonical home. The test fixtures are synthetic or
public-domain text.

Released under the MIT License; see [`LICENSE`](LICENSE).
