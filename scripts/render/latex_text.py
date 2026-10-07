"""Project source text into TeX without changing punctuation or word spacing."""
from __future__ import annotations

import re
from urllib.parse import quote

SPECIAL = {
    "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$",
    "&": r"\&", "#": r"\#", "_": r"\_", "%": r"\%",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def esc(value):
    return "".join(SPECIAL.get(char, char) for char in str(value or ""))


def esc_mixed(value):
    # In Chinese notes, only an apostrophe between Latin letters has an
    # unambiguous English role. Chinese quotation marks keep xeCJK's rules.
    text = str(value or "")
    return "".join(
        r"\StudyEN{’}" if char == "’" and 0 < index < len(text) - 1
        and text[index - 1].isascii() and text[index - 1].isalpha()
        and text[index + 1].isascii() and text[index + 1].isalpha()
        else SPECIAL.get(char, char)
        for index, char in enumerate(text)
    )


def esc_en(value):
    return "".join(
        r"\StudyFWQuote{" + char + "}" if char in "＇＂" else SPECIAL.get(char, char)
        for char in str(value or "")
    )


def escurl(value):
    # URL-encode before TeX escaping so a generated percent sign cannot comment
    # out the rest of a line. Preserve existing percent escapes and URL syntax.
    encoded = quote(str(value or ""), safe="/:?=&@#%+;,!~*'()-._")
    return esc(encoded)


def italic_ranges(text, runs):
    if not runs:
        return []
    if "".join(run["text"] for run in runs) != text:
        raise ValueError("inline runs do not reconstruct source text")
    result = []
    cursor = 0
    for run in runs:
        end = cursor + len(run["text"])
        if "italic" in run.get("marks", []) and cursor < end:
            result.append({"start": cursor, "end": end, "kind": "italic"})
        cursor = end
    return result


def _validate_ranges(text, ranges):
    allowed = {"sentence", "phrase", "vocab", "italic"}
    for item in ranges:
        if item["kind"] not in allowed:
            raise ValueError(f"unsupported text range: {item['kind']}")
        if not 0 <= item["start"] < item["end"] <= len(text):
            raise ValueError(f"text range is outside the source: {item}")
    for kind in ("sentence", "vocab"):
        items = sorted((r for r in ranges if r["kind"] == kind), key=lambda r: r["start"])
        for previous, current in zip(items, items[1:]):
            if current["start"] < previous["end"]:
                raise ValueError(f"overlapping {kind} ranges are not supported")


def _inline_segment(text, ranges, start, end, sentence_underlined):
    result = []
    # Only inline styles use word-sized pieces. Whitespace stays outside their
    # groups, but remains INSIDE the outer sentence underline.
    for token in re.finditer(r"\s+|\S+", text[start:end]):
        left, right = start + token.start(), start + token.end()
        if token.group().isspace():
            result.append(token.group())
            continue
        points = {left, right}
        for item in ranges:
            for boundary in (item["start"], item["end"]):
                if left < boundary < right:
                    points.add(boundary)
        points = sorted(points)
        for a, b in zip(points, points[1:]):
            active = [r for r in ranges if r["start"] <= a and b <= r["end"]]
            vocab = next((r for r in active if r["kind"] == "vocab"), None)
            phrase = any(r["kind"] == "phrase" for r in active)
            study = bool(vocab and vocab.get("study_notes"))
            piece = esc_en(text[a:b])
            if any(r["kind"] == "italic" for r in active):
                piece = r"\textit{" + piece + "}"
            if phrase or study:
                piece = r"\textcolor{StudyRed}{" + piece + "}"
            elif vocab and not sentence_underlined:
                piece = r"\exammark{" + piece + "}"
            if vocab:
                piece = r"\hyperlink{lex-" + esc(vocab["lexical_id"]) + "}{" + piece + "}"
            result.append(piece)
    return "".join(result)


def ranges_tex(text, ranges):
    _validate_ranges(text, ranges)
    sentences = sorted(
        (r for r in ranges if r["kind"] == "sentence"), key=lambda r: r["start"]
    )
    result = []
    cursor = 0
    for sentence in sentences:
        start, end = sentence["start"], sentence["end"]
        result.append(_inline_segment(text, ranges, cursor, start, False))
        content = _inline_segment(text, ranges, start, end, True)
        result.append(r"\StudySentenceUL{" + content + "}")
        cursor = end
    result.append(_inline_segment(text, ranges, cursor, len(text), False))
    return "".join(result)


def inline_tex(text, runs=()):
    return ranges_tex(text, italic_ranges(text, runs))
