#!/usr/bin/env python3
"""Deterministic sentence-analysis candidate classification for TE study notes.

Depth semantics:
- 1: Core long/complex-sentence rules retained from v8.
- 2: Structural reading difficulty.
- 3: Extended high-value reading/writing structures.

The classifier always evaluates all enabled Depth 1-3 rules, records every matched
reason, assigns the minimum matching depth as ``selection_depth``, then lets callers
filter by the requested ``sentence_analysis_depth``.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Sequence, Tuple


DEPTH_MIN = 1
DEPTH_MAX = 3

# Depth 1: preserve the v8 marker set and reasons exactly.
SUBORDINATE_MARKERS = {
    "which", "that", "who", "whom", "whose", "where", "when", "while", "because",
    "although", "though", "if", "unless", "since", "whereas", "as", "after", "before",
    "until", "whether", "what", "how", "why", "once", "provided", "despite", "including",
}

# Higher-depth rules intentionally use a narrower high-confidence set.
HIGH_CONF_RELATIVE_MARKERS = {"which", "who", "whom", "whose", "where"}
HIGH_CONF_SUBORDINATE_MARKERS = {
    "although", "though", "because", "if", "unless", "whereas", "whether",
    "when", "before", "after", "until", "once",
}

CORE_POSTMOD_PREPOSITIONS = {"of", "by", "for", "with", "from"}
AUX_POSTMOD_PREPOSITIONS = {"in", "on", "among", "between", "over", "under"}
ALL_POSTMOD_PREPOSITIONS = CORE_POSTMOD_PREPOSITIONS | AUX_POSTMOD_PREPOSITIONS

GERUND_EXCLUSIONS = {
    "according", "including", "during", "following", "concerning", "regarding",
    "considering", "assuming", "pending", "notwithstanding", "something", "anything",
    "nothing", "everything", "morning", "evening", "ceiling", "building",
}

IRREGULAR_PARTICIPLES = {
    "given", "driven", "seen", "taken", "known", "shown", "grown", "written", "built",
    "found", "left", "led", "held", "kept", "lost", "won", "run", "come", "gone",
    "become", "fallen", "chosen", "caught", "thought", "brought", "made", "born",
    "hit", "hurt", "based", "faced", "viewed", "armed", "asked", "pressed", "freed",
    "backed", "encouraged", "spurred", "fuelled", "fueled", "compared",
}

WITH_STATE_WORDS = {
    "high", "low", "strong", "weak", "open", "closed", "ready", "available", "stable",
    "volatile", "likely", "unlikely", "unable", "able", "higher", "lower", "unchanged",
    "intact", "underway", "ahead", "behind", "up", "down",
}

LOGICAL_RELATION_PATTERNS: Sequence[Tuple[str, Sequence[str]]] = (
    ("concession", (r"\beven though\b", r"\balthough\b", r"\bdespite\b", r"\bin spite of\b")),
    ("condition", (r"\bprovided that\b", r"\bas long as\b", r"\bunless\b", r"\bif\b")),
    ("cause", (r"\bbecause of\b", r"\bgiven that\b", r"\bbecause\b")),
    ("contrast", (r"\bwhereas\b",)),
    ("time", (r"\bwhen\b", r"\bafter\b", r"\bbefore\b", r"\bonce\b", r"\buntil\b")),
    ("purpose", (r"\bso that\b", r"\bin order to\b", r"\bso as to\b")),
)

AUXILIARIES = (
    "do", "does", "did", "is", "are", "was", "were", "has", "have", "had",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
)
AUX_PATTERN = r"(?:" + "|".join(AUXILIARIES) + r")"


REASON_DEPTH = {
    # Depth 1 reasons: exact v8 strings.
    "38+ words": 1,
    "34+ words with three or more clause/list separators": 1,
    "30+ words with multiple subordination/relative markers": 1,
    "28+ words with strong punctuation and multiple subordination markers": 1,
    "32+ words with from...to... range structure": 1,
    # Depth 2.
    "long insertion": 2,
    "complex appositive insertion": 2,
    "multi-layer post-modification": 2,
    "stacked non-finite compression": 2,
    "complex with-structure": 2,
    "dense subordinate/relative structure": 2,
    # Delayed main predicate / long subject remains a confirmed target but is not
    # enabled until a sufficiently precise detector is validated.
    # Depth 3.
    "multiple logical relations": 3,
    "high-value comparison/correlative framework": 3,
    "marked word order": 3,
    "strong parallelism": 3,
    "fronted compression": 3,
}


def validate_depth(depth: int) -> int:
    if not isinstance(depth, int) or isinstance(depth, bool) or not (DEPTH_MIN <= depth <= DEPTH_MAX):
        raise ValueError(f"sentence analysis depth must be an integer from {DEPTH_MIN} to {DEPTH_MAX}")
    return depth


def split_sentences(text: str) -> List[str]:
    """Split English prose into approximate sentences while preserving punctuation."""
    protected = text
    abbreviations = {
        "Mr.": "Mr<dot>", "Mrs.": "Mrs<dot>", "Ms.": "Ms<dot>", "Dr.": "Dr<dot>",
        "Prof.": "Prof<dot>", "St.": "St<dot>",
    }
    for old, new in abbreviations.items():
        protected = protected.replace(old, new)
    pieces = re.split(r"(?<=[.!?])\s+(?=[\"'“‘A-Z])", protected)
    return [piece.replace("<dot>", ".").strip() for piece in pieces if piece.strip()]


def words(text: str) -> List[str]:
    return re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", text)


def word_count(sentence: str) -> int:
    return len(words(sentence))


def subordinate_count(sentence: str) -> int:
    tokens = [token.lower() for token in re.findall(r"[A-Za-z]+", sentence)]
    return sum(1 for token in tokens if token in SUBORDINATE_MARKERS)


def clause_separator_count(sentence: str) -> int:
    return len(re.findall(r"[,;:]|—|–| - ", sentence))


def depth1_reasons(sentence: str) -> List[str]:
    """Return the original v8 Depth 1 reasons without changing thresholds or wording."""
    count = word_count(sentence)
    clauses = clause_separator_count(sentence)
    subords = subordinate_count(sentence)
    has_strong_punctuation = bool(re.search(r"[;:]|—|–| - ", sentence))
    reasons: List[str] = []
    if count >= 38:
        reasons.append("38+ words")
    if count >= 34 and clauses >= 3:
        reasons.append("34+ words with three or more clause/list separators")
    if count >= 30 and subords >= 2:
        reasons.append("30+ words with multiple subordination/relative markers")
    if count >= 28 and has_strong_punctuation and subords >= 2:
        reasons.append("28+ words with strong punctuation and multiple subordination markers")
    if count >= 32 and re.search(r"\bfrom\b.+\bto\b", sentence, flags=re.IGNORECASE):
        reasons.append("32+ words with from...to... range structure")
    return reasons


def _token_count(text: str) -> int:
    return len(words(text))


def _marker_count(text: str, markers: Iterable[str]) -> int:
    token_list = [token.lower() for token in re.findall(r"[A-Za-z]+", text)]
    marker_set = set(markers)
    return sum(1 for token in token_list if token in marker_set)


def _relative_count(text: str) -> int:
    return _marker_count(text, HIGH_CONF_RELATIVE_MARKERS)


def _high_conf_structural_count(text: str) -> int:
    return _marker_count(text, HIGH_CONF_RELATIVE_MARKERS | HIGH_CONF_SUBORDINATE_MARKERS)


def _candidate_insertion_spans(sentence: str) -> List[Dict[str, Any]]:
    spans: List[Dict[str, Any]] = []

    # Parentheses are naturally paired.
    for match in re.finditer(r"\(([^()]*)\)", sentence):
        content = match.group(1).strip()
        if content:
            spans.append({"kind": "parentheses", "text": content, "start": match.start(), "end": match.end()})

    # Em/en-dash pairs.
    for match in re.finditer(r"(?:—|–| - )\s*(.+?)\s*(?:—|–| - )", sentence):
        content = match.group(1).strip()
        if content:
            spans.append({"kind": "dash", "text": content, "start": match.start(), "end": match.end()})

    # Commas are ambiguous. Consider spans between pairs with material on both sides.
    comma_positions = [m.start() for m in re.finditer(r",", sentence)]
    for i, left in enumerate(comma_positions):
        for right in comma_positions[i + 1:]:
            content = sentence[left + 1:right].strip()
            if not content:
                continue
            before = sentence[:left].strip()
            after = sentence[right + 1:].strip()
            if _token_count(before) < 1 or _token_count(after) < 2:
                continue
            spans.append({"kind": "comma", "text": content, "start": left, "end": right + 1})
    return spans


def _gerund_matches(text: str) -> List[re.Match[str]]:
    matches: List[re.Match[str]] = []
    for match in re.finditer(r"\b[A-Za-z][A-Za-z-]*ing\b", text, flags=re.IGNORECASE):
        token = match.group(0).lower()
        if token not in GERUND_EXCLUSIONS:
            matches.append(match)
    return matches


def _participle_signal_count(text: str) -> int:
    count = len(_gerund_matches(text))
    lower = text.lower()
    for token in IRREGULAR_PARTICIPLES:
        count += len(re.findall(rf"\b{re.escape(token)}\b", lower))
    count += len(re.findall(r"\b[A-Za-z]+ed\b", text, flags=re.IGNORECASE))
    return count


def _insertion_has_structure(text: str) -> bool:
    if _high_conf_structural_count(text) >= 1:
        return True
    if _participle_signal_count(text) >= 1:
        return True
    preps = [token.lower() for token in re.findall(r"[A-Za-z]+", text) if token.lower() in ALL_POSTMOD_PREPOSITIONS]
    return len(preps) >= 2


def has_long_insertion(sentence: str) -> bool:
    if word_count(sentence) < 22:
        return False
    total = max(word_count(sentence), 1)
    for span in _candidate_insertion_spans(sentence):
        span_words = _token_count(span["text"])
        if span_words < 8 or span_words / total > 0.55:
            continue
        if _insertion_has_structure(span["text"]):
            return True
    return False


def has_complex_appositive(sentence: str) -> bool:
    if word_count(sentence) < 20:
        return False
    structural_starters = HIGH_CONF_RELATIVE_MARKERS | HIGH_CONF_SUBORDINATE_MARKERS
    for span in _candidate_insertion_spans(sentence):
        text = span["text"].strip()
        if _token_count(text) < 7:
            continue
        first_tokens = [token.lower() for token in re.findall(r"[A-Za-z]+", text)[:2]]
        if first_tokens and first_tokens[0] in structural_starters:
            continue
        starts_like_np = bool(re.match(r"^(?:a|an|the|one|another|its|their|his|her)\b", text, flags=re.IGNORECASE))
        if not starts_like_np:
            continue
        prep_count = sum(1 for token in re.findall(r"[A-Za-z]+", text.lower()) if token in ALL_POSTMOD_PREPOSITIONS)
        if _relative_count(text) >= 1 or _participle_signal_count(text) >= 1 or prep_count >= 1:
            return True
    return False


def has_multi_layer_postmodification(sentence: str) -> bool:
    if word_count(sentence) < 20:
        return False
    # Do not let a chain cross a strong clause boundary.
    segments = re.split(r"[;:]|—|–| - ", sentence)
    for segment in segments:
        token_list = [token.lower() for token in re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", segment)]
        if len(token_list) < 6:
            continue
        for start in range(len(token_list)):
            window = token_list[start:start + 18]
            if len(window) < 6:
                continue
            target = [token for token in window if token in ALL_POSTMOD_PREPOSITIONS]
            if len(target) < 3:
                continue
            core_count = sum(1 for token in target if token in CORE_POSTMOD_PREPOSITIONS)
            of_count = target.count("of")
            if core_count >= 2 or of_count >= 2:
                return True
    return False


def _span_to_next_boundary(sentence: str, start: int) -> str:
    tail = sentence[start:]
    match = re.search(r"[,;:]|—|–| - ", tail[1:])
    if match:
        return tail[:match.start() + 1].strip(" ,;:—–-")
    return tail.strip(" ,;:—–-")


def nonfinite_units(sentence: str) -> List[Dict[str, Any]]:
    units: List[Dict[str, Any]] = []
    patterns: Sequence[Tuple[str, str]] = (
        ("by_gerund", r"\bby\s+[A-Za-z][A-Za-z-]*ing\b"),
        ("having", r"\bhaving\s+(?:been\s+)?[A-Za-z][A-Za-z-]*\b"),
        ("gerund", r"(?:^|,\s+)([A-Za-z][A-Za-z-]*ing)\b"),
        ("linked_gerund", r"\b(?:while|when|after|before|without)\s+[A-Za-z][A-Za-z-]*ing\b"),
        ("postnominal_gerund", r"\b[A-Za-z][A-Za-z-]*s\s+[A-Za-z][A-Za-z-]*ing\b"),
        ("participle_prep", r"(?:^|,\s+)([A-Za-z][A-Za-z-]*(?:ed|en)|Given|Driven|Seen|Taken|Known|Built|Found|Left|Led|Made|Born|Hit|Hurt|Based|Faced|Viewed|Armed|Asked|Pressed|Freed|Backed|Encouraged|Spurred|Fuelled|Fueled|Compared)\s+(?:by|with|from|in)\b"),
    )
    occupied: List[Tuple[int, int]] = []
    for kind, pattern in patterns:
        for match in re.finditer(pattern, sentence, flags=re.IGNORECASE):
            matched_text = match.group(0)
            gerunds = _gerund_matches(matched_text)
            if kind in {"by_gerund", "gerund", "linked_gerund", "postnominal_gerund"} and not gerunds:
                continue
            start, end = match.span()
            if any(not (end <= old_start or start >= old_end) for old_start, old_end in occupied):
                continue
            span_text = _span_to_next_boundary(sentence, start)
            units.append({
                "kind": kind,
                "start": start,
                "end": end,
                "span": span_text,
                "word_count": _token_count(span_text),
            })
            occupied.append((start, end))
    units.sort(key=lambda item: (item["start"], item["end"]))
    return units


def has_stacked_nonfinite(sentence: str) -> bool:
    if word_count(sentence) < 20:
        return False
    units = nonfinite_units(sentence)
    if len(units) >= 2:
        return True
    return any(
        unit["word_count"] >= 8 and _high_conf_structural_count(unit["span"]) >= 1
        for unit in units
    )


def _with_spans(sentence: str) -> List[str]:
    spans: List[str] = []
    initial = re.match(r"^\s*With\b(.+?),", sentence, flags=re.IGNORECASE)
    if initial:
        spans.append("With" + initial.group(1))
    for match in re.finditer(r",\s+with\b([^,;:—–]+)", sentence, flags=re.IGNORECASE):
        spans.append("with" + match.group(1))
    return [span.strip() for span in spans if span.strip()]


def _with_predicative_signal_count(text: str) -> int:
    token_list = [token.lower() for token in re.findall(r"[A-Za-z]+", text)]
    gerunds = [token for token in token_list if token.endswith("ing") and token not in GERUND_EXCLUSIONS]
    participles = [token for token in token_list if token.endswith("ed") or token in IRREGULAR_PARTICIPLES]
    states = [token for token in token_list if token in WITH_STATE_WORDS]
    return len(gerunds) + len(participles) + len(states)


def has_complex_with_structure(sentence: str) -> bool:
    for span in _with_spans(sentence):
        count = _token_count(span)
        signals = _with_predicative_signal_count(span)
        if 7 <= count <= 11 and signals >= 2:
            return True
        if count >= 12 and signals >= 1:
            return True
    return False


def has_dense_subordination(sentence: str) -> bool:
    if word_count(sentence) < 24:
        return False
    relative = _relative_count(sentence)
    subordinate = _marker_count(sentence, HIGH_CONF_SUBORDINATE_MARKERS)
    total = relative + subordinate
    return total >= 3 or (total >= 2 and relative >= 1)


def logical_relation_categories(sentence: str) -> List[str]:
    lower = sentence.lower()
    categories: List[str] = []
    for category, patterns in LOGICAL_RELATION_PATTERNS:
        if any(re.search(pattern, lower, flags=re.IGNORECASE) for pattern in patterns):
            categories.append(category)
    return categories


def has_multiple_logical_relations(sentence: str) -> bool:
    return word_count(sentence) >= 18 and len(logical_relation_categories(sentence)) >= 2


def has_high_value_comparison(sentence: str) -> bool:
    patterns = (
        r"\bnot\s+so\s+much\b.+\bas\b",
        r"\bas\s+much\b.+\bas\b",
        r"\bthe\s+(?:more|less)\b.+?,\s*the\s+(?:more|less)\b",
        r"\bno\s+(?:more|less)\b.+\bthan\b",
    )
    return any(re.search(pattern, sentence, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def has_marked_word_order(sentence: str) -> bool:
    text = sentence.strip()
    if word_count(text) < 8:
        return False
    patterns = (
        rf"^(?:Rarely|Never|Seldom|Hardly|Scarcely|Little)\b\s+{AUX_PATTERN}\b",
        rf"^Not\s+until\b.+?\b{AUX_PATTERN}\b",
        rf"^Only\s+(?:when|after|if|once|by|with|through|then)\b.+?\b{AUX_PATTERN}\b",
        r"^So\s+[A-Za-z-]+\s+(?:is|are|was|were)\b",
        r"^It\s+(?:is|was)\b.+?\b(?:that|who)\b",
        r"^What\b.+?\b(?:is|was)\b",
    )
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def has_strong_parallelism(sentence: str) -> bool:
    by_gerunds = re.findall(r"\bby\s+[A-Za-z][A-Za-z-]*ing\b", sentence, flags=re.IGNORECASE)
    if len(by_gerunds) >= 3:
        return True
    if len(re.findall(r"\bwhether\b", sentence, flags=re.IGNORECASE)) >= 3:
        return True
    return bool(
        re.search(r"\bnot\s+only\b", sentence, flags=re.IGNORECASE)
        and re.search(r"\bbut\s+also\b", sentence, flags=re.IGNORECASE)
    )


def has_fronted_compression(sentence: str) -> bool:
    if word_count(sentence) < 14:
        return False
    text = sentence.strip()
    patterns = (
        r"^By\s+[A-Za-z][A-Za-z-]*ing\b.+?,",
        r"^Having\b.+?,",
        r"^[A-Z][A-Za-z-]*ing\b.+?,",
        r"^(?:Given|Driven|Seen|Taken|Known|Built|Found|Left|Led|Made|Born|Hit|Hurt|Based|Faced|Viewed|Armed|Asked|Pressed|Freed|Backed|Encouraged|Spurred|Fuelled|Fueled|Compared)\b.+?,",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            continue
        first_word_match = re.match(r"^[A-Za-z-]+", text)
        first_word = first_word_match.group(0).lower() if first_word_match else ""
        if first_word in GERUND_EXCLUSIONS:
            continue
        return True
    return False


def depth2_reasons(sentence: str) -> List[str]:
    reasons: List[str] = []
    if has_long_insertion(sentence):
        reasons.append("long insertion")
    if has_complex_appositive(sentence):
        reasons.append("complex appositive insertion")
    if has_multi_layer_postmodification(sentence):
        reasons.append("multi-layer post-modification")
    if has_stacked_nonfinite(sentence):
        reasons.append("stacked non-finite compression")
    if has_complex_with_structure(sentence):
        reasons.append("complex with-structure")
    if has_dense_subordination(sentence):
        reasons.append("dense subordinate/relative structure")
    return reasons


def depth3_reasons(sentence: str) -> List[str]:
    reasons: List[str] = []
    if has_multiple_logical_relations(sentence):
        reasons.append("multiple logical relations")
    if has_high_value_comparison(sentence):
        reasons.append("high-value comparison/correlative framework")
    if has_marked_word_order(sentence):
        reasons.append("marked word order")
    if has_strong_parallelism(sentence):
        reasons.append("strong parallelism")
    if has_fronted_compression(sentence):
        reasons.append("fronted compression")
    return reasons


def classify_sentence(sentence: str) -> Dict[str, Any] | None:
    reasons = depth1_reasons(sentence) + depth2_reasons(sentence) + depth3_reasons(sentence)
    if not reasons:
        return None
    selection_depth = min(REASON_DEPTH[reason] for reason in reasons)
    return {
        "sentence": sentence,
        "word_count": word_count(sentence),
        "selection_depth": selection_depth,
        "reasons": reasons,
    }


def sentence_analysis_candidates(text: str, analysis_depth: int = 1) -> List[Dict[str, Any]]:
    analysis_depth = validate_depth(analysis_depth)
    candidates: List[Dict[str, Any]] = []
    for sentence in split_sentences(text):
        classified = classify_sentence(sentence)
        if classified and classified["selection_depth"] <= analysis_depth:
            candidates.append(classified)
    return candidates
