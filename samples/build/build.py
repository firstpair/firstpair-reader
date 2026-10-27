"""Build the Reader sample vaults (shelf, single-book, library, code-book)
from texts.py and segmented.json.  The Triptych sample has its own builder,
build_triptych.py.

    python3 samples/build/build.py

Standard library only.  Each sample folder is rewritten in place: files the
build produces are written when they change, and files an earlier build
wrote but this one no longer produces (build/manifest.json) are removed.
Nothing else is touched, so `.obsidian/` (where a plugin is installed) and
anything added by hand survive.  Rerun segment.py first if a Chinese text in texts.py changed.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLES = HERE.parent
sys.path.insert(0, str(HERE))
import texts  # noqa: E402
import code_book  # noqa: E402

SEGMENTED = json.loads((HERE / "segmented.json").read_text(encoding="utf-8"))
OPEN_READER = "**[Open the Reader](firstpair:reader)**"
MANIFEST = HERE / "manifest.json"


# ------------------------------------------------------------------ output

class Vault:
    """The files of one sample vault, written together."""

    def __init__(self, name):
        self.root = SAMPLES / name
        self.files = {}

    def add(self, path, content):
        if path in self.files:
            raise SystemExit(f"{self.root.name}: {path} written twice")
        self.files[path] = content if isinstance(content, str) else dump(content)

    def write(self):
        written = 0
        for path, content in self.files.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                target.write_text(content, encoding="utf-8")
                written += 1
        # Remove only what an earlier build wrote and this one no longer
        # does (listed in build/manifest.json); anything else in the folder
        # is left alone.
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
        removed = 0
        for relative in sorted(set(manifest.get(self.root.name, [])) - set(self.files)):
            target = self.root / relative
            if target.is_file():
                target.unlink()
                removed += 1
            parent = target.parent
            while parent != self.root and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        manifest[self.root.name] = sorted(self.files)
        MANIFEST.write_text(dump(dict(sorted(manifest.items()))), encoding="utf-8")
        print(f"{self.root.name}: {len(self.files)} files ({written} written, {removed} removed)")


def dump(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def at(folder, path):
    return f"{folder}/{path}" if folder else path


def link(path, label=None):
    path = re.sub(r"\.md$", "", path)
    return f"[[{path}|{label}]]" if label else f"[[{path}]]"


def is_punct(token):
    return all(unicodedata.category(ch)[0] in "PSZ" for ch in token)


# ----------------------------------------------------------- aligned books

def glossed(words, glosses, where):
    """[text, reading, gloss] per word; glosses skip punctuation."""
    items = [item.strip() for item in glosses.split(" / ")]
    content = [word for word, _ in words if not is_punct(word)]
    if len(items) != len(content):
        pairs = "\n".join(f"  {w} = {g}" for w, g in zip(content, items + ["?"] * len(content)))
        raise SystemExit(f"{where}: {len(content)} words but {len(items)} glosses\n{pairs}")
    it = iter(items)
    return [[word, reading, "" if is_punct(word) else next(it)] for word, reading in words]


def source_text(words):
    return "".join(word for word, _ in words)


def lines(text):
    return text.split("\n")


def aligned_book(vault, folder, meta, pages, aligned, ui):
    """An aligned firstpair-reader.v2 book with its static Markdown notes.

    pages: [{id, title, part, units: [{id, kind?, source, translations,
    words, glosses?}]}].  ui: strings for the static notes.
    """
    data = at(folder, "_data")
    book = at(folder, "Book")
    index = {
        "schema": "firstpair-reader.v2",
        "title": meta["title"],
        "author": meta.get("author"),
        "subtitle": meta.get("subtitle"),
        "lang": meta["lang"],
        "ui_lang": meta["ui_lang"],
        "launcher": at(folder, "Home.md"),
        "contents": f"{book}/Contents.md",
        "parts": [{"id": part["id"], "title": part["title"], "note": f"{book}/{part['note']}.md"}
                  for part in meta["parts"]],
        "pages": [{"id": page["id"], "title": page["title"], "part": page["part"],
                   "chapter": f"{data}/pages/{page['id']}.json"} for page in pages],
        "aligned": aligned,
    }
    index = {key: value for key, value in index.items() if value is not None}
    vault.add(f"{data}/reader.json", index)
    for page in pages:
        vault.add(f"{data}/pages/{page['id']}.json", {
            "schema": "firstpair-aligned-chapter-v1",
            "id": page["id"],
            "title": page["title"],
            "units": page["units"],
        })

    lead = aligned["translations"][0]["id"]
    vault.add(at(folder, "Home.md"), "\n".join([
        f"# {meta['title']}", "",
        OPEN_READER, "",
        *([f"*{meta['author']}*", ""] if meta.get("author") else []),
        *([meta["subtitle"], ""] if meta.get("subtitle") else []),
        *ui["home"], "",
        f"{ui['contents']}: {link(index['contents'], ui['contents'])}", "",
    ]))
    contents = [f"# {meta['title']}", "", OPEN_READER, ""]
    for part in meta["parts"]:
        contents.append(f"## {link(f'{book}/' + part['note'], part['title'])}")
        contents.append("")
        for page in pages:
            if page["part"] == part["id"]:
                contents.append(f"- {page['title']}")
        contents.append("")
    vault.add(f"{book}/Contents.md", "\n".join(contents))
    for part in meta["parts"]:
        body = [f"# {part['title']}", "",
                f"{ui['up']}: {link(index['contents'], ui['contents'])}", ""]
        for page in pages:
            if page["part"] != part["id"]:
                continue
            body += [f"## {page['title']}", ""]
            for unit in page["units"]:
                text = unit["translations"].get(lead, [])
                if unit.get("kind") in ("heading", "cover"):
                    body += [f"### {' '.join(text)}", ""]
                else:
                    body += ["  \n".join(text), ""]
        vault.add(f"{book}/{part['note']}.md", "\n".join(body))


UI_EN = {"contents": "Contents", "up": "Up",
         "home": ["Without the plugin, read the book from its contents below; "
                  "with it, the notes open the Reader at the same place."]}
UI_RU = {"contents": "Содержание", "up": "Вверх",
         "home": ["Без плагина книгу можно читать по оглавлению ниже; "
                  "с плагином заметки открывают Reader на том же месте."]}


def luxun_book(vault, folder):
    meta = dict(texts.LUXUN, lang="en", ui_lang="en")
    pages = []
    number = 0
    for page, segmented in zip(texts.LUXUN["pages"], SEGMENTED["luxun"]):
        units = []
        for unit, words in zip(page["units"], segmented):
            number += 1
            if source_text(words) != unit["zh"]:
                raise SystemExit(f"segmented.json is stale for {unit['zh'][:12]}…; rerun segment.py")
            row = {"id": f"b{number:04d}"}
            if unit.get("kind"):
                row["kind"] = unit["kind"]
            row["source"] = [unit["zh"]]
            row["translations"] = {"en": lines(unit["en"])}
            row["words"] = glossed(words, unit["gloss_en"], f"Lu Xun {page['id']} b{number:04d}")
            units.append(row)
        pages.append({**page, "units": units})
    aligned = {
        "schema": "firstpair-parallel-reader-v1",
        "title": meta["title"],
        "unit": "paragraph",
        "sourceLanguage": {"id": "zh", "lang": "zh", "label": "中文", "position": "left",
                           "optional": True, "defaultVisible": False},
        "translations": [{"id": "en", "lang": "en", "label": "English",
                          "title": "Sample translation", "defaultVisible": True}],
        "interlinear": {"layers": ["pinyin", "gloss"], "glossLang": "en"},
    }
    aligned_book(vault, folder, meta, pages, aligned, UI_EN)


def analects_book(vault, folder):
    meta = dict(texts.ANALECTS, lang="ru", ui_lang="ru")
    pages = []
    number = 0
    for page, segmented in zip(texts.ANALECTS["pages"], SEGMENTED["analects"]):
        units = []
        for unit, words in zip(page["units"], segmented):
            number += 1
            where = f"Analects {page['id']} b{number:04d}"
            row = {"id": f"b{number:04d}"}
            if unit.get("kind"):
                row["kind"] = unit["kind"]
            row["source"] = [source_text(words)]
            row["translations"] = {"ru": lines(unit["ru"]), "en": lines(unit["en"])}
            row["words"] = glossed(words, unit["gloss_ru"], where)
            row["glosses"] = {"en": [w[2] for w in glossed(words, unit["gloss_en"], where)]}
            units.append(row)
        pages.append({**page, "units": units})
    aligned = {
        "schema": "firstpair-parallel-reader-v1",
        "title": meta["title"],
        "unit": "paragraph",
        "sourceLanguage": {"id": "zh", "lang": "zh", "label": "中文", "position": "left"},
        "translations": [
            {"id": "ru", "lang": "ru", "label": "Русский", "title": "Учебный перевод", "defaultVisible": True},
            {"id": "en", "lang": "en", "label": "English", "title": "Sample translation", "defaultVisible": False},
        ],
        "interlinear": {"layers": ["pinyin", "gloss"], "glossLang": "ru"},
    }
    aligned_book(vault, folder, meta, pages, aligned, UI_RU)


def daodejing_pages():
    pages = []
    number = 0
    for chapter_index, (chapter, segmented) in enumerate(zip(texts.DAODEJING, SEGMENTED["daodejing"])):
        heading_words, *unit_words = segmented
        number += 1
        title = chapter["zh_title"]
        units = [{
            "id": f"b{number:04d}", "kind": "heading", "source": [title],
            "translations": {"en": [chapter["title"]], "legge": [f"Chapter {chapter_index + 1}"]},
            "words": glossed(heading_words, texts.DAODEJING_HEADING_GLOSS[title], title),
        }]
        for unit_index, (unit, words) in enumerate(zip(chapter["units"], unit_words)):
            number += 1
            units.append({
                "id": f"b{number:04d}",
                "source": [source_text(words)],
                "translations": {
                    "en": lines(texts.DAODEJING_EN[chapter_index][unit_index]),
                    "legge": lines(texts.DAODEJING_LEGGE[chapter_index][unit_index]),
                },
                "words": glossed(words, unit["gloss_en"], f"{title} unit {unit_index + 1}"),
            })
        pages.append({"id": chapter["id"], "title": chapter["title"], "part": "P01", "units": units})
    return pages


def daodejing_book(vault, folder):
    meta = {
        "title": "Dao De Jing, chapters 1–3",
        "author": "Laozi (老子)",
        "subtitle": "道德经 · the Wang Bi text · two English translations",
        "lang": "en", "ui_lang": "en",
        "parts": [{"id": "P01", "title": "The Way (chapters 1–3)", "note": "01 The Way"}],
    }
    aligned = {
        "schema": "firstpair-parallel-reader-v1",
        "title": meta["title"],
        "unit": "paragraph",
        "sourceLanguage": {"id": "zh", "lang": "zh", "label": "中文", "position": "left"},
        "translations": [
            {"id": "en", "lang": "en", "label": "English", "title": "Sample translation (2026)",
             "default": True, "defaultVisible": True},
            {"id": "legge", "lang": "en", "label": "English", "title": "James Legge (1891)",
             "defaultVisible": True},
        ],
        "interlinear": {"layers": ["pinyin", "gloss"], "glossLang": "en"},
    }
    aligned_book(vault, folder, meta, daodejing_pages(), aligned, UI_EN)


# ------------------------------------------------- plain book with markers

def gettysburg_book(vault, folder):
    data = at(folder, "_data")
    note = at(folder, "Book/Address.md")
    titles = ["Four score and seven years ago", "Now we are engaged", "But, in a larger sense"]
    pages = [{"id": f"p{i + 1:03d}", "title": title, "part": "P01", "note": note,
              "marker": {"start": f"<!-- page:p{i + 1:03d} -->", "end": f"<!-- /page:p{i + 1:03d} -->"}}
             for i, title in enumerate(titles)]
    vault.add(f"{data}/reader.json", {
        "schema": "firstpair-reader.v2",
        "title": "The Gettysburg Address",
        "author": "Abraham Lincoln",
        "subtitle": "November 19, 1863 · the Bliss copy",
        "lang": "en",
        "ui_lang": "en",
        "launcher": at(folder, "Home.md"),
        "contents": at(folder, "Book/Contents.md"),
        "parts": [{"id": "P01", "title": "The Address", "note": note}],
        "pages": pages,
    })
    body = ["# The Gettysburg Address", "", f"Up: {link(at(folder, 'Book/Contents'), 'Contents')}", ""]
    for page, paragraph in zip(pages, texts.GETTYSBURG):
        body += [page["marker"]["start"], paragraph, page["marker"]["end"], ""]
    body += ["*Abraham Lincoln, November 19, 1863.*", ""]
    vault.add(note, "\n".join(body))
    vault.add(at(folder, "Book/Contents.md"), "\n".join([
        "# The Gettysburg Address", "", OPEN_READER, "",
        f"## {link(note, 'The Address')}", "", *[f"- {title}" for title in titles], "",
    ]))
    vault.add(at(folder, "Home.md"), "\n".join([
        "# The Gettysburg Address", "", OPEN_READER, "", "*Abraham Lincoln*", "",
        "A plain English book: one Markdown note holds the whole text, and the Reader cuts "
        "its pages out of it at the `<!-- page:… -->` markers.", "",
        f"Contents: {link(at(folder, 'Book/Contents'), 'Contents')}", "",
    ]))


# ------------------------------------------------------------------ shelf

def build_shelf():
    vault = Vault("shelf")
    books = [
        ("Analects", analects_book, "Лунь юй · Беседы и суждения", "Chinese → Russian and English, "
         "Russian interface, glosses in Russian and English"),
        ("Diary of a Madman", luxun_book, "A Madman's Diary", "Chinese → English, the Chinese a "
         "study column you switch on, pinyin and English glosses"),
        ("Gettysburg Address", gettysburg_book, "The Gettysburg Address", "a plain English book "
         "cut into pages from one note"),
    ]
    for folder, make, _title, _note in books:
        make(vault, folder)
    vault.add("Home.md", "\n".join([
        "# A small shelf", "", OPEN_READER, "",
        "Three books, each in its own folder with its own `_data/reader.json`. "
        "The Reader opens on a shelf listing them; each book keeps its own place.", "",
        *[f"- {link(f'{folder}/Home', title)}: {note}" for folder, _m, title, note in books], "",
    ]))
    vault.write()


def build_single_book():
    vault = Vault("single-book")
    daodejing_book(vault, "")
    vault.write()


# ---------------------------------------------------------------- library

def build_library():
    vault = Vault("library")
    editions = [
        ("sample", "Sample translation", "2026", "English translations", "Sample translation",
         texts.DAODEJING_EN),
        ("legge", "James Legge", "1891", "English translations", "Legge", texts.DAODEJING_LEGGE),
        ("wangbi", "道德经 (Wang Bi text)", "c. 240", "Original", "Original",
         [[source_text(words) for words in chapter[1:]] for chapter in SEGMENTED["daodejing"]]),
    ]
    library = {
        "schema_version": 1,
        "title": "Dao De Jing · three editions",
        "launcher": "Home",
        "editions": [],
        "anthology": "Sources/Chapter 1 in three editions",
        "sources": [{"id": "about", "title": "About the texts", "note": "Sources/About the texts"}],
    }
    for edition_id, title, version, family, folder, chapters in editions:
        library["editions"].append({
            "id": edition_id, "title": title, "version": version, "family": family,
            "data": f"_data/editions/{edition_id}.json", "note": f"{folder}/Contents",
        })
        part_note = f"{folder}/Chapters 1–3"
        pages = []
        body = [f"# {title}: chapters 1–3", "", f"Up: {link(f'{folder}/Contents', 'Contents')}", ""]
        for index, paragraphs in enumerate(chapters):
            page_id = f"c{index + 1:02d}"
            heading = (texts.DAODEJING[index]["zh_title"] if edition_id == "wangbi"
                       else f"Chapter {index + 1}")
            pages.append({"id": page_id, "title": heading, "part_id": "P01", "note": part_note})
            body += [f"<!-- lmr-page-start:{page_id} -->", f"## {heading}", ""]
            for paragraph in paragraphs:
                body += ["  \n".join(lines(paragraph)), ""]
            body += [f"<!-- lmr-page-end:{page_id} -->", ""]
        vault.add(f"{part_note}.md", "\n".join(body))
        vault.add(f"_data/editions/{edition_id}.json", {
            "title": title,
            "start_page": "c01",
            "parts": [{"id": "P01", "title": "Chapters 1–3", "note": part_note}],
            "pages": pages,
        })
        vault.add(f"{folder}/Contents.md", "\n".join([
            f"# {title}", "", OPEN_READER, "",
            f"- {link(part_note, 'Chapters 1–3')}", "",
        ]))
    vault.add("_data/mobile-library.json", library)
    vault.add("Home.md", "\n".join([
        "# Dao De Jing · three editions", "", OPEN_READER, "",
        "A library: one vault, several editions of the same chapters, grouped by family. "
        "Each edition's pages are cut from its Part note at the `lmr-page` markers.", "",
        *[f"- {link(f'{folder}/Contents', title)} ({version})"
          for _id, title, version, _family, folder, _c in editions],
        f"- {link('Sources/About the texts', 'About the texts')}", "",
    ]))
    vault.add("Sources/About the texts.md", "\n".join([
        "# About the texts", "",
        "- **Original**: chapters 1–3 of the *Dao De Jing* in the received text with Wang Bi's "
        "commentary (third century), in simplified characters; public domain.",
        "- **James Legge**: *The Texts of Taoism*, Sacred Books of the East, vol. 39 (Oxford, 1891); "
        "public domain. His parenthetical additions are kept.",
        "- **Sample translation**: written for these samples and released with them under the MIT "
        "licence.", "",
    ]))
    rows = ["# Chapter 1 in three editions", "", "| 道德经 | Legge (1891) | Sample (2026) |", "| --- | --- | --- |"]
    for zh, legge, mine in zip(editions[2][5][0], texts.DAODEJING_LEGGE[0], texts.DAODEJING_EN[0]):
        rows.append(f"| {zh} | {legge.replace(chr(10), '<br>')} | {mine} |")
    vault.add("Sources/Chapter 1 in three editions.md", "\n".join(rows) + "\n")
    vault.write()


# -------------------------------------------------------------- code book

def build_code_book():
    vault = Vault("code-book")
    code_book.build(vault, link)
    vault.write()


def main():
    build_shelf()
    build_single_book()
    build_library()
    build_code_book()


if __name__ == "__main__":
    main()
