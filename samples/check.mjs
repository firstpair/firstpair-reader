#!/usr/bin/env node
// Check the sample vaults with the plugins' own loaders.
//
//   node samples/check.mjs                 every sample vault
//   node samples/check.mjs samples/shelf   one (or several) vaults
//
// Reader vaults are read with the FirstPair Reader contract (discoverAll),
// then every file the books point at is opened: aligned chapters (units,
// translations, words and glosses), marker pages, library editions, code
// fragments.  A vault holding <Book>/_data/triptych-reader.json is checked
// with FirstPair Triptych's own index and payload validators.  Prints each
// book's format, title, pages, and parts; exits 1 on any error.
//
// The plugins are taken from ../plugins/ (this repository), else from
// $FIRSTPAIR_PLUGINS (a folder holding firstpair-reader/ and
// firstpair-triptych/), else from ~/src/firstpair/publishing/vault/plugin.

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { homedir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const here = dirname(fileURLToPath(import.meta.url));

function pluginFile(plugin, file) {
  const roots = [
    join(here, "..", "plugins"),
    process.env.FIRSTPAIR_PLUGINS,
    join(homedir(), "src", "firstpair", "publishing", "vault", "plugin"),
  ].filter(Boolean);
  for (const root of roots) {
    const path = join(root, plugin, file);
    if (existsSync(path)) return path;
  }
  return null;
}

const contractPath = pluginFile("firstpair-reader", "contract.js");
if (!contractPath) {
  console.error("FirstPair Reader contract.js not found");
  process.exit(1);
}
const contract = require(contractPath);

// The bundled Triptych plugin, loaded with a stub `obsidian` module for its
// pure validators (exported as __test).
function loadTriptych() {
  const path = pluginFile("firstpair-triptych", "main.js");
  if (!path) return null;
  const Module = require("node:module");
  const original = Module._load;
  class Stub {}
  const obsidian = new Proxy({ normalizePath: (value) => value, Platform: {} }, {
    get: (target, key) => (key in target ? target[key] : Stub),
  });
  Module._load = function load(request, ...rest) {
    return request === "obsidian" ? obsidian : original.call(this, request, ...rest);
  };
  try {
    return require(path).__test;
  } finally {
    Module._load = original;
  }
}

// A vault on disk as the contract's io: vault-relative paths, null when absent.
function vaultIo(root) {
  const full = (path) => join(root, ...String(path || "").split("/").filter(Boolean));
  return {
    async read(path) {
      const file = full(path);
      return existsSync(file) && statSync(file).isFile() ? readFileSync(file, "utf8") : null;
    },
    async list(path) {
      const dir = full(path);
      if (!existsSync(dir) || !statSync(dir).isDirectory()) return null;
      const files = [];
      const folders = [];
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const name = path ? `${path}/${entry.name}` : entry.name;
        (entry.isDirectory() ? folders : files).push(name);
      }
      return { files, folders };
    },
  };
}

const withMd = (note) => (/\.md$/i.test(note) ? note : `${note}.md`);

async function mustRead(io, path, label) {
  const text = await io.read(path);
  if (text === null) throw new Error(`${label}: missing ${path}`);
  return text;
}

async function checkAligned(io, book) {
  const aligned = typeof book.aligned === "string" ? JSON.parse(await mustRead(io, book.aligned, "aligned")) : book.aligned;
  const ids = (aligned.translations || []).map((item) => item.id);
  if (!ids.length) throw new Error("aligned edition lists no translations");
  let units = 0;
  const all = [];
  for (const page of book.pages) {
    if (!page.chapter) throw new Error(`page ${page.id} has no chapter`);
    const chapter = JSON.parse(await mustRead(io, page.chapter, `page ${page.id}`));
    if (chapter.schema !== "firstpair-aligned-chapter-v1") throw new Error(`${page.chapter}: schema ${chapter.schema}`);
    const seen = new Set();
    for (const unit of chapter.units || []) {
      const where = `${page.chapter} ${unit.id}`;
      if (!unit.id || seen.has(unit.id)) throw new Error(`${where}: missing or repeated unit id`);
      seen.add(unit.id);
      if (!Array.isArray(unit.source) || !unit.source.join("").trim()) throw new Error(`${where}: no source`);
      for (const id of ids) {
        if (!Array.isArray(unit.translations?.[id]) || !unit.translations[id].join("").trim()) {
          throw new Error(`${where}: no ${id} translation`);
        }
      }
      if (unit.kind && !["heading", "quote", "footnote", "cover"].includes(unit.kind)) {
        throw new Error(`${where}: unknown kind ${unit.kind}`);
      }
      if (unit.words) {
        const joined = unit.words.map((word) => word[0]).join("");
        if (joined !== unit.source.join("")) throw new Error(`${where}: words do not spell the source`);
        for (const word of unit.words) {
          const content = /[\p{L}\p{N}]/u.test(word[0]);
          if (content && (!word[1] || !word[2])) throw new Error(`${where}: ${word[0]} lacks a reading or gloss`);
        }
        for (const [lang, list] of Object.entries(unit.glosses || {})) {
          if (!Array.isArray(list) || list.length !== unit.words.length) {
            throw new Error(`${where}: glosses.${lang} has ${list?.length} items for ${unit.words.length} words`);
          }
        }
      }
      units += 1;
      all.push(unit);
    }
  }
  const languages = contract.glossLanguages(aligned, all, ids);
  return `${units} units, translations ${ids.join(", ")}, gloss ${languages.join("/") || "none"}`;
}

async function checkMarkdownPages(io, book) {
  for (const page of book.pages) {
    if (page.markdown !== null) continue;
    const text = await mustRead(io, page.file, `page ${page.id}`);
    if (page.marker && contract.extractMarked(text, page.marker) === null) {
      throw new Error(`page ${page.id}: markers missing in ${page.file}`);
    }
  }
}

async function checkCode(io, book) {
  const data = JSON.parse(await mustRead(io, book.fragments, "fragments"));
  const rows = new Map((Array.isArray(data) ? data : data.fragments || []).map((row) => [row.id, row]));
  let cards = 0;
  for (const page of book.pages) {
    const text = await mustRead(io, page.file, `chapter ${page.id}`);
    for (const match of text.matchAll(/^```(?:firstpair|rgbdns|sail)-fragment\n([\s\S]*?)^```/gm)) {
      const { id } = JSON.parse(match[1]);
      const row = rows.get(id);
      if (!row) throw new Error(`${page.file}: unknown fragment ${id}`);
      const code = await mustRead(io, withMd(row.code_note), `fragment ${id}`);
      const fence = code.slice(code.indexOf("## Full Source")).split("\n");
      const open = fence.findIndex((line) => line.startsWith("```"));
      const close = fence.findIndex((line, index) => index > open && /^```\s*$/.test(line));
      const lines = fence.slice(open + 1, close);
      if (!(row.start_line >= 1 && row.end_line >= row.start_line && row.end_line <= lines.length)) {
        throw new Error(`fragment ${id}: lines ${row.start_line}-${row.end_line} outside ${lines.length}`);
      }
      cards += 1;
    }
  }
  return `${rows.size} fragments, ${cards} cards`;
}

async function checkNotes(io, book) {
  for (const key of ["launcher", "contents"]) {
    if (book[key]) await mustRead(io, withMd(book[key]), key);
  }
  for (const part of book.parts) if (part.note) await mustRead(io, withMd(part.note), `part ${part.id}`);
}

function describe(book) {
  const shelf = contract.shelfEntry(book);
  const parts = book.parts.map((part) => `${part.title} (${part.pageIds.length})`).join("; ");
  return [
    `  ${book.format.padEnd(9)} ${book.root || "/"}: ${book.title}`
      + (shelf.languages ? ` [${shelf.languages}]` : "") + (book.uiLang ? ` ui=${book.uiLang}` : ""),
    `            ${book.pages.length} pages; parts: ${parts}`,
  ];
}

async function checkReaderVault(root) {
  const io = vaultIo(root);
  const { books, broken } = await contract.discoverAll(io);
  const out = [];
  for (const item of broken) throw new Error(`${item.root || "/"}: ${item.error.message}`);
  for (const book of books) {
    if (book.format === "library") {
      out.push(`  library   ${book.root || "/"}: ${book.title}, ${book.editions.length} editions`);
      for (const source of [book.sources.anthology, ...book.sources.notes.map((row) => row.note)].filter(Boolean)) {
        await mustRead(io, withMd(source), "library source");
      }
      for (const edition of book.editions) {
        const model = await contract.loadEdition(io, book, edition.id);
        await checkMarkdownPages(io, model);
        await checkNotes(io, model);
        out.push(`    edition ${edition.id}: ${model.title} (${edition.family}, ${edition.version}), `
          + `${model.pages.length} pages; parts: ${model.parts.map((part) => `${part.title} (${part.pageIds.length})`).join("; ")}`);
      }
      continue;
    }
    out.push(...describe(book));
    await checkNotes(io, book);
    if (book.aligned) out.push(`            ${await checkAligned(io, book)}`);
    else if (book.format === "code") out.push(`            ${await checkCode(io, book)}`);
    else await checkMarkdownPages(io, book);
  }
  return out;
}

async function checkTriptychVault(root, folder) {
  const triptych = loadTriptych();
  if (!triptych) throw new Error("FirstPair Triptych main.js not found");
  const io = vaultIo(root);
  const reader = triptych.parseTriptychReaderIndex(await mustRead(io, `${folder}/_data/triptych-reader.json`, "index"));
  for (const key of ["launcher", "contents", "review"]) await mustRead(io, withMd(reader[key]), key);
  const out = [`  triptych  ${folder}: ${reader.title}, editions ${reader.editions.map((e) => e.id).join(", ")}`];
  for (const set of reader.sets) {
    await mustRead(io, withMd(set.note), `set ${set.id}`);
    for (const page of set.pages) {
      const note = withMd(page.note);
      const payload = triptych.extractTriptychPayload(await mustRead(io, note, page.key));
      triptych.validateIndexedTriptychPayload(payload, note, reader);
    }
    out.push(`            set ${set.id}: ${set.pages.length} pages; parts: `
      + set.parts.map((part) => `${part.title} (${set.pages.filter((p) => p.part_id === part.id).length})`).join("; "));
  }
  const diffs = await io.read(`${folder}/_data/triptych-diffs.json`);
  if (diffs !== null) {
    const parsed = triptych.diffView.parseDiffs(diffs);
    out.push(`            diffs: ${Object.keys(parsed.pages).length} pages, categories ${parsed.categories.length}`);
  }
  const metrics = await io.read(`${folder}/_data/triptych-metrics.json`);
  if (metrics !== null) {
    const parsed = triptych.parseMetrics(metrics);
    out.push(`            metrics: ${parsed.metrics.map((metric) => metric.key).join(", ")}`);
  }
  return out;
}

async function checkVault(root) {
  const triptychFolders = readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(root, entry.name, "_data", "triptych-reader.json")))
    .map((entry) => entry.name);
  if (triptychFolders.length) {
    const out = [];
    for (const folder of triptychFolders) out.push(...await checkTriptychVault(root, folder));
    return out;
  }
  return checkReaderVault(root);
}

const args = process.argv.slice(2);
const vaults = args.length
  ? args.map((arg) => resolve(arg))
  : readdirSync(here, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith(".") && entry.name !== "build")
    .map((entry) => join(here, entry.name))
    .sort();

console.log(`contract: ${relative(process.cwd(), contractPath) || contractPath}`);
let failed = 0;
for (const root of vaults) {
  const name = relative(process.cwd(), root) || root;
  try {
    const lines = await checkVault(root);
    console.log(`ok ${name}`);
    for (const line of lines) console.log(line);
  } catch (error) {
    failed += 1;
    console.log(`FAIL ${name}: ${error.message}`);
  }
}
process.exit(failed ? 1 : 0);
