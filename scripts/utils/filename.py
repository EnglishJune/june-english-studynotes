#!/usr/bin/env python3
"""Build the canonical notes filename from an article title.

The filename stem preserves only Unicode letters/numbers plus ``_`` and ``-``.
The extension dot is introduced only by the fixed ``_notes.json`` suffix.
"""

from __future__ import annotations

import argparse
import unicodedata


APOSTROPHES = {"'", "\u2018", "\u2019", "\u02bc"}
EXTRA_DASHES = {"\u2212"}  # Unicode minus sign; Unicode Pd is handled by category.


def _classify_and_map(char: str) -> str:
    """Map one NFC-normalized source character to an allowed filename token."""
    if char in APOSTROPHES:
        return ""
    if char == "_":
        return "_"
    if char == "-" or char in EXTRA_DASHES or unicodedata.category(char) == "Pd":
        return "-"

    category = unicodedata.category(char)
    if category.startswith("L") or category.startswith("N"):
        return char
    if char.isspace():
        return "_"
    if category.startswith("P") or category.startswith("S"):
        return "_"
    if category.startswith("M") or category.startswith("C"):
        return ""

    # Defensive fallback: anything outside the explicit whitelist is discarded.
    return ""


def _normalize_separators(value: str) -> str:
    """Collapse each run of '_'/'-' to one separator, preferring '-' if present."""
    output: list[str] = []
    i = 0
    while i < len(value):
        char = value[i]
        if char not in {"_", "-"}:
            output.append(char)
            i += 1
            continue

        j = i
        has_hyphen = False
        while j < len(value) and value[j] in {"_", "-"}:
            has_hyphen = has_hyphen or value[j] == "-"
            j += 1
        output.append("-" if has_hyphen else "_")
        i = j

    return "".join(output).strip("_-")


def sanitize_title_for_filename(title: str) -> str:
    """Return a deterministic filename-safe title without truncating it."""
    if not isinstance(title, str):
        raise TypeError("title must be a string")

    normalized = unicodedata.normalize("NFC", title)
    mapped = "".join(_classify_and_map(char) for char in normalized)
    sanitized = _normalize_separators(mapped)
    return sanitized or "untitled"


def build_notes_filename(title: str) -> str:
    """Backward-compatible helper retained for parity tests."""
    return f"{sanitize_title_for_filename(title)}_notes.json"


def build_output_filename(title: str, suffix: str) -> str:
    """Return ``<sanitized_title><suffix>`` without changing the sanitiser."""
    if not isinstance(suffix, str) or not suffix:
        raise ValueError("suffix must be a non-empty string")
    return f"{sanitize_title_for_filename(title)}{suffix}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a canonical sanitized title stem or output filename.")
    parser.add_argument("title", help="Raw article title")
    parser.add_argument("--suffix", default="", help="Optional fixed suffix, e.g. _study_notes.html")
    args = parser.parse_args()
    stem = sanitize_title_for_filename(args.title)
    print(stem + args.suffix)


if __name__ == "__main__":
    main()
