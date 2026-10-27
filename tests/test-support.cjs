"use strict";

// The test DOM and Markdown renderer stand in for jsdom and Obsidian; check
// the parts the plugin tests lean on, so a plugin failure is the plugin's.
const test = require("node:test");
const assert = require("node:assert/strict");
const { createWindow } = require("./support/dom.cjs");
const { renderMarkdown } = require("./support/markdown.cjs");

test("selectors: classes, attributes, combinators, lists, and pseudo-classes", () => {
  const { document } = createWindow();
  document.body.innerHTML = '<table><thead><tr><th>A</th><th>B</th></tr></thead><tbody><tr><td lang="la">x</td><td>y</td></tr></tbody></table>'
    + '<p class="a b" data-x="1"><a href="#fn-1">1</a><a href="https://example.org">w</a></p><pre><code class="language-js">1</code></pre>';
  assert.equal(document.querySelectorAll("td:first-child").length, 1);
  assert.equal(document.querySelectorAll("thead th, tr:first-child th").length, 2);
  assert.equal(document.querySelector('a[href="#fn-1"]').textContent, "1");
  assert.equal(document.querySelectorAll('a[href^="https:"]').length, 1);
  assert.equal(document.querySelector('pre > code[class^="language-"]').className, "language-js");
  assert.equal(document.querySelector("p.a.b[data-x]").dataset.x, "1");
  assert.equal(document.querySelector("table td:not([lang])").textContent, "y");
  assert.equal(document.querySelector("a").closest("p.b").tagName, "P");
  assert.equal(document.querySelector("tbody td").matches("table [lang=la]"), true);
});

test("events: capture, bubbling, cancellation, and checkbox activation", () => {
  const window = createWindow();
  const { document } = window;
  const label = document.createElement("label");
  const box = document.createElement("input");
  box.setAttribute("type", "checkbox");
  label.append(box, "word");
  document.body.append(label);
  const seen = [];
  document.addEventListener("click", () => seen.push("capture"), true);
  window.addEventListener("click", () => seen.push("window"));
  box.addEventListener("change", () => seen.push(`change ${box.checked}`));
  label.click();
  // The label's click, then the click it forwards to its box, then change.
  assert.deepEqual(seen, ["capture", "window", "capture", "window", "change true"]);
  assert.equal(box.checked, true);
  seen.length = 0;
  box.addEventListener("click", (event) => event.preventDefault(), { once: true });
  box.click();
  assert.equal(box.checked, true, "a cancelled click restores the box");
  assert.equal(seen.includes("change false"), false);
});

test("text: tree walker, splitText, normalize, and focus", () => {
  const { document } = createWindow();
  const root = document.body;
  root.innerHTML = '<p>alpha <b>beta</b> <span data-reader-ui="">ui</span> gamma</p><p id="note" tabindex="-1">n</p>';
  const walker = document.createTreeWalker(root, 4, { acceptNode: (node) => (node.parentElement.hasAttribute("data-reader-ui") ? 2 : 1) });
  const texts = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) texts.push(node.data);
  assert.deepEqual(texts, ["alpha ", "beta", " ", " gamma", "n"], "the ui span is skipped");
  const first = root.querySelector("p").firstChild;
  first.splitText(2);
  assert.equal(root.querySelector("p").childNodes.length, 6);
  root.querySelector("p").normalize();
  assert.equal(root.querySelector("p").firstChild.data, "alpha ");
  document.getElementById("note").focus();
  assert.equal(document.activeElement.id, "note");
  root.querySelector("p").focus();
  assert.equal(document.activeElement.id, "note", "a plain paragraph takes no focus");
});

test("markdown: blocks, tables, fences, raw HTML, and inline markup", () => {
  const html = renderMarkdown("# Title {.unnumbered}\n\nA *b* [c](https://example.org) `d`<sup>1</sup>\n\n> quote\n\n| L | E |\n|---|---|\n| *x* | y |\n\n```rust\nfn f() {}\n```\n\n<!-- marker -->\nafter\n\n<p id=\"fn\">foot</p>\n");
  const { document } = createWindow();
  document.body.innerHTML = html;
  assert.equal(document.querySelector("h1").textContent, "Title {.unnumbered}");
  assert.equal(document.querySelector("p em").textContent, "b");
  assert.equal(document.querySelector("p a").getAttribute("href"), "https://example.org");
  assert.equal(document.querySelector("p sup").textContent, "1");
  assert.equal(document.querySelector("blockquote p").textContent, "quote");
  assert.equal(document.querySelector("td em").textContent, "x");
  assert.equal(document.querySelector("pre code.language-rust").textContent, "fn f() {}\n");
  assert.equal(document.querySelector("#fn").textContent, "foot");
  assert.ok(Array.from(document.querySelectorAll("p")).some((p) => p.textContent === "after"));
});
