# Reader browser harness

Runs the real FirstPair Reader plugin (`main.js`, `styles.css`) in Chromium
against a built aligned vault, inside a leaf that mimics Obsidian's CSS
containment, at desktop and iPhone sizes: opens a chapter, taps a word,
closes the drawer, switches layouts, reserves the dictionary column, and
verifies the edge-to-edge page/word navigation order without overflow, and
checks that the compact translation toolbar remains one line at phone width.
It records rail, toolbar, drawer, and column geometry plus screenshots.

```sh
cp plugins/firstpair-reader/{main.js,styles.css} tests/reader-harness/
mkdir -p <vault-parent>/harness && cp tests/reader-harness/* <vault-parent>/harness/
(cd <vault-parent> && python3 -m http.server 8765)      # serves harness/ and the vault
node tests/reader-harness/run.mjs             # ?vault=/<Vault Dir Name> in the URLs
```

`shots/` is ignored. Use it whenever the drawer, layouts, or touch targets
change; the headless test DOM (`tests/support/dom.cjs`) cannot measure
layout. The harness is not part of `npm test`: it needs Playwright and its
Chromium (`npm install --no-save @playwright/test && npx playwright install
chromium`), and an aligned vault with English and Russian translations.
