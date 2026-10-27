# tone_marks.py

Up: [[Tone Marks/Book|Tone Marks]]

## Full Source

```python
"""Turn numbered pinyin (ni3 hao3) into tone marks (nǐ hǎo)."""

import re
import sys

MARKS = {
    "a": "āáǎà", "e": "ēéěè", "i": "īíǐì",
    "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ",
}

SYLLABLE = re.compile(r"([a-zü:]+)([1-5])", re.IGNORECASE)


def mark_vowel(letters):
    """Index of the vowel that carries the tone mark, or -1."""
    lower = letters.lower()
    for vowel in "ae":
        if vowel in lower:
            return lower.index(vowel)
    if "ou" in lower:
        return lower.index("o")
    for index in range(len(lower) - 1, -1, -1):
        if lower[index] in MARKS:
            return index
    return -1


def convert_syllable(match):
    letters = match.group(1).replace("u:", "ü").replace("v", "ü").replace("V", "Ü")
    tone = int(match.group(2))
    index = mark_vowel(letters)
    if tone == 5 or index < 0:
        return letters
    vowel = letters[index]
    marked = MARKS[vowel.lower()][tone - 1]
    if vowel.isupper():
        marked = marked.upper()
    return letters[:index] + marked + letters[index + 1:]


def convert(text):
    return SYLLABLE.sub(convert_syllable, text)


if __name__ == "__main__":
    for line in sys.stdin:
        print(convert(line.rstrip("\n")))
```
