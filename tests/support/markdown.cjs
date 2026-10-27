"use strict";

// A small Markdown-to-HTML renderer for the test fixtures, standing in for
// Obsidian's renderer: ATX headings, paragraphs, blockquotes, pipe tables,
// fenced code (with a language class), simple lists, rules, raw HTML blocks
// and comments, and inline code, links, emphasis, and inline HTML.

const escapeHtml = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const escapeAttr = (text) => escapeHtml(text).replace(/"/g, "&quot;");

const FENCE = /^ {0,3}(`{3,}|~{3,})\s*([^\s`]*)/;
const HEADING = /^ {0,3}(#{1,6})(?:\s+(.*?))?(?:\s+#+)?\s*$/;
const RULE = /^ {0,3}([-*_])(?:\s*\1){2,}\s*$/;
const LIST = /^ {0,3}([-*+]|\d+[.)])\s+(.*)$/;
const QUOTE = /^ {0,3}>\s?(.*)$/;
const HTML_BLOCK = /^ {0,3}<(?:!--|\/?[a-zA-Z][\w-]*(?:\s|\/?>|$))/;
const TABLE_RULE = /^\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*$/;

function cells(line) {
  let text = line.trim();
  if (text.startsWith("|")) text = text.slice(1);
  if (text.endsWith("|") && !text.endsWith("\\|")) text = text.slice(0, -1);
  const out = [];
  let current = "";
  for (let i = 0; i < text.length; i += 1) {
    if (text[i] === "\\" && text[i + 1] === "|") { current += "|"; i += 1; continue; }
    if (text[i] === "|") { out.push(current.trim()); current = ""; continue; }
    current += text[i];
  }
  out.push(current.trim());
  return out;
}

function inline(text) {
  let out = "";
  let i = 0;
  while (i < text.length) {
    const rest = text.slice(i);
    let match;
    if ((match = /^<!--[\s\S]*?-->/.exec(rest)) || (match = /^<\/?[a-zA-Z][\w-]*(?:\s[^<>]*)?\/?>/.exec(rest))) {
      out += match[0]; i += match[0].length; continue;
    }
    if ((match = /^(`+)([\s\S]*?[^`])\1(?!`)/.exec(rest))) {
      out += `<code>${escapeHtml(match[2].trim())}</code>`; i += match[0].length; continue;
    }
    if ((match = /^!?\[([^\]]*)\]\(\s*<?([^)\s>]*)>?(?:\s+"([^"]*)")?\s*\)/.exec(rest))) {
      const title = match[3] ? ` title="${escapeAttr(match[3])}"` : "";
      out += rest[0] === "!"
        ? `<img src="${escapeAttr(match[2])}" alt="${escapeAttr(match[1])}"${title}>`
        : `<a href="${escapeAttr(match[2])}"${title}>${inline(match[1])}</a>`;
      i += match[0].length; continue;
    }
    if ((match = /^(\*\*|__)(?=\S)([\s\S]*?\S)\1/.exec(rest))) {
      out += `<strong>${inline(match[2])}</strong>`; i += match[0].length; continue;
    }
    if ((match = /^(\*|_)(?=\S)([\s\S]*?\S)\1(?!\1)/.exec(rest)) && (match[1] === "*" || !/\w/.test(text[i - 1] ?? ""))) {
      out += `<em>${inline(match[2])}</em>`; i += match[0].length; continue;
    }
    if ((match = /^\\([\\`*_{}[\]()#+\-.!|<>])/.exec(rest))) {
      out += escapeHtml(match[1]); i += match[0].length; continue;
    }
    if (rest.startsWith("  \n")) { out += "<br>\n"; i += 3; continue; }
    if (rest[0] === "&" && (match = /^&(?:#x[0-9a-f]+|#\d+|[a-z]+);/i.exec(rest))) { out += match[0]; i += match[0].length; continue; }
    out += escapeHtml(rest[0]);
    i += 1;
  }
  return out;
}

function blocks(lines) {
  const out = [];
  let i = 0;
  const blank = (line) => !line || !line.trim();
  const startsBlock = (line, next) => FENCE.test(line) || HEADING.test(line) || QUOTE.test(line) || RULE.test(line)
    || LIST.test(line) || HTML_BLOCK.test(line) || (line.includes("|") && next !== undefined && TABLE_RULE.test(next) && next.includes("-"));
  while (i < lines.length) {
    const line = lines[i];
    if (blank(line)) { i += 1; continue; }
    let match;
    if ((match = FENCE.exec(line))) {
      const fence = match[1];
      const body = [];
      i += 1;
      while (i < lines.length && !new RegExp(`^ {0,3}${fence[0] === "`" ? "`" : "~"}{${fence.length},}\\s*$`).test(lines[i])) body.push(lines[i++]);
      i += 1;
      const cls = match[2] ? ` class="language-${escapeAttr(match[2])}"` : "";
      out.push(`<pre><code${cls}>${escapeHtml(body.join("\n"))}${body.length ? "\n" : ""}</code></pre>`);
      continue;
    }
    if ((match = HEADING.exec(line))) {
      const level = match[1].length;
      out.push(`<h${level}>${inline((match[2] ?? "").trim())}</h${level}>`);
      i += 1; continue;
    }
    if (RULE.test(line)) { out.push("<hr>"); i += 1; continue; }
    if (QUOTE.test(line)) {
      const body = [];
      while (i < lines.length && !blank(lines[i]) && (QUOTE.test(lines[i]) || !startsBlock(lines[i], lines[i + 1]))) {
        const quoted = QUOTE.exec(lines[i]);
        body.push(quoted ? quoted[1] : lines[i]);
        i += 1;
      }
      out.push(`<blockquote>\n${blocks(body)}</blockquote>`);
      continue;
    }
    if (HTML_BLOCK.test(line)) {
      const body = [];
      if (/^ {0,3}<!--/.test(line)) {
        while (i < lines.length) { body.push(lines[i]); if (lines[i++].includes("-->")) break; }
      } else {
        while (i < lines.length && !blank(lines[i])) body.push(lines[i++]);
      }
      out.push(body.join("\n"));
      continue;
    }
    if (line.includes("|") && i + 1 < lines.length && TABLE_RULE.test(lines[i + 1]) && lines[i + 1].includes("-")) {
      const head = cells(line);
      i += 2;
      const rows = [];
      while (i < lines.length && !blank(lines[i]) && lines[i].includes("|")) rows.push(cells(lines[i++]));
      const row = (values, tag) => `<tr>\n${head.map((_h, index) => `<${tag}>${inline(values[index] ?? "")}</${tag}>`).join("\n")}\n</tr>`;
      out.push(`<table>\n<thead>\n${row(head, "th")}\n</thead>\n${rows.length ? `<tbody>${rows.map((values) => row(values, "td")).join("\n")}</tbody>\n` : ""}</table>`);
      continue;
    }
    if ((match = LIST.exec(line))) {
      const ordered = /\d/.test(match[1]);
      const items = [];
      while (i < lines.length && (match = LIST.exec(lines[i])) && /\d/.test(match[1]) === ordered) {
        const item = [match[2]];
        i += 1;
        while (i < lines.length && !blank(lines[i]) && !LIST.test(lines[i]) && /^\s+/.test(lines[i])) item.push(lines[i++].trim());
        items.push(`<li>${inline(item.join("\n"))}</li>`);
        if (i < lines.length && blank(lines[i]) && LIST.test(lines[i + 1] ?? "")) i += 1;
      }
      const tag = ordered ? "ol" : "ul";
      out.push(`<${tag}>\n${items.join("\n")}\n</${tag}>`);
      continue;
    }
    const body = [];
    while (i < lines.length && !blank(lines[i]) && (body.length === 0 || !startsBlock(lines[i], lines[i + 1]))) body.push(lines[i++]);
    out.push(`<p>${inline(body.join("\n"))}</p>`);
  }
  return out.map((block) => `${block}\n`).join("");
}

function renderMarkdown(markdown) {
  return blocks(String(markdown).replace(/\r\n?/g, "\n").replace(/\t/g, "    ").split("\n"));
}

module.exports = { renderMarkdown };
