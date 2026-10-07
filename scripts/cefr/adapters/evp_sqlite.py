#!/usr/bin/env python3
from __future__ import annotations

import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
CONTENT_POS = {"noun", "verb", "adjective", "adverb"}
TOKEN_RE = re.compile(r"[A-Za-z]+(?:[-’'][A-Za-z]+)*")
FUNCTION_LIKE = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "than", "that", "this", "these", "those",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
    "who", "whom", "whose", "which", "what",
    "be", "am", "is", "are", "was", "were", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "done",
    "can", "could", "may", "might", "must", "shall", "should", "will", "would",
    "to", "of", "in", "on", "at", "by", "for", "from", "with", "about", "into", "onto", "over", "under", "between", "through", "during", "before", "after", "above", "below", "up", "down", "out", "off",
    "not", "no", "only", "just", "so", "very", "too", "also", "even", "still", "already", "yet", "ever", "never", "here", "there", "then", "now", "once", "again", "back", "away", "together",
    "more", "most", "less", "least", "much", "many", "few", "some", "any", "all", "both", "each", "every", "either", "neither",
}

# Conservative irregular forms used only to find candidate EVP base words.
# Final CEFR assignment still comes from an EVP entry, never from this map.
IRREGULAR = {
    "am": ["be"], "is": ["be"], "are": ["be"], "was": ["be"], "were": ["be"], "been": ["be"],
    "has": ["have"], "had": ["have"],
    "does": ["do"], "did": ["do"], "done": ["do"],
    "goes": ["go"], "went": ["go"], "gone": ["go"],
    "says": ["say"], "said": ["say"],
    "made": ["make"],
    "took": ["take"], "taken": ["take"],
    "came": ["come"],
    "saw": ["see"], "seen": ["see"],
    "knew": ["know"], "known": ["know"],
    "got": ["get"], "gotten": ["get"],
    "gave": ["give"], "given": ["give"],
    "found": ["find"],
    "thought": ["think"],
    "told": ["tell"],
    "became": ["become"],
    "shown": ["show"],
    "left": ["leave"],
    "felt": ["feel"],
    "brought": ["bring"],
    "began": ["begin"], "begun": ["begin"],
    "kept": ["keep"],
    "held": ["hold"],
    "wrote": ["write"], "written": ["write"],
    "stood": ["stand"],
    "heard": ["hear"],
    "meant": ["mean"],
    "met": ["meet"],
    "ran": ["run"],
    "paid": ["pay"],
    "sat": ["sit"],
    "spoke": ["speak"], "spoken": ["speak"],
    "lay": ["lie"], "lain": ["lie"],
    "led": ["lead"],
    "grew": ["grow"], "grown": ["grow"],
    "fell": ["fall"], "fallen": ["fall"],
    "chose": ["choose"], "chosen": ["choose"],
    "wore": ["wear"], "worn": ["wear"],
    "drove": ["drive"], "driven": ["drive"],
    "stole": ["steal"], "stolen": ["steal"],
    "ate": ["eat"], "eaten": ["eat"],
    "drank": ["drink"], "drunk": ["drink"],
    "bought": ["buy"],
    "sold": ["sell"],
    "caught": ["catch"],
    "fought": ["fight"],
    "lost": ["lose"],
    "won": ["win"],
    "sent": ["send"],
    "built": ["build"],
    "spent": ["spend"],
    "understood": ["understand"],
    "grew": ["grow"],
    "threw": ["throw"], "thrown": ["throw"],
    "drew": ["draw"], "drawn": ["draw"],
    "flew": ["fly"], "flown": ["fly"],
    "forgot": ["forget"], "forgotten": ["forget"],
    "forgave": ["forgive"], "forgiven": ["forgive"],
    "rose": ["rise"], "risen": ["rise"],
    "slept": ["sleep"],
    "swam": ["swim"], "swum": ["swim"],
    "taught": ["teach"],
    "learned": ["learn"], "learnt": ["learn"],
    "dreamed": ["dream"], "dreamt": ["dream"],
    "lives": ["live", "life"],
    "lived": ["live"],
}


def _normalise(text: str) -> str:
    return str(text or "").replace("’", "'").strip().lower()


def _unique(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = _normalise(value)
        if value and value not in seen:
            out.append(value)
            seen.add(value)
    return out


def lemma_candidates(surface: str) -> list[str]:
    """Return conservative base-word candidates for EVP lookup.

    These candidates are only lookup aids. The adapter never derives a CEFR
    level from morphology; a level must come from a verified EVP row.
    """
    word = _normalise(surface)
    if not word:
        return []
    out = [word]
    out.extend(IRREGULAR.get(word, []))

    # Possessive forms are uncommon in the content-word path but stripping the
    # suffix can recover ordinary nouns when the token is not a proper name.
    if word.endswith("'s") and len(word) > 3:
        out.append(word[:-2])

    if re.fullmatch(r"[a-z]+", word):
        if word.endswith("ies") and len(word) > 4:
            out.append(word[:-3] + "y")
        if word.endswith("ves") and len(word) > 4:
            out.extend([word[:-3] + "f", word[:-3] + "fe", word[:-1]])
        if word.endswith("es") and len(word) > 4:
            out.extend([word[:-2], word[:-1]])
        if word.endswith("s") and not word.endswith(("ss", "us", "is")) and len(word) > 3:
            out.append(word[:-1])

        if word.endswith("ied") and len(word) > 4:
            out.append(word[:-3] + "y")
        if word.endswith("ed") and len(word) > 4:
            stem = word[:-2]
            out.extend([stem, stem + "e"])
            if len(stem) >= 2 and stem[-1] == stem[-2]:
                out.append(stem[:-1])

        if word.endswith("ying") and len(word) > 5:
            out.append(word[:-4] + "ie")
        if word.endswith("ing") and len(word) > 5:
            stem = word[:-3]
            out.extend([stem, stem + "e"])
            if len(stem) >= 2 and stem[-1] == stem[-2]:
                out.append(stem[:-1])

        if word.endswith("ier") and len(word) > 4:
            out.append(word[:-3] + "y")
        if word.endswith("iest") and len(word) > 5:
            out.append(word[:-4] + "y")
        if word.endswith("er") and len(word) > 4:
            stem = word[:-2]
            out.extend([stem, stem + "e"])
            if len(stem) >= 2 and stem[-1] == stem[-2]:
                out.append(stem[:-1])
        if word.endswith("est") and len(word) > 5:
            stem = word[:-3]
            out.extend([stem, stem + "e"])
            if len(stem) >= 2 and stem[-1] == stem[-2]:
                out.append(stem[:-1])

    return _unique(out)


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)


def validate_asset(db_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "adapter": "evp_sqlite",
        "asset": str(db_path),
        "exists": db_path.exists(),
        "schema_ok": False,
        "metadata": {},
    }
    if not db_path.exists():
        return result
    try:
        with _connect(db_path) as con:
            metadata = dict(con.execute("SELECT key, value FROM evp_metadata"))
            result["metadata"] = metadata
            required = {"entry_id", "base_word", "lookup_key", "guideword", "level", "part_of_speech", "topics"}
            cols = {row[1] for row in con.execute("PRAGMA table_info(evp_lookup)")}
            levels = {row[0] for row in con.execute("SELECT DISTINCT level FROM evp_entries")}
            result["schema_ok"] = (
                metadata.get("schema_name") == "jenglish-evp-sqlite"
                and metadata.get("schema_version") == "1"
                and required.issubset(cols)
                and levels.issubset(set(LEVELS))
            )
    except (sqlite3.Error, OSError) as exc:
        result["error"] = str(exc)
    return result


def _entry_rows(con: sqlite3.Connection, lookup_key: str) -> list[dict[str, Any]]:
    rows = []
    for row in con.execute(
        """
        SELECT entry_id, base_word, lookup_key, guideword, level, part_of_speech, topics
        FROM evp_lookup
        WHERE lookup_key = ?
        ORDER BY entry_id
        """,
        (lookup_key,),
    ):
        entry_id, base_word, key, guideword, level, pos, topics = row
        if (pos or "") not in CONTENT_POS:
            continue
        rows.append(
            {
                "candidate_id": int(entry_id),
                "base_word": base_word,
                "lookup_key": key,
                "guideword": guideword,
                "level": level,
                "part_of_speech": pos,
                "topics": topics,
            }
        )
    return rows


def _candidate_entries(con: sqlite3.Connection, surface: str) -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    used_lookup_keys: list[str] = []
    seen_ids: set[int] = set()
    for key in lemma_candidates(surface):
        rows = _entry_rows(con, key)
        if not rows:
            continue
        used_lookup_keys.append(key)
        for row in rows:
            if row["candidate_id"] not in seen_ids:
                entries.append(row)
                seen_ids.add(row["candidate_id"])
    return entries, used_lookup_keys


def _is_capitalised(surface: str) -> bool:
    return bool(surface and surface[0].isupper())


def prepare(article: dict[str, Any], db_path: Path) -> dict[str, Any]:
    check = validate_asset(db_path)
    if not check.get("schema_ok"):
        raise ValueError(f"EVP SQLite asset is unavailable or invalid: {check}")

    occurrences: list[dict[str, Any]] = []
    unclassified = 0
    with _connect(db_path) as con:
        for block in article.get("body", []):
            if block.get("type") != "paragraph":
                continue
            paragraph = int(block["number"])
            text = str(block.get("text") or "")
            for match in TOKEN_RE.finditer(text):
                surface = match.group(0)
                normalised_surface = _normalise(surface)
                contraction_head = normalised_surface.split("'", 1)[0]
                if normalised_surface in FUNCTION_LIKE or ("'" in normalised_surface and contraction_head in FUNCTION_LIKE):
                    continue
                entries, lookup_keys = _candidate_entries(con, surface)
                if not entries:
                    unclassified += 1
                    continue

                levels = sorted({entry["level"] for entry in entries}, key=LEVELS.index)
                capitalised = _is_capitalised(surface)
                needs_decision = capitalised or len(levels) > 1
                occurrence_id = f"p{paragraph}:{match.start()}-{match.end()}"
                item: dict[str, Any] = {
                    "occurrence_id": occurrence_id,
                    "paragraph": paragraph,
                    "start": match.start(),
                    "end": match.end(),
                    "surface": surface,
                    "context": text,
                    "lookup_keys": lookup_keys,
                    "capitalised": capitalised,
                    "candidates": entries,
                    "status": "decision_required" if needs_decision else "auto",
                }
                if not needs_decision:
                    item["selected_level"] = levels[0]
                occurrences.append(item)

    return {
        "schema_version": "jenglish-cefr-candidates-v1",
        "adapter": "evp_sqlite",
        "source": {
            "dataset_name": check.get("metadata", {}).get("dataset_name"),
            "schema_name": check.get("metadata", {}).get("schema_name"),
            "schema_version": check.get("metadata", {}).get("schema_version"),
            "source_sha256": check.get("metadata", {}).get("source_sha256"),
        },
        "counting": {
            "unit": "word_occurrence",
            "body_paragraphs_only": True,
            "included_parts_of_speech": sorted(CONTENT_POS),
            "function_like_words": "excluded_by_adapter_closed_class",
            "proper_names": "host_decision_then_skip",
            "denominator": "classified_occurrences_only",
        },
        "occurrences": occurrences,
        "summary": {
            "matched_occurrences": len(occurrences),
            "decision_required": sum(1 for x in occurrences if x["status"] == "decision_required"),
            "auto_resolved": sum(1 for x in occurrences if x["status"] == "auto"),
            "unclassified_tokens": unclassified,
        },
    }


def finalize(candidates: dict[str, Any], decisions: dict[str, Any] | None) -> dict[str, Any]:
    if candidates.get("adapter") != "evp_sqlite":
        raise ValueError("candidate file adapter is not evp_sqlite")
    decision_map = (decisions or {}).get("decisions", {})
    if not isinstance(decision_map, dict):
        raise ValueError("decisions must be an object mapping occurrence_id to candidate_id or null")

    counts: Counter[str] = Counter()
    missing: list[str] = []
    invalid: list[str] = []

    for item in candidates.get("occurrences", []):
        status = item.get("status")
        if status == "auto":
            level = item.get("selected_level")
            if level not in LEVELS:
                raise ValueError(f"invalid auto-selected CEFR level for {item.get('occurrence_id')}")
            counts[level] += 1
            continue

        oid = item.get("occurrence_id")
        if oid not in decision_map:
            missing.append(str(oid))
            continue
        chosen = decision_map[oid]
        if chosen is None:
            # Host explicitly identified a proper name or no fitting EVP sense.
            continue
        try:
            chosen_id = int(chosen)
        except (TypeError, ValueError):
            invalid.append(str(oid))
            continue
        by_id = {int(row["candidate_id"]): row for row in item.get("candidates", [])}
        if chosen_id not in by_id:
            invalid.append(str(oid))
            continue
        counts[by_id[chosen_id]["level"]] += 1

    if missing:
        raise ValueError("missing CEFR decisions for: " + ", ".join(missing[:20]) + (" ..." if len(missing) > 20 else ""))
    if invalid:
        raise ValueError("invalid CEFR decisions for: " + ", ".join(invalid[:20]) + (" ..." if len(invalid) > 20 else ""))

    total = sum(counts.values())
    if total <= 0:
        raise ValueError("no classified EVP word occurrences remain after decisions")

    raw = {level: counts[level] * 100.0 / total for level in LEVELS}
    rounded = {level: round(raw[level], 1) for level in LEVELS}
    # Keep the minimal renderer contract numerically stable at one decimal place.
    delta = round(100.0 - sum(rounded.values()), 1)
    if delta:
        # Adjust the largest bucket; this changes at most 0.2 percentage points.
        target = max(LEVELS, key=lambda level: counts[level])
        rounded[target] = round(rounded[target] + delta, 1)

    return {
        "levels": {
            level: {"percentage": rounded[level]}
            for level in LEVELS
        }
    }
