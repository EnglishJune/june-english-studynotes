#!/usr/bin/env python3
from __future__ import annotations
import hashlib, re, unicodedata
from typing import Any

def collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def concat_inline_runs(runs: list[dict[str, Any]]) -> str:
    return "".join(str(r.get("text", "")) for r in runs)

def lexical_id(lemma: str, pos: str) -> str:
    key = unicodedata.normalize("NFC", f"{lemma.strip().lower()}\x1f{pos.strip().lower()}")
    return "lex-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]

def reconstruct_chinese(sentences: list[dict[str, Any]]) -> str:
    return "".join(str(s.get("translation_zh", "")) for s in sentences).strip()
