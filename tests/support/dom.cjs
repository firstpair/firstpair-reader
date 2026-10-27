"use strict";

// A small, dependency-free DOM for the plugin tests: enough of Node, Element,
// Text, Document, events, selectors, TreeWalker, forms, and an HTML parser
// to open the plugins headlessly.  It does no layout: sizes are zero unless a
// test defines them.

const HTML_NS = "http://www.w3.org/1999/xhtml";
const VOID = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"]);
const RAW_TEXT = new Set(["script", "style", "textarea", "title"]);
const CLOSES_P = new Set(["address", "article", "aside", "blockquote", "details", "div", "dl", "fieldset", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "main", "menu", "nav", "ol", "p", "pre", "section", "table", "ul"]);
const FORM_CONTROLS = new Set(["button", "input", "select", "textarea", "option", "fieldset"]);

class NodeList extends Array {
  item(index) { return this[index] ?? null; }
}

const list = (items) => NodeList.from(items);

/* ------------------------------------------------------------------ events */

class Event {
  constructor(type, init = {}) {
    this.type = String(type);
    this.bubbles = Boolean(init.bubbles);
    this.cancelable = Boolean(init.cancelable);
    this.composed = Boolean(init.composed);
    this.defaultPrevented = false;
    this.target = null;
    this.currentTarget = null;
    this.eventPhase = 0;
    this.isTrusted = false;
    this.timeStamp = Date.now();
    this._stop = false;
    this._stopNow = false;
  }
  preventDefault() { if (this.cancelable) this.defaultPrevented = true; }
  stopPropagation() { this._stop = true; }
  stopImmediatePropagation() { this._stop = true; this._stopNow = true; }
  composedPath() { return this._path ? this._path.slice() : []; }
}
Event.NONE = 0; Event.CAPTURING_PHASE = 1; Event.AT_TARGET = 2; Event.BUBBLING_PHASE = 3;

class UIEvent extends Event {
  constructor(type, init = {}) { super(type, init); this.detail = init.detail ?? 0; this.view = init.view ?? null; }
}
class KeyboardEvent extends UIEvent {
  constructor(type, init = {}) {
    super(type, init);
    this.key = init.key ?? ""; this.code = init.code ?? "";
    this.altKey = Boolean(init.altKey); this.ctrlKey = Boolean(init.ctrlKey);
    this.metaKey = Boolean(init.metaKey); this.shiftKey = Boolean(init.shiftKey);
    this.repeat = Boolean(init.repeat);
  }
}
class MouseEvent extends UIEvent {
  constructor(type, init = {}) {
    super(type, init);
    this.button = init.button ?? 0; this.buttons = init.buttons ?? 0;
    this.clientX = init.clientX ?? 0; this.clientY = init.clientY ?? 0;
    this.altKey = Boolean(init.altKey); this.ctrlKey = Boolean(init.ctrlKey);
    this.metaKey = Boolean(init.metaKey); this.shiftKey = Boolean(init.shiftKey);
    this.relatedTarget = init.relatedTarget ?? null;
  }
}
class PointerEvent extends MouseEvent {
  constructor(type, init = {}) { super(type, init); this.pointerId = init.pointerId ?? 0; this.pointerType = init.pointerType ?? ""; this.isPrimary = Boolean(init.isPrimary); }
}
class FocusEvent extends UIEvent {}
class InputEvent extends UIEvent {
  constructor(type, init = {}) { super(type, init); this.data = init.data ?? null; this.inputType = init.inputType ?? ""; }
}
class CustomEvent extends Event {
  constructor(type, init = {}) { super(type, init); this.detail = init.detail ?? null; }
}

class EventTarget {
  constructor() { this._listeners = new Map(); }
  addEventListener(type, listener, options) {
    if (!listener) return;
    const capture = typeof options === "boolean" ? options : Boolean(options?.capture);
    const once = typeof options === "object" && options !== null && Boolean(options.once);
    const entries = this._listeners.get(type) ?? [];
    if (entries.some((entry) => entry.listener === listener && entry.capture === capture)) return;
    entries.push({ listener, capture, once });
    this._listeners.set(type, entries);
  }
  removeEventListener(type, listener, options) {
    const capture = typeof options === "boolean" ? options : Boolean(options?.capture);
    const entries = this._listeners.get(type);
    if (!entries) return;
    const index = entries.findIndex((entry) => entry.listener === listener && entry.capture === capture);
    if (index >= 0) entries.splice(index, 1);
  }
  _parentForEvent() { return null; }
  _invoke(event, phase) {
    const entries = (this._listeners.get(event.type) ?? []).slice();
    for (const entry of entries) {
      if (phase === Event.CAPTURING_PHASE && !entry.capture) continue;
      if (phase === Event.BUBBLING_PHASE && entry.capture) continue;
      if (!(this._listeners.get(event.type) ?? []).includes(entry)) continue;
      if (entry.once) this.removeEventListener(event.type, entry.listener, entry.capture);
      event.currentTarget = this;
      try {
        if (typeof entry.listener === "function") entry.listener.call(this, event);
        else entry.listener.handleEvent(event);
      } catch (error) {
        // As in a browser, a throwing listener does not stop the dispatch.
        console.error(error);
      }
      if (event._stopNow) return;
    }
  }
  dispatchEvent(event) {
    const path = [];
    for (let node = this; node; node = node._parentForEvent()) path.push(node);
    event.target = this;
    event._path = path;
    event._stop = false; event._stopNow = false;
    const activation = event.type === "click" && event instanceof MouseEvent ? activationTarget(path) : null;
    const undo = activation ? activation._preActivate?.() : null;
    for (let i = path.length - 1; i > 0 && !event._stop; i -= 1) {
      event.eventPhase = Event.CAPTURING_PHASE;
      path[i]._invoke(event, Event.CAPTURING_PHASE);
    }
    if (!event._stop) {
      event.eventPhase = Event.AT_TARGET;
      this._invoke(event, Event.CAPTURING_PHASE);
      if (!event._stopNow) this._invoke(event, Event.BUBBLING_PHASE);
    }
    if (event.bubbles) {
      for (let i = 1; i < path.length && !event._stop; i += 1) {
        event.eventPhase = Event.BUBBLING_PHASE;
        path[i]._invoke(event, Event.BUBBLING_PHASE);
      }
    }
    event.eventPhase = 0;
    event.currentTarget = null;
    if (activation) {
      if (event.defaultPrevented) undo?.();
      else activation._activate?.(event);
    }
    return !event.defaultPrevented;
  }
}

function activationTarget(path) {
  for (const node of path) {
    if (node.nodeType !== 1) continue;
    if (node._preActivate || node._activate) return node;
  }
  return null;
}

/* -------------------------------------------------------------------- nodes */

class Node extends EventTarget {
  constructor(document) {
    super();
    this.ownerDocument = document;
    this.parentNode = null;
    this._children = [];
  }
  get parentElement() { return this.parentNode && this.parentNode.nodeType === 1 ? this.parentNode : null; }
  get childNodes() { return list(this._children); }
  get firstChild() { return this._children[0] ?? null; }
  get lastChild() { return this._children[this._children.length - 1] ?? null; }
  get nextSibling() { const siblings = this.parentNode?._children; return siblings ? siblings[siblings.indexOf(this) + 1] ?? null : null; }
  get previousSibling() { const siblings = this.parentNode?._children; return siblings ? siblings[siblings.indexOf(this) - 1] ?? null : null; }
  get isConnected() { let node = this; while (node.parentNode) node = node.parentNode; return node.nodeType === 9; }
  get nodeValue() { return null; }
  set nodeValue(_value) {}
  getRootNode() { let node = this; while (node.parentNode) node = node.parentNode; return node; }
  hasChildNodes() { return this._children.length > 0; }
  _parentForEvent() {
    if (this.parentNode) return this.parentNode;
    return null;
  }
  contains(other) {
    for (let node = other; node; node = node.parentNode) if (node === this) return true;
    return false;
  }
  _adopt(node) {
    if (node.nodeType === 11) {
      const moved = node._children.slice();
      for (const child of moved) node.removeChild(child);
      return moved;
    }
    if (node.contains(this)) throw new Error("HierarchyRequestError: a node cannot contain itself");
    if (node.parentNode) node.parentNode.removeChild(node);
    return [node];
  }
  insertBefore(node, reference) {
    if (reference && reference.parentNode !== this) throw new Error("NotFoundError: reference is not a child");
    if (node === reference) return node;
    const nodes = this._adopt(node);
    let index = reference ? this._children.indexOf(reference) : this._children.length;
    for (const child of nodes) {
      child.parentNode = this;
      this._children.splice(index, 0, child);
      index += 1;
    }
    return node;
  }
  appendChild(node) { return this.insertBefore(node, null); }
  removeChild(node) {
    const index = this._children.indexOf(node);
    if (index < 0) throw new Error("NotFoundError: not a child");
    this._children.splice(index, 1);
    node.parentNode = null;
    const document = this.ownerDocument ?? this;
    if (document._activeElement && node.contains(document._activeElement)) document._activeElement = null;
    return node;
  }
  replaceChild(node, old) { this.insertBefore(node, old); this.removeChild(old); return old; }
  _nodes(items) {
    const document = this.ownerDocument ?? this;
    return items.map((item) => (item instanceof Node ? item : document.createTextNode(String(item))));
  }
  append(...items) { for (const node of this._nodes(items)) this.appendChild(node); }
  prepend(...items) { const first = this.firstChild; for (const node of this._nodes(items)) this.insertBefore(node, first); }
  replaceChildren(...items) { for (const child of this._children.slice()) this.removeChild(child); this.append(...items); }
  remove() { if (this.parentNode) this.parentNode.removeChild(this); }
  before(...items) { const parent = this.parentNode; if (!parent) return; for (const node of this._nodes(items)) parent.insertBefore(node, this); }
  after(...items) {
    const parent = this.parentNode; if (!parent) return;
    let reference = this.nextSibling;
    for (const node of this._nodes(items)) { if (node === reference) reference = node.nextSibling; parent.insertBefore(node, reference); }
  }
  replaceWith(...items) {
    const parent = this.parentNode; if (!parent) return;
    let reference = this.nextSibling;
    while (reference && items.includes(reference)) reference = reference.nextSibling;
    const nodes = this._nodes(items);
    parent.removeChild(this);
    for (const node of nodes) parent.insertBefore(node, reference);
  }
  normalize() {
    for (const child of this._children.slice()) {
      if (child.nodeType === 3) {
        if (!child.data) { this.removeChild(child); continue; }
        let next = child.nextSibling;
        while (next && next.nodeType === 3) { child.data += next.data; this.removeChild(next); next = child.nextSibling; }
      } else child.normalize();
    }
  }
  get textContent() {
    let text = "";
    for (const child of this._children) if (child.nodeType === 1 || child.nodeType === 3 || child.nodeType === 11) text += child.textContent;
    return text;
  }
  set textContent(value) {
    for (const child of this._children.slice()) this.removeChild(child);
    const text = value == null ? "" : String(value);
    if (text) this.appendChild((this.ownerDocument ?? this).createTextNode(text));
  }
  compareDocumentPosition(other) {
    if (other === this) return 0;
    const chain = (node) => { const nodes = []; for (; node; node = node.parentNode) nodes.unshift(node); return nodes; };
    const a = chain(this), b = chain(other);
    if (a[0] !== b[0]) return 1;
    let i = 0; while (a[i] === b[i]) i += 1;
    if (i === a.length) return 16 | 4; // other is contained and following
    if (i === b.length) return 8 | 2;
    const siblings = a[i - 1]._children;
    return siblings.indexOf(b[i]) > siblings.indexOf(a[i]) ? 4 : 2;
  }
}
Node.ELEMENT_NODE = 1; Node.TEXT_NODE = 3; Node.COMMENT_NODE = 8; Node.DOCUMENT_NODE = 9; Node.DOCUMENT_FRAGMENT_NODE = 11;
Node.DOCUMENT_POSITION_PRECEDING = 2; Node.DOCUMENT_POSITION_FOLLOWING = 4;

class CharacterData extends Node {
  constructor(document, data) { super(document); this.data = String(data); }
  get nodeValue() { return this.data; }
  set nodeValue(value) { this.data = String(value); }
  get length() { return this.data.length; }
  get nextElementSibling() { return elementSibling(this, 1); }
  get previousElementSibling() { return elementSibling(this, -1); }
}
class Text extends CharacterData {
  get nodeType() { return 3; }
  get nodeName() { return "#text"; }
  get textContent() { return this.data; }
  set textContent(value) { this.data = value == null ? "" : String(value); }
  get wholeText() { return this.data; }
  splitText(offset) {
    const rest = this.ownerDocument.createTextNode(this.data.slice(offset));
    this.data = this.data.slice(0, offset);
    if (this.parentNode) this.parentNode.insertBefore(rest, this.nextSibling);
    return rest;
  }
  cloneNode() { return this.ownerDocument.createTextNode(this.data); }
}
class Comment extends CharacterData {
  get nodeType() { return 8; }
  get nodeName() { return "#comment"; }
  get textContent() { return this.data; }
  set textContent(value) { this.data = String(value); }
  cloneNode() { return this.ownerDocument.createComment(this.data); }
}

function elementSibling(node, step) {
  const siblings = node.parentNode?._children;
  if (!siblings) return null;
  for (let i = siblings.indexOf(node) + step; i >= 0 && i < siblings.length; i += step) if (siblings[i].nodeType === 1) return siblings[i];
  return null;
}

class ParentNode extends Node {
  get children() { return list(this._children.filter((child) => child.nodeType === 1)); }
  get childElementCount() { return this._children.filter((child) => child.nodeType === 1).length; }
  get firstElementChild() { return this._children.find((child) => child.nodeType === 1) ?? null; }
  get lastElementChild() { for (let i = this._children.length - 1; i >= 0; i -= 1) if (this._children[i].nodeType === 1) return this._children[i]; return null; }
  _descendants() {
    const out = [];
    const walk = (node) => { for (const child of node._children) if (child.nodeType === 1) { out.push(child); walk(child); } };
    walk(this);
    return out;
  }
  querySelectorAll(selector) {
    const groups = parseSelector(selector);
    return list(this._descendants().filter((element) => groups.some((group) => matchComplex(element, group, this))));
  }
  querySelector(selector) {
    const groups = parseSelector(selector);
    return this._descendants().find((element) => groups.some((group) => matchComplex(element, group, this))) ?? null;
  }
  getElementsByTagName(name) { const lower = String(name).toLowerCase(); return list(this._descendants().filter((el) => lower === "*" || el.localName === lower)); }
  getElementsByClassName(names) { const wanted = String(names).split(/\s+/).filter(Boolean); return list(this._descendants().filter((el) => wanted.every((cls) => el.classList.contains(cls)))); }
}

class DocumentFragment extends ParentNode {
  get nodeType() { return 11; }
  get nodeName() { return "#document-fragment"; }
  getElementById(id) { return this._descendants().find((el) => el.id === id) ?? null; }
  cloneNode(deep) { const copy = this.ownerDocument.createDocumentFragment(); if (deep) for (const child of this._children) copy.appendChild(child.cloneNode(true)); return copy; }
}

/* ------------------------------------------------------- class list, style */

class DOMTokenList {
  constructor(element) { this._element = element; }
  _tokens() { return (this._element.getAttribute("class") ?? "").split(/\s+/).filter(Boolean); }
  _set(tokens) { this._element.setAttribute("class", [...new Set(tokens)].join(" ")); }
  get length() { return new Set(this._tokens()).size; }
  get value() { return this._element.getAttribute("class") ?? ""; }
  item(index) { return [...new Set(this._tokens())][index] ?? null; }
  contains(token) { return this._tokens().includes(String(token)); }
  add(...tokens) { this._set([...this._tokens(), ...tokens.map(String)]); }
  remove(...tokens) { const drop = new Set(tokens.map(String)); this._set(this._tokens().filter((token) => !drop.has(token))); }
  toggle(token, force) {
    const has = this.contains(token);
    const want = force === undefined ? !has : Boolean(force);
    if (want && !has) this.add(token);
    if (!want && has) this.remove(token);
    return want;
  }
  replace(from, to) { if (!this.contains(from)) return false; this._set(this._tokens().map((token) => (token === from ? to : token))); return true; }
  forEach(fn) { [...new Set(this._tokens())].forEach(fn); }
  [Symbol.iterator]() { return [...new Set(this._tokens())][Symbol.iterator](); }
  toString() { return this.value; }
}

const kebab = (name) => (name.startsWith("--") ? name : name.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`).replace(/^(webkit|moz|ms)-/, "-$1-"));

class StyleDeclaration {
  constructor() { this._values = new Map(); }
  get length() { return this._values.size; }
  item(index) { return [...this._values.keys()][index] ?? ""; }
  getPropertyValue(name) { return this._values.get(kebab(String(name))) ?? ""; }
  setProperty(name, value) {
    const key = kebab(String(name));
    if (value == null || value === "") this._values.delete(key);
    else this._values.set(key, typeof value === "number" && value === 0 ? "0px" : String(value));
  }
  removeProperty(name) { const key = kebab(String(name)); const old = this._values.get(key) ?? ""; this._values.delete(key); return old; }
  get cssText() { return [...this._values].map(([key, value]) => `${key}: ${value};`).join(" "); }
  set cssText(text) {
    this._values.clear();
    for (const part of String(text).split(";")) {
      const index = part.indexOf(":");
      if (index > 0) this.setProperty(part.slice(0, index).trim(), part.slice(index + 1).trim());
    }
  }
}
function makeStyle() {
  const style = new StyleDeclaration();
  return new Proxy(style, {
    get(target, key) {
      if (typeof key === "symbol" || key in target) { const value = Reflect.get(target, key); return typeof value === "function" ? value.bind(target) : value; }
      return target.getPropertyValue(key);
    },
    set(target, key, value) {
      if (typeof key === "symbol" || key in target) return Reflect.set(target, key, value);
      target.setProperty(key, value);
      return true;
    },
  });
}

function makeDataset(element) {
  const attr = (key) => `data-${String(key).replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`)}`;
  return new Proxy({}, {
    get(_target, key) { return typeof key === "symbol" ? undefined : element.getAttribute(attr(key)) ?? undefined; },
    set(_target, key, value) { element.setAttribute(attr(key), String(value)); return true; },
    deleteProperty(_target, key) { element.removeAttribute(attr(key)); return true; },
    has(_target, key) { return element.hasAttribute(attr(key)); },
    ownKeys() { return element._attrs.filter(([name]) => name.startsWith("data-")).map(([name]) => name.slice(5).replace(/-([a-z])/g, (_m, letter) => letter.toUpperCase())); },
    getOwnPropertyDescriptor(_target, key) { const value = element.getAttribute(attr(key)); return value == null ? undefined : { value, enumerable: true, configurable: true, writable: true }; },
  });
}

/* ------------------------------------------------------------------ element */

const rect = () => ({ x: 0, y: 0, top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0, toJSON() { return this; } });

class Element extends ParentNode {
  constructor(document, localName, namespace = HTML_NS) {
    super(document);
    this.localName = localName;
    this.namespaceURI = namespace;
    this._attrs = [];
    this._style = null;
    this.scrollTop = 0;
    this.scrollLeft = 0;
    if (localName === "input") { this._value = null; this._checked = null; this.indeterminate = false; }
    if (localName === "textarea") this._value = null;
    if (localName === "option") this._selected = null;
  }
  get nodeType() { return 1; }
  get tagName() { return this.namespaceURI === HTML_NS ? this.localName.toUpperCase() : this.localName; }
  get nodeName() { return this.tagName; }
  get nextElementSibling() { return elementSibling(this, 1); }
  get previousElementSibling() { return elementSibling(this, -1); }

  get attributes() { return this._attrs.map(([name, value]) => ({ name, value, localName: name })); }
  getAttributeNames() { return this._attrs.map(([name]) => name); }
  getAttribute(name) {
    const key = String(name).toLowerCase();
    if (key === "style" && this._style && this._style.length) return this._style.cssText;
    const found = this._attrs.find(([attr]) => attr === key);
    return found ? found[1] : null;
  }
  setAttribute(name, value) {
    const key = String(name).toLowerCase();
    const text = String(value);
    if (key === "style") { this.style.cssText = text; }
    const found = this._attrs.find(([attr]) => attr === key);
    if (found) found[1] = text; else this._attrs.push([key, text]);
  }
  hasAttribute(name) { const key = String(name).toLowerCase(); return this._attrs.some(([attr]) => attr === key) || (key === "style" && Boolean(this._style?.length)); }
  removeAttribute(name) {
    const key = String(name).toLowerCase();
    if (key === "style" && this._style) this._style.cssText = "";
    this._attrs = this._attrs.filter(([attr]) => attr !== key);
  }
  toggleAttribute(name, force) {
    const has = this.hasAttribute(name);
    const want = force === undefined ? !has : Boolean(force);
    if (want && !has) this.setAttribute(name, "");
    if (!want && has) this.removeAttribute(name);
    return want;
  }

  get id() { return this.getAttribute("id") ?? ""; }
  set id(value) { this.setAttribute("id", value); }
  get className() { return this.getAttribute("class") ?? ""; }
  set className(value) { this.setAttribute("class", value); }
  get classList() { return (this._classList ??= new DOMTokenList(this)); }
  get dataset() { return (this._dataset ??= makeDataset(this)); }
  get style() { return (this._style ??= makeStyle()); }

  get innerHTML() { return this._children.map(serialize).join(""); }
  set innerHTML(html) {
    for (const child of this._children.slice()) this.removeChild(child);
    parseHTML(this.ownerDocument, String(html), this);
  }
  get outerHTML() { return serialize(this); }
  get innerText() { return this.textContent; }
  set innerText(value) { this.textContent = value; }
  insertAdjacentHTML(position, html) {
    const fragment = this.ownerDocument.createDocumentFragment();
    parseHTML(this.ownerDocument, String(html), fragment);
    this._insertAdjacent(position, fragment);
  }
  insertAdjacentElement(position, element) { this._insertAdjacent(position, element); return element; }
  insertAdjacentText(position, text) { this._insertAdjacent(position, this.ownerDocument.createTextNode(text)); }
  _insertAdjacent(position, node) {
    switch (String(position).toLowerCase()) {
      case "beforebegin": this.parentNode?.insertBefore(node, this); break;
      case "afterbegin": this.insertBefore(node, this.firstChild); break;
      case "beforeend": this.appendChild(node); break;
      case "afterend": this.parentNode?.insertBefore(node, this.nextSibling); break;
      default: throw new Error(`bad position ${position}`);
    }
  }

  matches(selector) { return parseSelector(selector).some((group) => matchComplex(this, group, null)); }
  closest(selector) {
    const groups = parseSelector(selector);
    for (let node = this; node && node.nodeType === 1; node = node.parentNode) if (groups.some((group) => matchComplex(node, group, null))) return node;
    return null;
  }
  getElementById(id) { return this._descendants().find((el) => el.id === id) ?? null; }

  cloneNode(deep) {
    const copy = this.ownerDocument.createElementNS(this.namespaceURI, this.localName);
    for (const [name, value] of this._attrs) copy._attrs.push([name, value]);
    if (this._style) copy.style.cssText = this._style.cssText;
    if (deep) for (const child of this._children) copy.appendChild(child.cloneNode(true));
    return copy;
  }

  // Layout: nothing is measured.
  getBoundingClientRect() { return rect(); }
  getClientRects() { return []; }
  get clientWidth() { return 0; }
  get clientHeight() { return 0; }
  get offsetWidth() { return 0; }
  get offsetHeight() { return 0; }
  get offsetTop() { return 0; }
  get offsetLeft() { return 0; }
  get offsetParent() { return null; }
  get scrollWidth() { return 0; }
  get scrollHeight() { return 0; }
  scrollIntoView() {}
  scrollTo(x, y) { if (typeof x === "object" && x) { if (x.top != null) this.scrollTop = x.top; if (x.left != null) this.scrollLeft = x.left; } else { this.scrollLeft = x ?? 0; this.scrollTop = y ?? 0; } }
  scrollBy(x, y) { if (typeof x === "object" && x) { this.scrollTop += x.top ?? 0; this.scrollLeft += x.left ?? 0; } else { this.scrollLeft += x ?? 0; this.scrollTop += y ?? 0; } }
  setPointerCapture(id) { (this._captures ??= new Set()).add(id); }
  releasePointerCapture(id) { this._captures?.delete(id); }
  hasPointerCapture(id) { return Boolean(this._captures?.has(id)); }

  // Reflected attributes.
  get title() { return this.getAttribute("title") ?? ""; }
  set title(value) { this.setAttribute("title", value); }
  get lang() { return this.getAttribute("lang") ?? ""; }
  set lang(value) { this.setAttribute("lang", value); }
  get name() { return this.getAttribute("name") ?? ""; }
  set name(value) { this.setAttribute("name", value); }
  get hidden() { return this.hasAttribute("hidden"); }
  set hidden(value) { this.toggleAttribute("hidden", Boolean(value)); }
  get disabled() { return FORM_CONTROLS.has(this.localName) && this.hasAttribute("disabled"); }
  set disabled(value) { this.toggleAttribute("disabled", Boolean(value)); }
  get placeholder() { return this.getAttribute("placeholder") ?? ""; }
  set placeholder(value) { this.setAttribute("placeholder", value); }
  get src() { return this.getAttribute("src") ?? ""; }
  set src(value) { this.setAttribute("src", value); }
  get href() { return this.getAttribute("href") ?? ""; }
  set href(value) { this.setAttribute("href", value); }
  get rows() { return Number(this.getAttribute("rows") ?? 2); }
  set rows(value) { this.setAttribute("rows", value); }
  get min() { return this.getAttribute("min") ?? ""; }
  set min(value) { this.setAttribute("min", value); }
  get max() { return this.getAttribute("max") ?? ""; }
  set max(value) { this.setAttribute("max", value); }
  get step() { return this.getAttribute("step") ?? ""; }
  set step(value) { this.setAttribute("step", value); }
  get controls() { return this.hasAttribute("controls"); }
  set controls(value) { this.toggleAttribute("controls", Boolean(value)); }
  get open() { return this.hasAttribute("open"); }
  set open(value) { this.toggleAttribute("open", Boolean(value)); }
  get isContentEditable() {
    for (let node = this; node && node.nodeType === 1; node = node.parentNode) {
      const value = node.getAttribute("contenteditable");
      if (value === "" || value === "true") return true;
      if (value === "false") return false;
    }
    return false;
  }
  get type() {
    if (this.localName === "input") return (this.getAttribute("type") ?? "text").toLowerCase();
    if (this.localName === "button") return (this.getAttribute("type") ?? "submit").toLowerCase();
    if (this.localName === "select") return this.hasAttribute("multiple") ? "select-multiple" : "select-one";
    if (this.localName === "textarea") return "textarea";
    return this.getAttribute("type") ?? "";
  }
  set type(value) { this.setAttribute("type", value); }
  get tabIndex() {
    const value = this.getAttribute("tabindex");
    if (value != null && /^-?\d+$/.test(value.trim())) return Number(value);
    return this._focusableByDefault() ? 0 : -1;
  }
  set tabIndex(value) { this.setAttribute("tabindex", String(value)); }
  _focusableByDefault() {
    if (["button", "input", "select", "textarea"].includes(this.localName)) return !this.disabled;
    if (this.localName === "a") return this.hasAttribute("href");
    return false;
  }
  focus() {
    if (!this.isConnected) return;
    if (!this._focusableByDefault() && !this.hasAttribute("tabindex") && !this.isContentEditable) return;
    const document = this.ownerDocument;
    if (document._activeElement === this) return;
    const previous = document._activeElement;
    document._activeElement = this;
    if (previous) previous.dispatchEvent(new FocusEvent("blur"));
    this.dispatchEvent(new FocusEvent("focus"));
    this.dispatchEvent(new FocusEvent("focusin", { bubbles: true }));
  }
  blur() {
    const document = this.ownerDocument;
    if (document._activeElement !== this) return;
    document._activeElement = null;
    this.dispatchEvent(new FocusEvent("blur"));
  }
  click() {
    if (this.disabled) return;
    if (this._clicking) return;
    this._clicking = true;
    try {
      this.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, composed: true, detail: 0, view: this.ownerDocument.defaultView }));
    } finally { this._clicking = false; }
  }

  // Forms: value, checked, select options.
  get value() {
    switch (this.localName) {
      case "input": return this._value ?? this.getAttribute("value") ?? (["checkbox", "radio"].includes(this.type) ? "on" : "");
      case "textarea": return this._value ?? this.textContent;
      case "option": return this.getAttribute("value") ?? this.textContent.replace(/\s+/g, " ").trim();
      case "select": { const option = this.selectedOptions[0]; return option ? option.value : ""; }
      case "button": return this.getAttribute("value") ?? "";
      default: return this.getAttribute("value") ?? "";
    }
  }
  set value(value) {
    const text = value == null ? "" : String(value);
    switch (this.localName) {
      case "input": case "textarea": this._value = text; break;
      case "option": this.setAttribute("value", text); break;
      case "select": for (const option of this.options) option._selected = option.value === text; break;
      default: this.setAttribute("value", text);
    }
  }
  get defaultValue() { return this.getAttribute("value") ?? ""; }
  get checked() { return this._checked ?? this.hasAttribute("checked"); }
  set checked(value) { this._checked = Boolean(value); }
  get defaultChecked() { return this.hasAttribute("checked"); }
  get options() { return list(this._descendants().filter((el) => el.localName === "option")); }
  get selectedOptions() {
    const options = this.options;
    const explicit = options.filter((option) => option._selected ?? option.hasAttribute("selected"));
    if (this.hasAttribute("multiple")) return list(explicit);
    if (explicit.length) return list([explicit[explicit.length - 1]]);
    const first = options.find((option) => !option.disabled);
    return list(first ? [first] : []);
  }
  get selectedIndex() { const selected = this.selectedOptions[0]; return selected ? this.options.indexOf(selected) : -1; }
  set selectedIndex(index) { this.options.forEach((option, i) => { option._selected = i === index; }); }
  get selected() {
    if (this.localName !== "option") return undefined;
    const select = this.closest("select");
    return select ? select.selectedOptions.includes(this) : Boolean(this._selected ?? this.hasAttribute("selected"));
  }
  set selected(value) {
    const select = this.closest("select");
    if (value && select && !select.hasAttribute("multiple")) for (const option of select.options) option._selected = false;
    this._selected = Boolean(value);
  }
  get labels() { return list([]); }
  get control() {
    if (this.localName !== "label") return undefined;
    const target = this.getAttribute("for");
    if (target) return this.ownerDocument.getElementById(target);
    return this._descendants().find((el) => ["input", "select", "textarea", "button"].includes(el.localName)) ?? null;
  }

  // Click activation: checkboxes and radios toggle, labels forward the click.
  get _preActivate() {
    if (this.localName !== "input" || !["checkbox", "radio"].includes(this.type) || this.disabled) return null;
    return () => {
      const old = this.checked;
      const oldIndeterminate = this.indeterminate;
      this.checked = this.type === "radio" ? true : !old;
      this.indeterminate = false;
      return () => { this.checked = old; this.indeterminate = oldIndeterminate; };
    };
  }
  get _activate() {
    if (this.localName === "input" && ["checkbox", "radio"].includes(this.type)) {
      return () => {
        this.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
        this.dispatchEvent(new Event("change", { bubbles: true }));
      };
    }
    if (this.localName === "label") {
      return (event) => {
        const control = this.control;
        if (control && !event._path.includes(control)) control.click();
      };
    }
    return null;
  }
}

// Obsidian is a browser: these names exist and answer to instanceof.
class HTMLElement extends Element {}
class SVGElement extends Element {}

/* ----------------------------------------------------------------- document */

class TreeWalker {
  constructor(root, whatToShow = 0xffffffff, filter = null) {
    this.root = root;
    this.whatToShow = whatToShow;
    this.filter = filter;
    this.currentNode = root;
  }
  _accept(node) {
    const bit = 1 << (node.nodeType - 1);
    if (!(this.whatToShow & bit)) return 3;
    if (!this.filter) return 1;
    return typeof this.filter === "function" ? this.filter(node) : this.filter.acceptNode(node);
  }
  nextNode() {
    let node = this.currentNode;
    let result = 1;
    for (;;) {
      if (result !== 2 && node._children.length) {
        node = node._children[0];
      } else {
        let next = null;
        for (let at = node; at && at !== this.root; at = at.parentNode) {
          if (at.nextSibling) { next = at.nextSibling; break; }
        }
        if (!next) return null;
        node = next;
      }
      result = this._accept(node);
      if (result === 1) { this.currentNode = node; return node; }
    }
  }
}

class Document extends ParentNode {
  constructor() {
    super(null);
    this.ownerDocument = null;
    this.defaultView = null;
    this._activeElement = null;
    this.documentElement = this.createElement("html");
    this.head = this.createElement("head");
    this.body = this.createElement("body");
    this.documentElement.append(this.head, this.body);
    this.appendChild(this.documentElement);
  }
  get nodeType() { return 9; }
  get nodeName() { return "#document"; }
  get activeElement() { return this._activeElement && this._activeElement.isConnected ? this._activeElement : this.body; }
  _parentForEvent() { return this.defaultView; }
  createElement(name) { return this.createElementNS(HTML_NS, String(name).toLowerCase()); }
  createElementNS(namespace, name) {
    const html = !namespace || namespace === HTML_NS;
    return html ? new HTMLElement(this, String(name).toLowerCase(), HTML_NS) : new SVGElement(this, String(name), namespace);
  }
  createTextNode(data) { return new Text(this, data); }
  createComment(data) { return new Comment(this, data); }
  createDocumentFragment() { return new DocumentFragment(this); }
  createTreeWalker(root, whatToShow, filter) { return new TreeWalker(root, whatToShow, filter); }
  createEvent() { return new Event(""); }
  getElementById(id) { return this._descendants().find((el) => el.id === id) ?? null; }
  getSelection() { return this.defaultView?.getSelection() ?? null; }
  elementFromPoint() { return null; }
  hasFocus() { return true; }
}

/* ---------------------------------------------------------------- selectors */

function parseSelector(text) {
  const source = String(text);
  if (parseSelector.cache.has(source)) return parseSelector.cache.get(source);
  let i = 0;
  const peek = () => source[i];
  const ident = () => {
    const start = i;
    while (i < source.length && /[\w\- -￿\\]/.test(source[i])) { if (source[i] === "\\") i += 1; i += 1; }
    if (start === i) throw new SyntaxError(`bad selector: ${source}`);
    return source.slice(start, i).replace(/\\(.)/g, "$1");
  };
  const quoted = () => {
    const quote = source[i]; i += 1;
    let value = "";
    while (i < source.length && source[i] !== quote) { if (source[i] === "\\") i += 1; value += source[i]; i += 1; }
    i += 1;
    return value;
  };
  const skip = () => { while (/\s/.test(peek() ?? "")) i += 1; };
  const compound = () => {
    const parts = [];
    for (;;) {
      const c = peek();
      if (c === "*") { i += 1; parts.push({ kind: "any" }); }
      else if (c === "#") { i += 1; parts.push({ kind: "id", value: ident() }); }
      else if (c === ".") { i += 1; parts.push({ kind: "class", value: ident() }); }
      else if (c === "[") {
        i += 1; skip();
        const name = ident().toLowerCase(); skip();
        let op = null, value = null, flag = "";
        if (peek() !== "]") {
          op = source[i] === "=" ? "=" : source.slice(i, i + 2); i += op.length; skip();
          value = peek() === '"' || peek() === "'" ? quoted() : ident(); skip();
          if (/[iIsS]/.test(peek() ?? "")) { flag = source[i].toLowerCase(); i += 1; skip(); }
        }
        if (peek() !== "]") throw new SyntaxError(`bad selector: ${source}`);
        i += 1;
        parts.push({ kind: "attr", name, op, value, flag });
      } else if (c === ":") {
        i += 1;
        if (peek() === ":") i += 1;
        const name = ident().toLowerCase();
        let arg = null;
        if (peek() === "(") {
          let depth = 0; const start = i + 1;
          for (; i < source.length; i += 1) { if (source[i] === "(") depth += 1; else if (source[i] === ")") { depth -= 1; if (!depth) break; } }
          arg = source.slice(start, i); i += 1;
        }
        parts.push({ kind: "pseudo", name, arg: name === "not" || name === "is" || name === "where" || name === "has" ? parseSelector(arg) : arg });
      } else if (c && /[\w\- -￿\\]/.test(c)) parts.push({ kind: "tag", value: ident().toLowerCase() });
      else break;
    }
    if (!parts.length) throw new SyntaxError(`bad selector: ${source}`);
    return parts;
  };
  const groups = [];
  let current = [];
  skip();
  while (i < source.length) {
    current.push({ combinator: current.length ? pendingCombinator : null, parts: compound() });
    const before = i; skip();
    const c = peek();
    if (c === ",") { i += 1; skip(); groups.push(current); current = []; continue; }
    if (c === ">" || c === "+" || c === "~") { pendingCombinator = c; i += 1; skip(); continue; }
    if (i >= source.length) break;
    if (i > before) { pendingCombinator = " "; continue; }
    throw new SyntaxError(`bad selector: ${source}`);
  }
  if (!current.length) throw new SyntaxError(`bad selector: ${source}`);
  groups.push(current);
  parseSelector.cache.set(source, groups);
  return groups;
}
let pendingCombinator = " ";
parseSelector.cache = new Map();

function matchCompound(element, parts, scope) {
  for (const part of parts) {
    switch (part.kind) {
      case "any": break;
      case "tag": if (element.localName.toLowerCase() !== part.value) return false; break;
      case "id": if (element.id !== part.value) return false; break;
      case "class": if (!element.classList.contains(part.value)) return false; break;
      case "attr": {
        const actual = element.getAttribute(part.name);
        if (actual == null) return false;
        if (!part.op) break;
        const a = part.flag === "i" ? actual.toLowerCase() : actual;
        const v = part.flag === "i" ? part.value.toLowerCase() : part.value;
        const ok = {
          "=": () => a === v,
          "^=": () => v !== "" && a.startsWith(v),
          "$=": () => v !== "" && a.endsWith(v),
          "*=": () => v !== "" && a.includes(v),
          "~=": () => a.split(/\s+/).includes(v),
          "|=": () => a === v || a.startsWith(`${v}-`),
        }[part.op];
        if (!ok || !ok()) return false;
        break;
      }
      case "pseudo": if (!matchPseudo(element, part, scope)) return false; break;
      default: return false;
    }
  }
  return true;
}

function matchPseudo(element, { name, arg }, scope) {
  const siblings = () => (element.parentNode ? element.parentNode._children.filter((child) => child.nodeType === 1) : [element]);
  switch (name) {
    case "first-child": return siblings()[0] === element;
    case "last-child": return siblings().at(-1) === element;
    case "only-child": return siblings().length === 1;
    case "first-of-type": return siblings().find((el) => el.localName === element.localName) === element;
    case "last-of-type": return siblings().filter((el) => el.localName === element.localName).at(-1) === element;
    case "nth-child": return nth(arg, siblings().indexOf(element) + 1);
    case "nth-of-type": return nth(arg, siblings().filter((el) => el.localName === element.localName).indexOf(element) + 1);
    case "not": return !arg.some((group) => matchComplex(element, group, scope));
    case "is": case "where": return arg.some((group) => matchComplex(element, group, scope));
    case "has": return element._descendants().some((el) => arg.some((group) => matchComplex(el, group, element)));
    case "scope": return scope ? element === scope : element === element.ownerDocument.documentElement;
    case "root": return element === element.ownerDocument.documentElement;
    case "empty": return !element._children.some((child) => child.nodeType === 1 || (child.nodeType === 3 && child.data));
    case "checked": return element.localName === "option" ? element.selected : Boolean(element.checked) && element.localName === "input";
    case "disabled": return element.disabled;
    case "enabled": return FORM_CONTROLS.has(element.localName) && !element.disabled;
    case "focus": return element.ownerDocument.activeElement === element;
    case "hover": case "active": case "focus-visible": case "focus-within": return false;
    default: throw new SyntaxError(`unsupported pseudo-class :${name}`);
  }
}

function nth(expression, index) {
  const text = String(expression).replace(/\s+/g, "").toLowerCase();
  if (text === "odd") return index % 2 === 1;
  if (text === "even") return index % 2 === 0;
  const match = /^([+-]?\d*)n([+-]\d+)?$/.exec(text);
  if (!match) return index === Number(text);
  const a = match[1] === "" || match[1] === "+" ? 1 : match[1] === "-" ? -1 : Number(match[1]);
  const b = Number(match[2] ?? 0);
  if (a === 0) return index === b;
  return (index - b) / a >= 0 && (index - b) % a === 0;
}

// Right to left: the last compound matches the element, then combinators
// walk to ancestors or earlier siblings.  `scope` bounds :scope only.
function matchComplex(element, compounds, scope) {
  const step = (el, index) => {
    if (!matchCompound(el, compounds[index].parts, scope)) return false;
    if (index === 0) return true;
    const combinator = compounds[index].combinator;
    if (combinator === ">") { const parent = el.parentElement; return Boolean(parent) && step(parent, index - 1); }
    if (combinator === " ") { for (let parent = el.parentElement; parent; parent = parent.parentElement) if (step(parent, index - 1)) return true; return false; }
    if (combinator === "+") { const previous = el.previousElementSibling; return Boolean(previous) && step(previous, index - 1); }
    if (combinator === "~") { for (let previous = el.previousElementSibling; previous; previous = previous.previousElementSibling) if (step(previous, index - 1)) return true; return false; }
    return false;
  };
  return step(element, compounds.length - 1);
}

/* --------------------------------------------------------------------- HTML */

const ENTITIES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ", mdash: "—", ndash: "–", hellip: "…", laquo: "«", raquo: "»", copy: "©" };
const decode = (text) => text.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (match, name) => {
  if (name[0] === "#") return String.fromCodePoint(name[1].toLowerCase() === "x" ? parseInt(name.slice(2), 16) : Number(name.slice(1)));
  return ENTITIES[name.toLowerCase()] ?? match;
});
const escapeText = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/ /g, "&nbsp;");
const escapeAttr = (text) => text.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/ /g, "&nbsp;");

function parseHTML(document, html, parent) {
  const stack = [parent];
  const top = () => stack[stack.length - 1];
  const tagRe = /<!--([\s\S]*?)-->|<!(?:doctype|DOCTYPE)[^>]*>|<\/([a-zA-Z][\w:-]*)\s*>|<([a-zA-Z][\w:-]*)((?:\s+[^\s"'>/=]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'=<>`]+))?)*)\s*(\/?)>/g;
  let last = 0;
  let match;
  const text = (value) => { if (value) top().appendChild(document.createTextNode(decode(value))); };
  while ((match = tagRe.exec(html))) {
    text(html.slice(last, match.index));
    last = tagRe.lastIndex;
    if (match[1] !== undefined) { top().appendChild(document.createComment(match[1])); continue; }
    if (match[2]) {
      const name = match[2].toLowerCase();
      for (let i = stack.length - 1; i > 0; i -= 1) {
        if (stack[i].localName === name) { stack.length = i; break; }
      }
      continue;
    }
    if (!match[3]) continue;
    const name = match[3].toLowerCase();
    if (CLOSES_P.has(name)) {
      for (let i = stack.length - 1; i > 0; i -= 1) {
        if (stack[i].localName === "p") { stack.length = i; break; }
        if (!["span", "a", "em", "strong", "b", "i", "code", "sup", "sub", "mark"].includes(stack[i].localName)) break;
      }
    }
    if ((name === "li" || name === "td" || name === "th" || name === "tr" || name === "option") && top().localName === name) stack.pop();
    const element = name === "svg" || top().namespaceURI === "http://www.w3.org/2000/svg"
      ? document.createElementNS("http://www.w3.org/2000/svg", match[3]) : document.createElement(name);
    const attrRe = /([^\s"'>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;
    let attr;
    while ((attr = attrRe.exec(match[4] ?? ""))) element.setAttribute(attr[1], decode(attr[2] ?? attr[3] ?? attr[4] ?? ""));
    top().appendChild(element);
    if (RAW_TEXT.has(name)) {
      const end = html.toLowerCase().indexOf(`</${name}`, last);
      const body = html.slice(last, end < 0 ? html.length : end);
      if (body) element.appendChild(document.createTextNode(name === "textarea" || name === "title" ? decode(body) : body));
      const close = end < 0 ? html.length : html.indexOf(">", end) + 1;
      tagRe.lastIndex = last = close;
      continue;
    }
    if (!VOID.has(name) && !match[5]) stack.push(element);
  }
  text(html.slice(last));
  return parent;
}

function serialize(node) {
  if (node.nodeType === 3) {
    const parent = node.parentNode?.localName;
    return parent && RAW_TEXT.has(parent) && parent !== "textarea" && parent !== "title" ? node.data : escapeText(node.data);
  }
  if (node.nodeType === 8) return `<!--${node.data}-->`;
  if (node.nodeType === 11) return node._children.map(serialize).join("");
  const attrs = node.getAttributeNames().map((name) => ` ${name}="${escapeAttr(node.getAttribute(name))}"`).join("");
  const name = node.namespaceURI === HTML_NS ? node.localName : node.tagName;
  if (VOID.has(node.localName) && node.namespaceURI === HTML_NS) return `<${name}${attrs}>`;
  return `<${name}${attrs}>${node._children.map(serialize).join("")}</${name}>`;
}

/* ------------------------------------------------------------------- window */

class Window extends EventTarget {
  constructor() {
    super();
    this.document = new Document();
    this.document.defaultView = this;
    this.window = this;
    this.self = this;
    this.innerWidth = 1024;
    this.innerHeight = 768;
    this.devicePixelRatio = 1;
    Object.assign(this, {
      Node, Text, Comment, Element, HTMLElement, SVGElement, Document, DocumentFragment, NodeList,
      Event, UIEvent, KeyboardEvent, MouseEvent, PointerEvent, FocusEvent, InputEvent, CustomEvent, EventTarget,
      TreeWalker, NodeFilter: { SHOW_ALL: 0xffffffff, SHOW_ELEMENT: 1, SHOW_TEXT: 4, SHOW_COMMENT: 128, FILTER_ACCEPT: 1, FILTER_REJECT: 2, FILTER_SKIP: 3 },
      setTimeout, clearTimeout, setInterval, clearInterval, queueMicrotask, console,
    });
  }
  getComputedStyle(element) {
    const style = makeStyle();
    if (element?._style) style.cssText = element._style.cssText;
    if (!style.getPropertyValue("display")) style.setProperty("display", element?.hidden ? "none" : "block");
    return style;
  }
  getSelection() {
    return { rangeCount: 0, isCollapsed: true, toString: () => "", removeAllRanges() {}, addRange() {}, getRangeAt() { return null; } };
  }
  matchMedia(query) { return { matches: false, media: query, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }; }
  requestAnimationFrame(callback) { return setTimeout(() => callback(Date.now()), 0); }
  cancelAnimationFrame(handle) { clearTimeout(handle); }
  scrollTo() {}
  focus() {}
  blur() {}
}

function createWindow() { return new Window(); }

module.exports = {
  createWindow, Window, Document, Node, Element, HTMLElement, Text, Comment, DocumentFragment,
  Event, KeyboardEvent, MouseEvent, PointerEvent, CustomEvent, parseHTML, serialize, parseSelector,
};
