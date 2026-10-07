# Vocabulary enrichment

## Lexical identity and location
Top-level lexical identity is `(lemma, POS)`. `lexical_id` is a deterministic relationship identifier derived from normalised lemma + POS; it is not a position. Exact source location is stored in `occurrences[{paragraph,sentence,start,end,surface}]`, where offsets are relative to `sentence.text` and must satisfy `sentence.text[start:end] == surface`.

Paragraph vocabulary links to exactly one lexical master through `lexical_id`.

## Top-level entries
Final entries contain `lexical_id`, `lemma`, `forms_in_article`, nullable `uk_phonetic`, `pos`, contextual learner-dictionary-style `definition_en`, concise reusable `meaning_zh`, `labels`, and `occurrences`.

Do not include renderer anchors, source flags, database definitions, paragraph refs, or database difficulty helper fields in final JSON.

## Database supplement
Retain existing rules: NETEM matches only non-function B2/C1/C2 rows and label them `研`; CET supplement only `★` CET-6 rows and label them `CET-6`; no CET-4. Use conservative linguistic lemmatisation only; never derive-family normalise (e.g. `realisation` does not become `realise`).

## British IPA
Use the same proven two-stage Youdao control flow as the current `te-weekly-json-study-notes` skill. For each exact lemma, resolve in this order:

1. exact bundled OALD9 lookup;
2. direct runtime Youdao JSON British-IPA lookup;
3. if unresolved, stop at `host_lookup_required` until the host-level Youdao lookup has been completed;
4. host-level exact-lemma `dict.youdao.com` evidence supplied through `--runtime-ipa-json`;
5. only after that stage is complete, conservative compound fallback;
6. broader reliable British-IPA web evidence when available;
7. unresolved -> final `uk_phonetic: null`.

Never invent IPA from model knowledge and never require ordinary users to type it. Distinguish direct Youdao DNS/network/timeout/HTTP/JSON/schema failures from a valid response containing no British IPA. Detailed diagnostics remain internal.

For hyphenated lemmas, complete the whole-lemma OALD9, direct Youdao, and host-level Youdao stages first. Then resolve visible components with OALD9 followed by direct Youdao and join only when every component is verified. For a closed compound, split automatically only when there is exactly one credible two-part split whose components are independently recognised by OALD9; never guess an ambiguous split.

## Host-level runtime IPA evidence
The Youdao runtime bridge is strict and current-run only. `scripts/vocabulary/resolve_ipa.py --runtime-ipa-json <file>` accepts exactly:

```json
{
  "exact-lemma": {
    "ipa_uk": "/.../",
    "source": "youdao_web"
  }
}
```

Do not accept a bare IPA string, `ipa` instead of `ipa_uk`, or another source label in this file. The host lookup must use the exact lemma and explicit British/UK pronunciation evidence from `dict.youdao.com`. The runtime file may be `{}` when the host-level Youdao stage has been completed but yielded no usable value; its presence allows compound fallback to proceed. Never persist runtime Youdao values into OALD9.

If broader reliable British-pronunciation evidence is used after Youdao and compound fallback, keep it separate in `--reliable-ipa-json` with the same object shape but `source: "reliable_web"`. Values without reliable evidence must be omitted, not guessed.
