"""The code-book sample: a short book about tone_marks.py.

A code book is a folder with `_data/fragments.json` beside `Chapters/`.
Chapters cite the program through ```firstpair-fragment blocks; the Reader
turns each into a card that shows the numbered lines or opens the code
note with those lines marked.  Line numbers are found here, so the book
stays right when the program changes.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FOLDER = "Tone Marks"
SOURCE = (HERE / "tone_marks.py").read_text(encoding="utf-8")
CODE_NOTE = f"{FOLDER}/Code/tone_marks"


def top_level_ranges(source):
    """{symbol: (start, end)} for each top-level def, assignment, or block."""
    rows = source.split("\n")
    starts = []
    for number, line in enumerate(rows, 1):
        if line and not line[0].isspace() and not line.startswith(("import", "from", '"""', ")", "}")):
            name = line.split("(")[0].split(" =")[0].replace("def ", "").rstrip(":")
            if line.startswith("if __name__"):
                name = "main"
            starts.append((name, number))
    ranges = {}
    for index, (name, start) in enumerate(starts):
        end = (starts[index + 1][1] - 1) if index + 1 < len(starts) else len(rows)
        while end > start and not rows[end - 1].strip():
            end -= 1
        ranges[name] = (start, end)
    return ranges


FRAGMENTS = [
    ("convert", "Convert a whole line: every numbered syllable is replaced in place."),
    ("main", "Read standard input line by line and print each line converted."),
    ("MARKS", "The four marked forms of each vowel, in tone order."),
    ("mark_vowel", "The placement rule: a or e if present, the o of ou, else the last vowel."),
    ("SYLLABLE", "A syllable is letters (with ü or u: or v) followed by a tone digit."),
    ("convert_syllable", "Normalise ü, find the vowel, and put the mark on it; tone 5 is unmarked."),
]

CHAPTERS = [
    ("01 What it does", [
        "# What it does", "",
        "`tone_marks.py` reads pinyin with tone numbers, as typed on a keyboard without "
        "accents, and writes it with tone marks: `ni3 hao3` becomes `nǐ hǎo`, and "
        "`xue2 er2 shi2 xi2 zhi1` becomes `xué ér shí xí zhī`.", "",
        "The whole program is one substitution over the line:", "",
        "{convert}", "",
        "and a loop over standard input:", "",
        "{main}", "",
        "Try it: `echo 'Dao4 ke3 dao4' | python3 tone_marks.py`.", "",
    ]),
    ("02 Where the mark goes", [
        "# Where the mark goes", "",
        "Each vowel has four marked forms, one per tone:", "",
        "{MARKS}", "",
        "Which vowel of a syllable takes the mark follows one rule of thumb: *a* or *e* "
        "whenever present; in *ou*, the *o*; otherwise the last vowel (so *liú*, *guì*).", "",
        "{mark_vowel}", "",
    ]),
    ("03 One syllable at a time", [
        "# One syllable at a time", "",
        "A syllable is a run of letters followed by a digit from 1 to 5. `ü` may be typed "
        "as `u:` or `v`.", "",
        "{SYLLABLE}", "",
        "Each match is rewritten on its own; the fifth (neutral) tone keeps its letters "
        "and loses the digit.", "",
        "{convert_syllable}", "",
    ]),
]


def build(vault, link):
    ranges = top_level_ranges(SOURCE)
    rows = []
    for symbol, summary in FRAGMENTS:
        start, end = ranges[symbol]
        rows.append({
            "id": symbol, "symbol": symbol, "source_path": "tone_marks.py",
            "code_note": CODE_NOTE, "start_line": start, "end_line": end, "summary": summary,
        })
    vault.add(f"{FOLDER}/_data/fragments.json", {"fragments": rows})
    vault.add(f"{CODE_NOTE}.md", "\n".join([
        "# tone_marks.py", "",
        f"Up: {link(f'{FOLDER}/Book', 'Tone Marks')}", "",
        "## Full Source", "",
        "```python", SOURCE.rstrip("\n"), "```", "",
    ]))
    for name, body in CHAPTERS:
        text = "\n".join(body)
        for symbol, _summary in FRAGMENTS:
            block = "```firstpair-fragment\n" + json.dumps({"id": symbol}) + "\n```"
            text = text.replace("{" + symbol + "}", block)
        vault.add(f"{FOLDER}/Chapters/{name}.md", text)
    vault.add(f"{FOLDER}/Book.md", "\n".join([
        "# Tone Marks", "",
        "**[Open the Reader](firstpair:reader)**", "",
        "A three-chapter code book about a forty-line Python program. Each chapter cites the "
        "program by fragment; the Reader shows each fragment as a card with **Show code** and "
        "**Open file**.", "",
        *[f"- {link(f'{FOLDER}/Chapters/{name}', name[3:])}" for name, _ in CHAPTERS],
        f"- {link(CODE_NOTE, 'tone_marks.py')} (the full source)", "",
    ]))
    vault.add("Home.md", "\n".join([
        "# Code book sample", "",
        "**[Open the Reader](firstpair:reader)**", "",
        f"The book is {link(f'{FOLDER}/Book', 'Tone Marks')}.", "",
    ]))
