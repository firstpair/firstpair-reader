"""Split the Chinese units into words and give each its pinyin.

    uv run --with jieba --with pypinyin python samples/build/segment.py

Writes samples/build/segmented.json, which build.py reads (build.py itself
needs only the standard library).  The Lu Xun text is split by jieba with
the adjustments in texts.py; the classical texts are split by hand there.
Punctuation gets an empty reading.  Review the output by eye after a change:
particles (的 de, 了 le, 得 de) and words read differently in context
(说 yuè in 不亦说乎, 乐 lè, 为 wéi/wèi) are the usual traps.
"""

import json
import sys
import unicodedata
from pathlib import Path

import jieba
from pypinyin import Style, pinyin

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import texts  # noqa: E402


def is_punct(token):
    return all(unicodedata.category(ch)[0] in "PSZ" for ch in token)


def reading(word, overrides=None):
    if is_punct(word):
        return ""
    if overrides and word in overrides:
        return overrides[word]
    return join_syllables([syllable[0] for syllable in pinyin(word, style=Style.TONE, heteronym=False)])


# Syllables of one word run together; one that starts with a, o, or e takes
# an apostrophe after another syllable (xué'ér, rán'ér).
def join_syllables(syllables):
    out = syllables[0]
    for syllable in syllables[1:]:
        base = unicodedata.normalize("NFD", syllable)[:1].lower()
        out += ("'" if base in "aoe" else "") + syllable
    return out


def hand_split(seg):
    words = []
    for token in seg.split():
        word, _, fixed = token.partition("=")
        words.append([word, "" if is_punct(word) else (fixed or reading(word))])
    return words


def jieba_split(text):
    return [[word, reading(word, texts.LUXUN_READINGS)]
            for word in jieba.cut(text, HMM=False) if word.strip()]


def main():
    jieba.setLogLevel(60)
    for word in texts.LUXUN_JIEBA_WORDS:
        jieba.add_word(word)
    for pair in texts.LUXUN_JIEBA_SPLITS:
        jieba.suggest_freq(pair, True)

    out = {"luxun": [], "analects": [], "daodejing": []}
    for page in texts.LUXUN["pages"]:
        out["luxun"].append([jieba_split(unit["zh"]) for unit in page["units"]])
    for page in texts.ANALECTS["pages"]:
        out["analects"].append([hand_split(unit["seg"]) for unit in page["units"]])
    for chapter in texts.DAODEJING:
        units = [hand_split(chapter["zh_title"])]
        units += [hand_split(unit["seg"]) for unit in chapter["units"]]
        out["daodejing"].append(units)

    # One line per unit keeps the file easy to review and diff.
    lines = ["{"]
    for index, (key, pages) in enumerate(out.items()):
        lines.append(f"  {json.dumps(key)}: [")
        for page_index, units in enumerate(pages):
            lines.append("    [")
            for unit_index, words in enumerate(units):
                comma = "," if unit_index < len(units) - 1 else ""
                lines.append(f"      {json.dumps(words, ensure_ascii=False)}{comma}")
            lines.append("    ]" + ("," if page_index < len(pages) - 1 else ""))
        lines.append("  ]" + ("," if index < len(out) - 1 else ""))
    lines.append("}")
    (HERE / "segmented.json").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for key, pages in out.items():
        for units in pages:
            for words in units:
                print(key, " ".join(f"{w}/{r}" if r else w for w, r in words))


if __name__ == "__main__":
    main()
