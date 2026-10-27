#!/usr/bin/env python3
"""Build the sample FirstPair Triptych vault in ``samples/triptych/``.

The vault holds three drafts of one short essay, "The Ferry at Low Water",
written for this sample (MIT, like the rest of the repository).  It exercises
the parts of the Triptych format a reader meets first:

* ``<book>/_data/triptych-reader.json``   Reader index, schema 4
* ``<book>/Triptychs/...``                Reader, Contents and Review launchers,
                                          set hubs, and fragment notes carrying
                                          schema-3 fenced ``triptych`` payloads
* ``<book>/_data/editions.jsonl``         edition ledger (+ ``editions.json``)
* ``<book>/_data/triptych-metrics.json``  ranked metrics (triptych-metrics.v1)
* ``<book>/_data/triptych-diffs.json``    precomputed diffs (edition-diffs.v2)
* ``<book>/Editions/<draft>.md``           each draft whole; unit links land here

Standard library only.  Run from the repository root:

    python3 samples/build/build_triptych.py

The output is deterministic.  Files the builder no longer produces are
removed; ``.obsidian/`` and ``Preferences/`` (Obsidian's settings and the
plugin's decision ledger) are left alone so a vault opened locally survives
a rebuild.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VAULT = ROOT / "samples" / "triptych"
BOOK = "The Ferry Crossing"
TRIPTYCHS = f"{BOOK}/Triptychs"
READER_LAUNCHER = f"{TRIPTYCHS}/Reader"
READER_CONTENTS = f"{TRIPTYCHS}/Contents"
REVIEW_LAUNCHER = f"{TRIPTYCHS}/Review"
PRESERVED = (".obsidian", "Preferences")

PROJECT_ID = "ferry-sample"
TARGET_CONTRACT = "firstpair.rosetta-editorial.v1"
READER_SCHEMA = 4
TRIPTYCH_SCHEMA = 3
TITLE = "The Ferry at Low Water"

# Fake but well-formed identities: three releases of one manuscript.
EDITIONS = [
    {"id": "draft-1", "title": "Draft 1", "version": "0.1.0", "commit": "0" * 39 + "1"},
    {"id": "draft-2", "title": "Draft 2", "version": "0.2.0", "commit": "0" * 39 + "2"},
    {"id": "final", "title": "Final", "version": "1.0.0", "commit": "0" * 39 + "3"},
]
CANONICAL = "final"
EDITION_BY_ID = {row["id"]: row for row in EDITIONS}
ORDER = [row["id"] for row in EDITIONS]

PARTS = [
    {"id": "river", "title": "The River", "heading": "Part I — The River"},
    {"id": "crossing", "title": "The Crossing", "heading": "Part II — The Crossing"},
]

SETS = [
    {
        "id": "drafts",
        "title": "All drafts",
        "description": "Every draft side by side: Draft 1, Draft 2, Final.",
        "editions": ["draft-1", "draft-2", "final"],
    },
    {
        "id": "revision",
        "title": "Last revision",
        "description": "The last revision only: Draft 2 against Final.",
        "editions": ["draft-2", "final"],
    },
]

# ---------------------------------------------------------------------------
# The text.  One entry per page; each page is a list of units, each unit a
# (kind, {edition: text}) pair.  An edition missing from a unit's dict lacks
# that unit.  Written for this sample; the drafts differ by word choice,
# punctuation, an added and a dropped sentence, and a sentence moved from
# page 2 to page 3.
# ---------------------------------------------------------------------------

PAGES = [
    {
        "id": "p01",
        "part": "river",
        "title": "The Ferry at Low Water",
        "units": [
            ("heading", {
                "draft-1": "Low Water",
                "draft-2": "The Ferry at Low Water",
                "final": "The Ferry at Low Water",
            }),
            ("paragraph", {
                "draft-1": (
                    "There is no bridge at our town. The river is wide and slow here, "
                    "and it has always been crossed by a flat ferry pulled along a cable. "
                    "In summer the water drops so low that the ferry scrapes the gravel, "
                    "and the whole town comes down to watch it stick."
                ),
                "draft-2": (
                    "There is no bridge at our village. The river is wide and slow here; "
                    "it has always been crossed by a flat ferry pulled along a cable. "
                    "In summer the water drops so low that the ferry scrapes the gravel, "
                    "and the whole village comes down to watch it stick."
                ),
                "final": (
                    "There is no bridge at our village. The river is wide and slow here; "
                    "it has always been crossed by a flat ferry hauled along a steel cable. "
                    "In summer the water drops so low that the ferry scrapes the gravel, "
                    "and half the village comes down to watch it stick."
                ),
            }),
        ],
    },
    {
        "id": "p02",
        "part": "river",
        "title": "The boatman",
        "units": [
            ("paragraph", {
                "draft-1": (
                    "The ferryman is called Anselm. He has worked the cable for thirty years, "
                    "and he knows every bar of sand between the two landings. "
                    "He does not hurry for anyone, not even for the town doctor. "
                    "On the far bank the road climbs through apple orchards toward the old market square."
                ),
                "draft-2": (
                    "The ferryman is called Anselm. He has worked the cable for thirty years "
                    "and knows every bar of sand between the two landings. "
                    "He does not hurry for anyone, not even for the village doctor."
                ),
                "final": (
                    "The boatman is called Anselm. He has worked the cable for thirty years "
                    "and knows every bar of sand between the two landings. "
                    "He does not hurry for anyone, not even for the village doctor, "
                    "and nobody has ever asked him to."
                ),
            }),
        ],
    },
    {
        "id": "p03",
        "part": "river",
        "title": "Children on the landing",
        "units": [
            ("paragraph", {
                "draft-1": (
                    "Children are not allowed to ride alone. They wait on the landing with their bicycles, "
                    "and the ferryman counts them twice before he lets go of the rope."
                ),
                "draft-2": (
                    "On the far bank the road climbs through apple orchards toward the old market square. "
                    "Children are not allowed to ride alone. They wait on the landing with their bicycles, "
                    "and the ferryman counts them twice before he lets go of the rope."
                ),
                "final": (
                    "On the far bank the road climbs through apple orchards toward the old market square. "
                    "Children may not ride alone. They wait on the landing with their bicycles, "
                    "and the boatman counts them twice before he lets go of the rope."
                ),
            }),
        ],
    },
    {
        "id": "p04",
        "part": "crossing",
        "title": "The crossing",
        "units": [
            ("paragraph", {
                "draft-1": (
                    "The crossing takes eleven minutes when the river is high and nearly twenty when it is low. "
                    "Anselm once said the time depends mostly on the conversation. "
                    "In the middle there is a place where the cable dips under the surface and the whole ferry tilts. "
                    "Visitors from the town grip the rail there; nobody who grew up on the River ever does."
                ),
                "draft-2": (
                    "The crossing takes eleven minutes when the river is high and nearly twenty when it is low. "
                    "In the middle there is a place where the cable dips under the surface and the whole ferry tilts. "
                    "Visitors from the village grip the rail there. Nobody who grew up on the river ever does."
                ),
                "final": (
                    "The crossing takes eleven minutes when the river is high and nearly twenty when it is low. "
                    "In the middle there is a place where the cable dips under the surface and the whole ferry tilts. "
                    "Visitors from the village grip the rail there. Nobody who grew up on the river ever does."
                ),
            }),
        ],
    },
    {
        "id": "p05",
        "part": "crossing",
        "title": "The council meeting",
        "units": [
            ("paragraph", {
                "draft-1": (
                    "Last spring the council voted again to build a bridge. "
                    "The ferryman listened to the whole meeting from the back of the hall "
                    "and then went home without a word."
                ),
                "draft-2": (
                    "Last spring the council voted, once again, to build a bridge. "
                    "The ferryman listened to the whole meeting from the back of the hall, "
                    "then went home without saying a word."
                ),
                "final": (
                    "Last spring the council voted, once again, to build a bridge. "
                    "The boatman listened to the whole meeting from the back of the hall, "
                    "then went home without saying a word. "
                    "The next morning the ferry left on time, as it always has."
                ),
            }),
        ],
    },
    {
        "id": "p06",
        "part": "crossing",
        "title": "Coda",
        "units": [
            ("paragraph", {
                "final": "Bridges take years. The river is in no hurry, and neither is he.",
            }),
        ],
    },
]

FUNCTION_WORDS = frozenset(
    """a an and are as at be been but by did do does for from had has have he her
    him his i if in into is it its may might must no nor not of on once or our she
    so than that the their them then there these they this to too was we were what
    when where which while who will with would yet""".split()
)

# ---------------------------------------------------------------------------
# Cross-runtime identities (mirrors review-state.js).
# ---------------------------------------------------------------------------

WORD_JOINERS = frozenset("-‐‑'’ʼ")


def sha256_id(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def fingerprint(text: str) -> str:
    """FNV-1a over the whitespace-compacted NFC code points."""

    value = 0x811C9DC5
    for character in unicodedata.normalize("NFC", re.sub(r"\s+", " ", text).strip()):
        value ^= ord(character)
        value = (value * 0x01000193) & 0xFFFFFFFF
    return f"{value:08x}"


def is_word_point(character: str) -> bool:
    return character not in WORD_JOINERS and unicodedata.category(character)[0] in "LMN"


def word_tokens(text: str, sentence_id: str) -> list[dict]:
    tokens = []
    cursor = 0
    while cursor < len(text):
        if not is_word_point(text[cursor]):
            cursor += 1
            continue
        start = cursor
        cursor += 1
        while cursor < len(text):
            if is_word_point(text[cursor]):
                cursor += 1
            elif (
                text[cursor] in WORD_JOINERS
                and cursor + 1 < len(text)
                and is_word_point(text[cursor + 1])
            ):
                cursor += 2
            else:
                break
        word = text[start:cursor]
        tokens.append({
            "key": f"{sentence_id}:w{len(tokens):03d}",
            "ordinal": len(tokens),
            "start": start,
            "end": cursor,
            "offset_unit": "unicode-code-point",
            "text": word,
            "text_sha256": sha256_id(word),
        })
    return tokens


SENTENCE_END = re.compile(r"(?<=[.!?])([\"'”’)\]]*)\s+(?=[\"'“‘(]*[A-Z0-9])")


def sentence_offsets(text: str) -> list[tuple[int, int]]:
    """Sentence (start, end) offsets: a terminal mark, space, capital."""

    spans, start = [], 0
    for boundary in SENTENCE_END.finditer(text):
        end = boundary.start() + len(boundary.group(1))
        spans.append((start, end))
        start = boundary.end()
    if text[start:].strip():
        spans.append((start, len(text.rstrip())))
    return spans


def stable_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def page_digest(payload: dict) -> str:
    """editorialPageDigest: the prose-bound projection of one page."""

    projection = {
        "key": payload["key"],
        "set": payload["set"],
        "lineage": payload["lineage"],
        "panes": [
            {name: pane[name] for name in (
                "edition", "units", "notes", "unit_kinds", "text_sha256", "sentence_spans",
            )}
            for pane in payload["panes"]
        ],
    }
    return sha256_id(stable_json(projection))


def source_content_id(digests: list[tuple[str, str]]) -> str:
    return sha256_id(stable_json({
        "project_id": PROJECT_ID,
        "target_contract_version": TARGET_CONTRACT,
        "pages": sorted([list(item) for item in digests]),
    }))

# ---------------------------------------------------------------------------
# Panes.
# ---------------------------------------------------------------------------


def edition_note(edition: str) -> str:
    return f"{BOOK}/Editions/{EDITION_BY_ID[edition]['title']}"


def block_id(edition: str, page: str, index: int) -> str:
    return f"{edition}-{page}-u{index}"


def unit_link(edition: str, page: dict, index: int, kind: str, text: str) -> str:
    if kind == "heading":
        return f"{edition_note(edition)}#{text}"
    return f"{edition_note(edition)}#^{block_id(edition, page['id'], index)}"


def build_pane(page: dict, edition: str) -> dict:
    texts, units, notes, kinds, spans = [], [], [], [], []
    offset = 0
    for index, (kind, by_edition) in enumerate(page["units"], 1):
        if edition not in by_edition:
            continue
        text = by_edition[edition]
        unit = f"{edition}:{page['id']}.{index}"
        occurrences: Counter[str] = Counter()
        for number, (start, end) in enumerate(sentence_offsets(text), 1):
            sentence = text[start:end]
            mark = fingerprint(sentence)
            occurrences[mark] += 1
            sentence_id = f"{unit}:H{mark}:O{occurrences[mark]:03d}:{mark}"
            spans.append({
                "id": sentence_id,
                "unit": unit,
                "unit_index": len(units),
                "sentence_index": number,
                "start": offset + start,
                "end": offset + end,
                "fingerprint": mark,
                "offset_unit": "unicode-code-point",
                "text_sha256": sha256_id(sentence),
                "tokens": word_tokens(sentence, sentence_id),
            })
        texts.append(text)
        units.append(unit)
        notes.append(unit_link(edition, page, index, kind, text))
        kinds.append(kind)
        offset += len(text) + 2  # the "\n\n" join
    text = "\n\n".join(texts)
    return {
        "edition": edition,
        "title": EDITION_BY_ID[edition]["title"],
        "units": units,
        "notes": notes,
        "unit_kinds": kinds,
        "sentence_spans": spans,
        "text": text,
        "text_sha256": sha256_id(text),
    }

# ---------------------------------------------------------------------------
# Rosetta rail: a small divergence review written for this sample.
# ---------------------------------------------------------------------------


def words_of(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower())


def similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, words_of(left), words_of(right), autojunk=False).ratio()


def sentences_of(text: str) -> list[str]:
    return [block[a:b] for block in text.split("\n\n") for a, b in sentence_offsets(block)]


def review(texts: dict[str, str], order: list[str]) -> dict:
    present = [edition for edition in order if texts[edition].strip()]
    norm = {edition: " ".join(texts[edition].lower().split()) for edition in present}
    groups: dict[str, list[str]] = defaultdict(list)
    for edition in present:
        groups[norm[edition]].append(edition)
    equal_groups = [group for group in groups.values() if len(group) > 1]
    all_equal = len(groups) == 1 and len(present) > 1
    pairs = {
        f"{a}|{b}": round(similarity(texts[a], texts[b]), 4)
        for a, b in combinations(present, 2)
    }

    def sim(a: str, b: str) -> float:
        return pairs.get(f"{a}|{b}", pairs.get(f"{b}|{a}", 0.0))

    panes: dict[str, dict] = {}
    if len(present) < 2:
        for edition in present:
            panes[edition] = {"score": 0, "features": ["="], "bars": 0, "structural": False, "outlier": False}
        return {"all_equal": all_equal, "equal_groups": equal_groups, "pair_similarity": pairs, "panes": panes}

    lengths = {e: len(texts[e]) for e in present}
    counts = {e: len(sentences_of(texts[e])) for e in present}
    mean_length = sum(lengths.values()) / len(present)
    mean_count = sum(counts.values()) / len(present)
    scores, features, structural = {}, {}, {}
    for edition in present:
        others = [other for other in present if other != edition]
        mean_sim = sum(sim(edition, other) for other in others) / len(others)
        scores[edition] = 0 if all_equal else round(100 * (1 - mean_sim))
        weighted: list[tuple[str, float]] = []
        own = sentences_of(texts[edition])
        theirs = [s for other in others for s in sentences_of(texts[other])]
        new = sum(1 for s in own if max((similarity(s, t) for t in theirs), default=0) < 0.5)
        if own and new:
            weighted.append(("N", new / len(own)))
        if counts[edition] >= mean_count + 0.6:
            weighted.append(("S", counts[edition] / mean_count))
        if counts[edition] <= mean_count - 0.6:
            weighted.append(("F", mean_count / max(1, counts[edition])))
        rare = {w for w in words_of(texts[edition]) if len(w) >= 9}
        rare -= {w for other in others for w in words_of(texts[other])}
        if rare:
            weighted.append(("R", len(rare) / 3))
        if lengths[edition] >= mean_length * 1.12:
            weighted.append(("E", lengths[edition] / mean_length))
        if lengths[edition] <= mean_length * 0.88:
            weighted.append(("C", mean_length / max(1, lengths[edition])))
        weighted.sort(key=lambda item: -item[1])
        features[edition] = ["="] if all_equal or not weighted else [code for code, _ in weighted[:3]]
        structural[edition] = any(
            counts[other] != counts[edition] and sim(edition, other) >= 0.55 for other in others
        )
    for edition in present:
        rest = [scores[other] for other in present if other != edition]
        outlier = scores[edition] >= 40 and scores[edition] >= max(rest) + 10 and len(set(features[edition]) - {"="}) >= 2
        if all_equal or (scores[edition] < 3 and features[edition] == ["="] and not structural[edition]):
            bars = 0
        elif outlier:
            bars = 3
        elif "N" in features[edition]:
            bars = 2
        else:
            bars = 1
        panes[edition] = {
            "score": scores[edition],
            "features": features[edition],
            "bars": bars,
            "structural": structural[edition],
            "outlier": outlier,
        }
    return {"all_equal": all_equal, "equal_groups": equal_groups, "pair_similarity": pairs, "panes": panes}

# ---------------------------------------------------------------------------
# Edition diffs (firstpair.edition-diffs.v2), as the shared diff view reads
# them: code-point ranges over each pane's text, per pair and per set.
# ---------------------------------------------------------------------------

TOKEN_RE = re.compile(r"[^\W_]+(?:[-'’][^\W_]+)*|[^\w\s]")
CATEGORIES = ["punct", "inflect", "function", "lexical", "restructure", "rewrite", "content", "moved"]
MOVE_MIN_WORDS = 6


def tokens(text: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group().casefold()) for m in TOKEN_RE.finditer(text)]


def word_list(toks) -> list[str]:
    return [t[2] for t in toks if re.search(r"\w", t[2])]


def content_words(toks) -> list[str]:
    return [w for w in word_list(toks) if w not in FUNCTION_WORDS]


def category(tag: str, left, right) -> str:
    wl, wr = word_list(left), word_list(right)
    if not wl and not wr:
        return "punct"
    if tag == "replace" and wl == wr:
        return "inflect"
    if set(wl + wr) <= FUNCTION_WORDS:
        return "function"
    if tag == "replace":
        if len(wl) <= 2 and len(wr) <= 2 and not set(wl) & set(wr):
            return "lexical"
        return "restructure" if set(wl) & set(wr) else "rewrite"
    return "content" if max(len(wl), len(wr)) > 3 else "lexical"


def merge_ranges(text: str, toks, kinds) -> list[list]:
    out: list[list] = []
    for (start, end, _), kind in zip(toks, kinds):
        if kind is None:
            continue
        kind = list(kind) if isinstance(kind, tuple) else [kind]
        if out and out[-1][2:] == kind and not text[out[-1][1]:start].strip():
            out[-1][1] = end
        else:
            out.append([start, end, *kind])
    return out


def overlap(words: list[str], other: list[str]) -> float:
    if not words or not other:
        return 0.0
    return sum((Counter(words) & Counter(other)).values()) / len(words)


def page_diffs(texts: dict[str, str], order: list[str], hunks: dict) -> dict:
    toks = {e: tokens(texts[e]) for e in order}
    entry: dict[str, dict] = {}
    kept: dict[tuple[str, str], tuple[set, set]] = {}
    for left, right in combinations(order, 2):
        matcher = difflib.SequenceMatcher(
            None, [t[2] for t in toks[left]], [t[2] for t in toks[right]], autojunk=False,
        )
        kinds_left: list = [None] * len(toks[left])
        kinds_right: list = [None] * len(toks[right])
        keep_left, keep_right = set(), set()
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                keep_left.update(range(i1, i2))
                keep_right.update(range(j1, j2))
                continue
            a, b = toks[left][i1:i2], toks[right][j1:j2]
            kind = category(tag, a, b)
            for index in range(i1, i2):
                kinds_left[index] = ("del", kind)
            for index in range(j1, j2):
                kinds_right[index] = ("ins", kind)
            wl, wr = word_list(a), word_list(b)
            if tag == "replace" and kind == "lexical" and len(wl) == 1 and len(wr) == 1:
                hunks[f"{left}|{right}"].append((wl[0], wr[0], a[0][0], a[-1][1], b[0][0], b[-1][1]))
        kept[(left, right)] = (keep_left, keep_right)
        entry[f"{left}|{right}"] = {
            left: merge_ranges(texts[left], toks[left], kinds_left),
            right: merge_ranges(texts[right], toks[right], kinds_right),
        }
    if len(order) >= 3:
        group = {}
        for edition in order:
            others = [o for o in order if o != edition]
            survives = {
                o: kept[(edition, o)][0] if (edition, o) in kept else kept[(o, edition)][1]
                for o in others
            }
            kinds = []
            for index in range(len(toks[edition])):
                found = [o for o in others if index in survives[o]]
                kinds.append(
                    None if len(found) == len(others)
                    else "uniq" if not found
                    else f"share:{found[0]}" if len(found) == 1
                    else "part"
                )
            group[edition] = merge_ranges(texts[edition], toks[edition], kinds)
        entry["|".join(order)] = group
    if all(not ranges for diff in entry.values() for ranges in diff.values()):
        return {}
    return entry


def mark_moves(entries: dict, texts: dict, keys: list[str]) -> None:
    """A dropped run whose words reappear as an addition on a neighbouring page moved."""

    for position, key in enumerate(keys):
        for pair, diff in entries[key].items():
            if pair.count("|") != 1:
                continue
            left, right = pair.split("|")
            for side, other_side, mark, opposite in ((left, right, "del", "ins"), (right, left, "ins", "del")):
                for rng in diff.get(side, []):
                    if rng[2] != mark or rng[3] not in ("content", "rewrite"):
                        continue
                    words = content_words(tokens(texts[key][side][rng[0]:rng[1]]))
                    if len(words) < MOVE_MIN_WORDS:
                        continue
                    for near in keys[max(0, position - 2):position + 3]:
                        if near == key:
                            continue
                        for other in entries[near].get(pair, {}).get(other_side, []):
                            if other[2] != opposite or other[3] not in ("content", "rewrite"):
                                continue
                            moved = content_words(tokens(texts[near][other_side][other[0]:other[1]]))
                            if overlap(words, moved) >= 0.5:
                                rng[3:] = ["moved", near]
                                other[3:] = ["moved", key]
                                break
                        if rng[3] == "moved":
                            break


def rule_id(pair: str, source: str, target: str) -> str:
    return "R" + hashlib.sha256(f"{pair}\x1f{source}\x1f{target}".encode()).hexdigest()[:12]


def build_diffs(pages_by_set: list[tuple[dict, list[str], dict[str, dict[str, str]]]], part_of: dict) -> dict:
    """pages_by_set: (set, edition order, {page key: {edition: text}}) in book order."""

    entries: dict[str, dict] = {}
    rules: dict[str, list] = {}
    summary: dict[str, dict] = {}
    for reader_set, order, pages in pages_by_set:
        keys = list(pages)
        hunks_by_page = {}
        for key in keys:
            hunks: dict[str, list] = defaultdict(list)
            entries[key] = page_diffs(pages[key], order, hunks)
            hunks_by_page[key] = hunks
        mark_moves(entries, pages, keys)
        # Rules and the Part summary come from the first (widest) set only,
        # so a page shown in two sets is not counted twice.
        if reader_set is not SETS[0]:
            continue
        for left, right in combinations(order, 2):
            pair = f"{left}|{right}"
            found: dict[tuple[str, str], list] = defaultdict(list)
            for key in keys:
                for source, target, a0, a1, b0, b1 in hunks_by_page[key].get(pair, []):
                    found[(source, target)].append([key, a0, a1, b0, b1])
            recurring = {sub: hits for sub, hits in found.items() if len({h[0] for h in hits}) >= 3}
            listed = []
            for (source, target), hits in sorted(recurring.items(), key=lambda item: (-len(item[1]), item[0])):
                listed.append({
                    "id": rule_id(pair, source, target),
                    "from": source,
                    "to": target,
                    "count": len(hits),
                    "pages": len({h[0] for h in hits}),
                    "reverse": rule_id(pair, target, source) if (target, source) in recurring else None,
                    "reverse_count": len(found.get((target, source), [])),
                    "occurrences": hits,
                })
            if listed:
                rules[pair] = listed
        for key in keys:
            for pair, diff in entries[key].items():
                if pair.count("|") != 1:
                    continue
                left, right = pair.split("|")
                bucket = summary.setdefault(pair, {}).setdefault(part_of[key], {})
                for side in (right, left):
                    for rng in diff.get(side, []):
                        if side == left and rng[3] != "content":
                            continue
                        count = len(re.findall(r"[^\W_]+", pages[key][side][rng[0]:rng[1]]))
                        count = count or (1 if rng[3] == "punct" else 0)
                        if count:
                            bucket[rng[3]] = bucket.get(rng[3], 0) + count
    return {
        "schema": "firstpair.edition-diffs.v2",
        "editions": ORDER,
        "categories": CATEGORIES,
        "pages": {key: entry for key, entry in entries.items() if entry},
        "rules": rules,
        "summary": summary,
    }

# ---------------------------------------------------------------------------
# Metrics (firstpair.triptych-metrics.v1): numbers only, never prose.
# ---------------------------------------------------------------------------

METRICS = [
    {
        "key": "changed", "letter": "Δ", "better": "lower", "format": "percent",
        "warn": 15, "bad": 35, "rank": 1,
        "label": {"en": "Changed"},
        "description": {"en": "Share of words changed since the previous draft."},
    },
    {
        "key": "sentence_length", "letter": "L", "better": "lower", "format": "decimal1",
        "warn": 20, "bad": 26, "rank": 2,
        "label": {"en": "Sentence length"},
        "description": {"en": "Mean words per sentence."},
    },
    {
        "key": "words", "letter": "W", "better": "lower", "format": "integer", "rank": 3,
        "label": {"en": "Words"},
        "description": {"en": "Words on the page."},
    },
]


def metric_values(texts: dict[str, str]) -> dict:
    values = {}
    for index, edition in enumerate(ORDER):
        text = texts.get(edition, "")
        if not text:
            continue
        words = words_of(text)
        row = {
            "words": len(words),
            "sentence_length": round(len(words) / max(1, len(sentences_of(text))), 2),
        }
        previous = texts.get(ORDER[index - 1], "") if index else None
        if previous:
            row["changed"] = round(100 * (1 - similarity(previous, text)), 1)
        values[edition] = row
    return values

# ---------------------------------------------------------------------------
# Notes.
# ---------------------------------------------------------------------------


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def navigation_line(previous, up, current, next_) -> str:
    return " | ".join((
        f"[[{previous[0]}|Previous: {previous[1]}]]" if previous else "Previous (start)",
        f"[[{up}|Up]]",
        f"[[{current}#Top|Top]]",
        f"[[{READER_CONTENTS}|TOC]]",
        f"[[{next_[0]}|Next: {next_[1]}]]" if next_ else "Next (end)",
    ))


BAR_GLYPHS = {0: "·", 1: "|", 2: "||", 3: "|||"}
MARKS_LEGEND = (
    "Marks per pane: `·` shared, `|` tonal or lexical pressure, `||` addition, "
    "omission, or new claim, `|||` review outlier, `*` structural split or fusion; "
    "`≡` marks pages where panes are identical."
)


def fragment_note(payload, reader_set, page, nav, badges) -> str:
    lines = [
        "---",
        'type: "triptych"',
        f"triptych_key: {yaml_quote(payload['key'])}",
        f"set: {yaml_quote(reader_set['id'])}",
        f"part_id: {yaml_quote(page['part'])}",
        f"status: {yaml_quote(badges)}",
        "edition_ids:",
        *[f"  - {yaml_quote(e)}" for e in reader_set["editions"]],
        "---",
        "",
        '<a id="Top"></a>',
        "",
        "<!-- reader-navigation:top -->",
        nav,
        "",
        f"# {page['title']}",
        "",
    ]
    for group in payload["review"]["equal_groups"]:
        lines += ["**≡ Identical:** " + " = ".join(EDITION_BY_ID[e]["title"] for e in group), ""]
    lines += ["```triptych", json.dumps(payload, ensure_ascii=False, indent=1), "```", ""]
    for pane in payload["panes"]:
        rail = payload["review"]["panes"].get(pane["edition"])
        suffix = ""
        if rail:
            glyph = BAR_GLYPHS[rail["bars"]] + ("*" if rail["structural"] else "")
            suffix = f" — `{glyph}` score {rail['score']} [{','.join(rail['features'])}]"
        lines += [f"## {pane['title']}{suffix}", ""]
        if pane["text"]:
            lines += ["> " + line if line else ">" for line in pane["text"].split("\n")]
        else:
            lines.append("> (absent in this edition)")
        lines.append("")
    lines += ["<!-- reader-navigation:bottom -->", nav]
    return "\n".join(lines) + "\n"


def note_title(page: dict) -> str:
    return f"{PAGES.index(page) + 1:04d} {page['title']}"


def build() -> dict[str, str]:
    files: dict[str, str] = {}
    page_texts: dict[str, dict[str, str]] = {}
    part_of: dict[str, str] = {}
    digests: list[tuple[str, str]] = []
    reader_sets = []
    payloads: list[tuple[str, dict]] = []
    diff_inputs = []
    metric_rows: dict[str, dict] = {}

    for reader_set in SETS:
        set_note = f"{TRIPTYCHS}/{reader_set['title']}"
        pages = []
        hub_rows = []
        texts_for_diffs: dict[str, dict[str, str]] = {}
        for index, page in enumerate(PAGES):
            key = f"{reader_set['id']}/{page['id']}"
            panes = [build_pane(page, edition) for edition in reader_set["editions"]]
            texts = {pane["edition"]: pane["text"] for pane in panes}
            texts_for_diffs[key] = texts
            part_of[key] = page["part"]
            metric_rows[key] = metric_values(texts)
            payload = {
                "schema_version": TRIPTYCH_SCHEMA,
                "project_id": PROJECT_ID,
                "source_content_id": None,  # bound below, once every page is known
                "target_contract_version": TARGET_CONTRACT,
                "key": key,
                "set": reader_set["id"],
                "set_title": reader_set["title"],
                "lineage": page["id"],
                "incipit": page["title"],
                "panes": panes,
                "review": review(texts, reader_set["editions"]),
            }
            digest = page_digest(payload)
            digests.append((key, digest))
            note = f"{set_note}/{note_title(page)}"
            part = next(p for p in PARTS if p["id"] == page["part"])
            previous = PAGES[index - 1] if index else None
            following = PAGES[index + 1] if index + 1 < len(PAGES) else None
            nav = navigation_line(
                (f"{set_note}/{note_title(previous)}", previous["title"]) if previous else None,
                f"{set_note}#{part['heading']}",
                note,
                (f"{set_note}/{note_title(following)}", following["title"]) if following else None,
            )
            badges, prior = [], None
            for pane in panes:
                if not pane["text"]:
                    badges.append("A")
                    continue
                badges.append("P" if prior is None else "S" if pane["text"] == prior else "D")
                prior = pane["text"]
            payloads.append((note, payload, reader_set, page, nav, "/".join(badges)))
            pages.append({
                "key": key,
                "note": note,
                "title": page["title"],
                "part_id": page["part"],
                "order": index + 1,
                "target_digest": digest,
            })
            marks = " ".join(
                BAR_GLYPHS[r["bars"]] + ("*" if r["structural"] else "")
                if (r := payload["review"]["panes"].get(e)) else "—"
                for e in reader_set["editions"]
            )
            if payload["review"]["equal_groups"]:
                marks = "≡ " + marks
            hub_rows.append((part, note, page["title"], marks))
        diff_inputs.append((reader_set, reader_set["editions"], texts_for_diffs))
        page_texts.update(texts_for_diffs)

        hub = [
            "---",
            'type: "triptych-hub"',
            f"set: {yaml_quote(reader_set['id'])}",
            f"triptych_count: {len(hub_rows)}",
            "---",
            "",
            f"# {reader_set['title']}",
            "",
            reader_set["description"],
            "",
            "Panes: " + " · ".join(EDITION_BY_ID[e]["title"] for e in reader_set["editions"]) + ".",
            "",
            MARKS_LEGEND,
        ]
        current = None
        for part, note, title, marks in hub_rows:
            if part is not current:
                hub += ["", f"## {part['heading']}", ""]
                current = part
            hub.append(f"- `{marks}` [[{note}|{title}]]")
        files[f"{set_note}.md"] = "\n".join(hub) + "\n"
        reader_sets.append({
            "id": reader_set["id"],
            "title": reader_set["title"],
            "description": reader_set["description"],
            "note": set_note,
            "edition_ids": reader_set["editions"],
            "navigation_edition_id": reader_set["editions"][-1],
            "parts": [
                {"id": p["id"], "title": p["title"], "heading": p["heading"], "order": n}
                for n, p in enumerate(PARTS, 1)
            ],
            "pages": pages,
        })

    content_id = source_content_id(digests)
    for note, payload, reader_set, page, nav, badges in payloads:
        payload["source_content_id"] = content_id
        files[f"{note}.md"] = fragment_note(payload, reader_set, page, nav, badges)

    canonical = EDITION_BY_ID[CANONICAL]
    index = {
        "schema_version": READER_SCHEMA,
        "title": TITLE,
        "book_version": canonical["version"],
        "source_commit": canonical["commit"],
        "project_id": PROJECT_ID,
        "source_content_id": content_id,
        "target_contract_version": TARGET_CONTRACT,
        "launcher": READER_LAUNCHER,
        "contents": READER_CONTENTS,
        "review": REVIEW_LAUNCHER,
        "editions": [
            {"id": row["id"], "version": row["version"], "source_commit": row["commit"]}
            for row in EDITIONS
        ],
        "sets": reader_sets,
    }
    files[f"{BOOK}/_data/triptych-reader.json"] = json.dumps(index, ensure_ascii=False, indent=2) + "\n"

    ledger = [
        {
            "id": row["id"],
            "title": row["title"],
            "version": row["version"],
            "commit": row["commit"],
            "lang": "en",
            "canonical": row["id"] == CANONICAL,
            "index": number,
        }
        for number, row in enumerate(EDITIONS, 1)
    ]
    files[f"{BOOK}/_data/editions.jsonl"] = "".join(
        json.dumps(row, ensure_ascii=False) + "\n" for row in ledger
    )
    files[f"{BOOK}/_data/editions.json"] = json.dumps(ledger, ensure_ascii=False, indent=2) + "\n"
    files[f"{BOOK}/_data/triptych-metrics.json"] = json.dumps(
        {"schema": "firstpair.triptych-metrics.v1", "metrics": METRICS, "values": metric_rows},
        ensure_ascii=False, indent=1,
    ) + "\n"
    files[f"{BOOK}/_data/triptych-diffs.json"] = json.dumps(
        build_diffs(diff_inputs, part_of), ensure_ascii=False, separators=(",", ":"),
    ) + "\n"

    set_links = [
        f"- [[{row['note']}|{row['title']}]] ({len(row['pages'])} pages)" for row in reader_sets
    ]
    files[f"{TRIPTYCHS}/Reader.md"] = "\n".join([
        "---", 'type: "triptych-reader-launcher"', "---", "",
        f"# {TITLE}", "",
        f"**[[{READER_CONTENTS}|Open the contents]]**",
        f"**[[{REVIEW_LAUNCHER}|Open Review]]**", "",
        "With FirstPair Triptych enabled this note opens the Reader. "
        "Without it, follow a set below; every page is plain Markdown.", "",
        *set_links,
    ]) + "\n"
    files[f"{TRIPTYCHS}/Contents.md"] = "\n".join([
        "---", 'type: "triptych-reader-contents"', "---", "",
        "# Contents", "",
        "Each set shows the same pages with a different choice of drafts.", "",
        *set_links,
    ]) + "\n"
    files[f"{TRIPTYCHS}/Review.md"] = "\n".join([
        "---", 'type: "triptych-review-launcher"', "---", "",
        "# Review", "",
        f"**[[{READER_LAUNCHER}|Open the Reader]]**", "",
        "With FirstPair Triptych enabled this note opens Review: the pages you have "
        "marked, the edit rules, and the digest of your decisions.",
    ]) + "\n"

    for row in EDITIONS:
        edition = row["id"]
        lines = [
            "---", 'type: "edition"', f"edition: {yaml_quote(edition)}",
            f"version: {yaml_quote(row['version'])}", f"commit: {yaml_quote(row['commit'])}",
            "---", "",
        ]
        titles = [
            units[edition] for page in PAGES for kind, units in page["units"]
            if kind == "heading" and edition in units
        ]
        lines += [f"# {titles[0] if titles else row['title']}", ""]
        for part in PARTS:
            lines += [f"## {part['heading']}", ""]
            for page in (p for p in PAGES if p["part"] == part["id"]):
                for number, (kind, units) in enumerate(page["units"], 1):
                    if kind != "heading" and edition in units:
                        lines += [f"{units[edition]} ^{block_id(edition, page['id'], number)}", ""]
        files[f"{edition_note(edition)}.md"] = "\n".join(lines).rstrip() + "\n"

    files["Home.md"] = "\n".join([
        f"# {TITLE}",
        "",
        f"**[[{READER_LAUNCHER}|Open the Triptych Reader]]** · **[[{REVIEW_LAUNCHER}|Open Review]]**",
        "",
        "A sample vault for the FirstPair Triptych plugin: three drafts of one short "
        "essay, side by side.",
        "",
        "- **Draft 1**, **Draft 2**, **Final**: the drafts differ by word choice "
        "(*town* becomes *village*, *ferryman* becomes *boatman*), punctuation, a "
        "dropped sentence (page 4), added sentences (pages 2 and 5, and a closing "
        "page found only in the Final), and a sentence moved from page 2 to page 3.",
        "- Two sets: *All drafts* (three panes) and *Last revision* (Draft 2 against Final).",
        "- Each draft whole: " + ", ".join(
            f"[[{edition_note(row['id'])}|{row['title']}]]" for row in EDITIONS
        ) + ".",
        "",
        "The essay was written for this sample and is released under the MIT "
        "License with the rest of the repository. The commits and versions are "
        "placeholders. Generated by `samples/build/build_triptych.py`; edit that "
        "script, not these notes.",
        "",
        "To try it, install the plugin into this vault's `.obsidian/plugins/firstpair-triptych/` "
        "and enable it under Settings → Community plugins.",
    ]) + "\n"
    files["README.md"] = "\n".join([
        "# Triptych sample vault",
        "",
        "An Obsidian vault for the FirstPair Triptych plugin: three drafts "
        "(Draft 1, Draft 2, Final) of a short essay, *The Ferry at Low Water*, in "
        "two Parts and six pages, shown in two sets. Open the folder as a vault, "
        "install `plugins/firstpair-triptych` into `.obsidian/plugins/`, enable it, "
        "and start from `Home.md`.",
        "",
        "The essay was written for this sample; it and the vault are MIT licensed "
        "like the rest of the repository. Edition commits are placeholders.",
        "",
        "The vault is generated: run `python3 samples/build/build_triptych.py` from "
        "the repository root, and check it with `node samples/build/check-triptych.mjs`.",
    ]) + "\n"
    return files


def write(files: dict[str, str]) -> tuple[int, int]:
    written = removed = 0
    for relative, content in sorted(files.items()):
        path = VAULT / relative
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written += 1
    wanted = {VAULT / relative for relative in files}
    for path in sorted(VAULT.rglob("*"), reverse=True):
        relative = path.relative_to(VAULT)
        if relative.parts[0] in PRESERVED:
            continue
        if path.is_file() and path not in wanted:
            path.unlink()
            removed += 1
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    return written, removed


def main() -> int:
    files = build()
    written, removed = write(files)
    print(f"{VAULT.relative_to(ROOT)}: {len(files)} files ({written} written, {removed} removed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
