# AGENTS.md

FirstPair Reader and FirstPair Triptych, two Obsidian plugins. This is a
public MIT repository; see `README.md` for what the plugins do.

## Layout

- `plugins/firstpair-reader/`, `plugins/firstpair-triptych/`: sources
  (`main-source.js`, its modules, `styles-source.css`), the release files
  (`manifest.json`, generated `main.js` and `styles.css`), and each plugin's
  README.
- `plugins/shared/`: modules both bundles embed.
- `scripts/`: `bundle-obsidian-plugin.py <plugin dir> [--check]`,
  `bundle-firstpair-triptych.py [--check]`, `release.sh`.
- `tests/`: `node:test` suites, `obsidian-mock.cjs`, and `support/` (a small
  DOM and Markdown renderer, so the tests need no packages).
- `samples/`: sample vaults, maintained separately.

## Commands

Node 20 or newer and Python 3; no `npm install`.

```sh
npm run build     # bundle main.js and styles.css for both plugins
npm test          # bundles current, node --check, every test suite
npm run release   # npm test, then each plugin's release files and hashes
```

## Rules

- `main.js` and `styles.css` are generated. Change the sources, run
  `npm run build`, and commit sources and bundles together; `npm test` fails
  on a stale bundle.
- Bump a plugin's `manifest.json` `version` for every release that changes
  its behavior or interface; a release is that plugin's `manifest.json`,
  `main.js`, and `styles.css`.
- The plugins make no network requests of their own (the optional
  transcription service a user configures is the only exception) and collect
  no telemetry.
- No private data, ever: no personal paths, names, e-mail addresses, tokens,
  private repository or book names, or copyrighted book text, in code,
  fixtures, docs, or commit messages. Test fixtures are synthetic or public
  domain.
- Add or update a test with every behavior change; DOM behavior is tested
  through the bundled `main.js`.
