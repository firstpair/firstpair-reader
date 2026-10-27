#!/usr/bin/env node
// Check a FirstPair Triptych vault against the plugin's own parsers.
//
//   node samples/build/check-triptych.mjs [vaultDir] [pluginDir]
//
// vaultDir defaults to ../triptych beside this script; pluginDir to
// ../../plugins/firstpair-triptych (the folder holding main.js or
// main-source.js, with ../shared beside it).  The plugin is loaded under a
// stub `obsidian` module, as the plugin's tests load it, and its exported
// test hooks parse the Reader index, every fenced payload, the metrics, and
// the diffs.  Exits non-zero on any error.

import { createHash } from "node:crypto";
import fs from "node:fs";
import Module, { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_VAULT = path.resolve(HERE, "../triptych");
const DEFAULT_PLUGIN = path.resolve(HERE, "../../plugins/firstpair-triptych");
const FALLBACK_PLUGIN = path.join(os.homedir(), "src/firstpair/publishing/vault/plugin/firstpair-triptych");

function obsidianStub() {
  class Stub {}
  return {
    ItemView: Stub,
    Plugin: Stub,
    PluginSettingTab: Stub,
    Setting: Stub,
    Notice: Stub,
    Platform: { isMobile: false, isDesktop: true },
    normalizePath: (value) => String(value).replace(/\\/g, "/").replace(/\/+/g, "/").replace(/^\/|\/$/g, ""),
    requestUrl: async () => { throw new Error("no network in check-triptych"); },
    setIcon: () => {},
  };
}

function resolvePluginDir(pluginDir) {
  if (pluginDir) return path.resolve(pluginDir);
  return fs.existsSync(path.join(DEFAULT_PLUGIN, "main.js")) ? DEFAULT_PLUGIN : FALLBACK_PLUGIN;
}

function loadPlugin(pluginDir) {
  const entry = ["main.js", "main-source.js"]
    .map((name) => path.join(pluginDir, name))
    .find((file) => fs.existsSync(file));
  if (!entry) throw new Error(`no main.js or main-source.js in ${pluginDir}`);
  const originalLoad = Module._load;
  Module._load = function load(request, parent, isMain) {
    if (request === "obsidian") return obsidianStub();
    return originalLoad.call(this, request, parent, isMain);
  };
  try {
    delete require.cache[entry];
    const PluginClass = require(entry);
    if (!PluginClass || !PluginClass.__test) throw new Error(`${entry} exports no __test hooks`);
    const reviewState = path.join(pluginDir, "review-state.js");
    return {
      entry,
      hooks: PluginClass.__test,
      reviewState: fs.existsSync(reviewState) ? require(reviewState) : null,
    };
  } finally {
    Module._load = originalLoad;
  }
}

// The vault adapter surface detectBookRoot uses, over the file system.
function fsAdapter(vaultDir) {
  const full = (relative) => path.join(vaultDir, relative);
  return {
    exists: async (relative) => fs.existsSync(full(relative)),
    read: async (relative) => fs.readFileSync(full(relative), "utf8"),
    list: async (relative) => {
      const entries = fs.readdirSync(full(relative), { withFileTypes: true });
      return {
        folders: entries.filter((e) => e.isDirectory()).map((e) => e.name),
        files: entries.filter((e) => e.isFile()).map((e) => e.name),
      };
    },
  };
}

function frontmatter(raw) {
  const match = raw.match(/^---\n([\s\S]*?)\n---\n/);
  const fields = {};
  if (!match) return fields;
  for (const line of match[1].split("\n")) {
    const field = line.match(/^([A-Za-z_]+):\s*(.*)$/);
    if (field) fields[field[1]] = field[2].replace(/^"(.*)"$/, "$1");
  }
  return fields;
}

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

const sha256Id = (text) => `sha256:${createHash("sha256").update(text, "utf8").digest("hex")}`;
const codePoints = (text) => Array.from(text).length;

export async function checkTriptych(vaultDir = DEFAULT_VAULT, pluginDir) {
  vaultDir = path.resolve(vaultDir);
  pluginDir = resolvePluginDir(pluginDir);
  const errors = [];
  const fail = (message) => errors.push(message);
  const summary = { vault: vaultDir, plugin: null };
  let plugin;
  try {
    plugin = loadPlugin(pluginDir);
    summary.plugin = plugin.entry;
  } catch (error) {
    fail(`plugin: ${error.message}`);
    return { ok: false, errors, summary };
  }
  const T = plugin.hooks;
  const exists = (relative) => fs.existsSync(path.join(vaultDir, relative));
  const read = (relative) => fs.readFileSync(path.join(vaultDir, relative), "utf8");

  if (exists(".obsidian/plugins")) fail(".obsidian/plugins must not ship in the sample vault");

  // 1. The book folder, found as the plugin finds it.
  const root = await T.detectBookRoot(fsAdapter(vaultDir));
  summary.bookRoot = root;
  const indexPath = `${root}/_data/triptych-reader.json`;
  if (!exists(indexPath)) {
    fail(`detectBookRoot chose "${root}", which has no _data/triptych-reader.json`);
    return { ok: false, errors, summary };
  }

  // 2. The Reader index.
  let reader;
  try {
    reader = T.parseTriptychReaderIndex(read(indexPath));
  } catch (error) {
    fail(`${indexPath}: ${error.message}`);
    return { ok: false, errors, summary };
  }
  summary.title = reader.title;
  summary.editions = reader.editions.map((e) => e.id);
  summary.canonical = reader.editions.find(
    (e) => e.version === reader.book_version && e.source_commit === reader.source_commit,
  ).id;
  summary.sets = reader.sets.map((set) => ({
    id: set.id,
    title: set.title,
    editions: set.edition_ids,
    parts: set.parts.map((part) => `${part.heading} (${set.pages.filter((p) => p.part_id === part.id).length})`),
    pages: set.pages.length,
  }));
  summary.pages = reader.sets.reduce((sum, set) => sum + set.pages.length, 0);

  const noteType = (note, expected, extra = {}) => {
    const file = `${note}.md`;
    if (!exists(file)) return fail(`missing note ${file}`);
    const fields = frontmatter(read(file));
    if (fields.type !== expected) fail(`${file}: type is "${fields.type}", expected "${expected}"`);
    for (const [key, value] of Object.entries(extra)) {
      if (fields[key] !== value) fail(`${file}: ${key} is "${fields[key]}", expected "${value}"`);
    }
  };
  noteType(reader.launcher, "triptych-reader-launcher");
  noteType(reader.contents, "triptych-reader-contents");
  noteType(reader.review, "triptych-review-launcher");
  for (const note of [reader.launcher, reader.contents, reader.review]) {
    if (!note.startsWith(`${root}/Triptychs/`)) fail(`${note} lies outside ${root}/Triptychs`);
  }
  if (exists("Home.md") && !read("Home.md").includes(`[[${reader.launcher}|Open the Triptych Reader]]`)) {
    fail("Home.md has no Open the Triptych Reader route");
  }

  // 3. Every page: payload, identity, digest, and the unit links it carries.
  const panesByKey = new Map();
  const digests = [];
  for (const set of reader.sets) {
    noteType(set.note, "triptych-hub", { set: set.id });
    for (const page of set.pages) {
      const file = `${page.note}.md`;
      if (!exists(file)) {
        fail(`missing page ${file}`);
        continue;
      }
      const raw = read(file);
      const fields = frontmatter(raw);
      if (fields.type !== "triptych" || fields.triptych_key !== page.key) {
        fail(`${file}: frontmatter does not name ${page.key}`);
      }
      let payload;
      try {
        payload = T.extractTriptychPayload(raw);
        T.validateIndexedTriptychPayload(payload, file, reader);
      } catch (error) {
        fail(`${file}: ${error.message}`);
        continue;
      }
      const digest = T.editorialPageDigest(payload);
      if (digest !== page.target_digest) fail(`${file}: target_digest ${page.target_digest} != ${digest}`);
      digests.push([page.key, digest]);
      panesByKey.set(page.key, new Map(payload.panes.map((pane) => [pane.edition, pane])));
      for (const pane of payload.panes) {
        for (const link of pane.notes) {
          const [target, anchor = ""] = link.split("#");
          if (!exists(`${target}.md`)) {
            fail(`${file}: unit note ${target} is missing`);
            continue;
          }
          const body = read(`${target}.md`);
          const found = anchor.startsWith("^")
            ? body.includes(` ${anchor}\n`)
            : !anchor || body.split("\n").some((line) => line.replace(/^#+\s+/, "") === anchor && line.startsWith("#"));
          if (!found) fail(`${file}: unit link ${link} does not resolve`);
        }
        const review = payload.review && payload.review.panes ? payload.review.panes[pane.edition] : null;
        if (pane.text && payload.review && !review) fail(`${file}: no review rail for ${pane.edition}`);
      }
    }
  }

  summary.validPages = panesByKey.size;

  // The index's source_content_id binds exactly these pages.
  const contentId = sha256Id(stableJson({
    pages: [...digests].sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0)),
    project_id: reader.project_id,
    target_contract_version: reader.target_contract_version,
  }));
  if (contentId !== reader.source_content_id) {
    fail(`source_content_id ${reader.source_content_id} does not bind the pages (${contentId})`);
  }

  // 4. Edition ledger and the interface language it implies.
  const ledgerPath = `${root}/_data/editions.jsonl`;
  if (!exists(ledgerPath)) {
    fail(`missing ${ledgerPath}`);
  } else {
    const jsonl = read(ledgerPath);
    const rows = jsonl.split("\n").filter((line) => line.trim()).map((line) => JSON.parse(line));
    const canonical = rows.filter((row) => row.canonical === true);
    if (canonical.length !== 1) fail(`${ledgerPath}: expected one canonical edition, found ${canonical.length}`);
    else if (canonical[0].id !== summary.canonical) {
      fail(`${ledgerPath}: canonical ${canonical[0].id} is not the index's ${summary.canonical}`);
    }
    for (const edition of reader.editions) {
      const row = rows.find((item) => item.id === edition.id);
      if (!row) fail(`${ledgerPath}: no row for ${edition.id}`);
      else if (row.version !== edition.version || row.commit !== edition.source_commit) {
        fail(`${ledgerPath}: ${edition.id} disagrees with the Reader index`);
      }
    }
    const jsonPath = `${root}/_data/editions.json`;
    if (exists(jsonPath) && JSON.stringify(JSON.parse(read(jsonPath))) !== JSON.stringify(rows)) {
      fail(`${jsonPath} differs from editions.jsonl`);
    }
    summary.language = plugin.reviewState && plugin.reviewState.pickUiLanguage
      ? plugin.reviewState.pickUiLanguage(jsonl)
      : (canonical[0] && canonical[0].lang) || "en";
  }

  // 5. Metrics.
  const metricsPath = `${root}/_data/triptych-metrics.json`;
  if (exists(metricsPath)) {
    try {
      const metrics = T.parseMetrics(read(metricsPath));
      const keys = new Set(metrics.metrics.map((metric) => metric.key));
      for (const [pageKey, byEdition] of Object.entries(metrics.values)) {
        if (!reader.pageByKey.has(pageKey)) fail(`${metricsPath}: unknown page ${pageKey}`);
        for (const [edition, values] of Object.entries(byEdition)) {
          if (!reader.editionById.has(edition)) fail(`${metricsPath}: unknown edition ${edition}`);
          for (const [key, value] of Object.entries(values)) {
            if (!keys.has(key) || !Number.isFinite(value)) fail(`${metricsPath}: bad value ${pageKey} ${edition} ${key}`);
          }
        }
      }
      summary.metrics = metrics.metrics.map((metric) => metric.key);
    } catch (error) {
      fail(`${metricsPath}: ${error.message}`);
    }
  }

  // 6. Diffs: every range inside its pane, every page and target known.
  const diffsPath = `${root}/_data/triptych-diffs.json`;
  if (exists(diffsPath)) {
    try {
      const diffs = T.diffView.parseDiffs(read(diffsPath));
      const raw = JSON.parse(read(diffsPath));
      for (const edition of diffs.editions) {
        if (!reader.editionById.has(edition)) fail(`${diffsPath}: unknown edition ${edition}`);
      }
      let ranges = 0;
      for (const [pageKey, entry] of Object.entries(diffs.pages)) {
        const panes = panesByKey.get(pageKey);
        if (!panes) {
          // A page whose payload already failed is not reported twice.
          if (!reader.pageByKey.has(pageKey)) fail(`${diffsPath}: unknown page ${pageKey}`);
          continue;
        }
        for (const [combo, byEdition] of Object.entries(entry)) {
          const members = combo.split("|");
          if (members.some((edition) => !panes.has(edition))) fail(`${diffsPath}: ${pageKey} ${combo} names an edition not on the page`);
          for (const [edition, list] of Object.entries(byEdition)) {
            const pane = panes.get(edition);
            if (!pane || !members.includes(edition)) {
              fail(`${diffsPath}: ${pageKey} ${combo} has ranges for ${edition}`);
              continue;
            }
            const length = codePoints(pane.text);
            for (const range of list) {
              ranges += 1;
              const [from, to, kind, category, target] = range;
              if (!(Number.isInteger(from) && Number.isInteger(to) && from >= 0 && from < to && to <= length)) {
                fail(`${diffsPath}: ${pageKey} ${combo} ${edition} range ${from}-${to} outside its pane`);
              }
              if (T.diffView.visibleRanges([range]).length !== 1) fail(`${diffsPath}: ${pageKey} bad kind ${kind}`);
              if (category && !T.diffView.CATEGORIES.includes(category)) fail(`${diffsPath}: ${pageKey} bad category ${category}`);
              if (category === "moved" && !reader.pageByKey.has(target)) fail(`${diffsPath}: ${pageKey} moved to unknown ${target}`);
            }
          }
        }
      }
      let rules = 0;
      for (const [pair, list] of Object.entries(diffs.rules)) {
        for (const rule of list) {
          rules += 1;
          for (const [pageKey] of rule.occurrences) {
            if (!reader.pageByKey.has(pageKey)) fail(`${diffsPath}: rule ${rule.id} names unknown page ${pageKey}`);
          }
        }
        if (!T.diffView.pairKeys(diffs).includes(pair)) fail(`${diffsPath}: rules for unknown pair ${pair}`);
      }
      const partIds = new Set(reader.sets.flatMap((set) => set.parts.map((part) => part.id)));
      for (const [pair, byPart] of Object.entries(diffs.summary)) {
        for (const partId of Object.keys(byPart)) {
          if (!partIds.has(partId)) fail(`${diffsPath}: summary ${pair} names unknown part ${partId}`);
        }
      }
      summary.diffs = { schema: raw.schema, pages: Object.keys(diffs.pages).length, ranges, rules };
    } catch (error) {
      fail(`${diffsPath}: ${error.message}`);
    }
  }

  return { ok: errors.length === 0, errors, summary };
}

function printSummary({ ok, errors, summary }) {
  const lines = [
    `vault    ${summary.vault}`,
    `plugin   ${summary.plugin}`,
  ];
  if (summary.title) {
    lines.push(
      `book     ${summary.bookRoot} — "${summary.title}" (ui ${summary.language || "?"})`,
      `editions ${summary.editions.join(", ")} (canonical ${summary.canonical})`,
    );
    for (const set of summary.sets) {
      lines.push(`set      ${set.id} "${set.title}": ${set.editions.join(" | ")}; ${set.pages} pages; ${set.parts.join(", ")}`);
    }
    lines.push(`pages    ${summary.validPages} of ${summary.pages} payloads valid and bound to their target_digest`);
    if (summary.metrics) lines.push(`metrics  ${summary.metrics.join(", ")}`);
    if (summary.diffs) {
      lines.push(`diffs    ${summary.diffs.schema}: ${summary.diffs.pages} pages, ${summary.diffs.ranges} ranges, ${summary.diffs.rules} rules`);
    }
  }
  for (const error of errors) lines.push(`ERROR    ${error}`);
  lines.push(ok ? "ok" : `FAILED (${errors.length} errors)`);
  console.log(lines.join("\n"));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = await checkTriptych(process.argv[2] || DEFAULT_VAULT, process.argv[3]);
  printSummary(result);
  process.exitCode = result.ok ? 0 : 1;
}
