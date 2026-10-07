# Sentence analysis depth specification

This reference preserves the deterministic sentence-selection logic from `te-weekly-json-study-notes` for `june-english-core-read-study-note-v1`.

## Depth semantics

Depth is selection/analysis breadth, not sentence difficulty.

- **Depth 1 — Core**: the original high-precision v8 long/complex-sentence rules.
- **Depth 2 — Structural**: structures that often make Chinese learners lose the main clause or misread modification/embedding.
- **Depth 3 — Extended**: additional high-value advanced reading and writing structures.

Selection is cumulative: requesting Depth 2 includes Depth 1+2; requesting Depth 3 includes Depth 1+2+3.

`sentence_analysis_depth` defaults to `1` when the user does not specify it.

The classifier evaluates the established rules internally and may retain `reason`/`selection_depth` only as audit data during generation. In final study-note JSON, selected sentences are represented only by a non-null `sentences[].sentence_note_zh`; ordinary sentences use `null`. Internal rule metadata is not emitted.

## Depth 1 — Core

Preserve these five v8 rules exactly:

1. 38 or more words.
2. 34 or more words with at least three comma, semicolon, colon, dash, or list separators.
3. 30 or more words with at least two original v8 subordinate/relative markers.
4. 28 or more words with strong punctuation plus at least two original v8 subordinate markers.
5. 32 or more words with a `from ... to ...` range structure.

Keep the original Depth 1 reason strings unchanged in internal diagnostics for backward traceability.

## Depth 2 — Structural

### Long insertion

Trigger when all apply:

- sentence has at least 22 words;
- there is a comma-pair, dash-pair, or parenthetical insertion;
- insertion has at least 8 words;
- insertion is no more than 55% of sentence word count;
- insertion contains at least one structural signal: high-confidence relative/subordinate marker, participial/non-finite signal, or multiple post-modifying prepositions.

Reason: `long insertion`.

### Complex appositive insertion

Trigger when all apply:

- sentence has at least 20 words;
- inserted appositive span has at least 7 words;
- span behaves like a noun phrase rather than beginning with a subordinate/relative marker;
- span contains at least one further PP, relative marker, or participial modifier.

Reason: `complex appositive insertion`.

### Multi-layer post-modification

Trigger when all apply:

- sentence has at least 20 words;
- within a strong-boundary-safe rolling window of at most 18 words there are at least 3 target post-modifying prepositions;
- at least 2 are core signals (`of/by/for/with/from`) or `of` appears at least twice.

Auxiliary signals may include `in/on/among/between/over/under`.

Reason: `multi-layer post-modification`.

### Stacked non-finite compression

Use only high-confidence non-finite signals. Do not select a sentence merely because one `-ing` form appears.

Trigger when either applies:

- sentence has at least 20 words and at least 2 high-confidence non-finite units; or
- sentence has at least 20 words and one non-finite span has at least 8 words and itself contains a high-confidence relative/subordinate structure.

High-confidence signals include `having + participle`, `by + V-ing`, clear initial/comma-linked `V-ing`, linked `while/when/after/before/without + V-ing`, plausible post-nominal `V-ing`, and clear participle + `by/with/from/in` structures.

Reason: `stacked non-finite compression`.

### Complex with-structure

Only detect sentence-initial `With ... ,` or `, with ...` secondary-predication spans.

Trigger when either applies:

- span has 7-11 words and at least 2 predicative signals; or
- span has at least 12 words and at least 1 predicative signal.

Do not treat ordinary short `with + noun` PPs as candidates.

Reason: `complex with-structure`.

### Dense subordinate/relative structure

Use a narrower high-confidence marker set than Depth 1.

Relative markers: `which/who/whom/whose/where`.

Subordinate markers: `although/though/because/if/unless/whereas/whether/when/before/after/until/once`.

Trigger for sentences of at least 24 words when either applies:

- at least 3 high-confidence structural markers; or
- at least 2 markers and at least 1 is a high-confidence relative marker.

Do not use ambiguous `as/since/while` as Depth-2-specific signals.

Reason: `dense subordinate/relative structure`.

### Delayed main predicate / long subject

This remains a confirmed Depth 2 target but is **not enabled in this V1**. Do not approximate it with a weak regex. Enable it only after a detector can identify the main finite predicate with sufficiently high precision.

## Depth 3 — Extended

### Multiple logical relations

For sentences of at least 18 words, trigger when at least 2 distinct high-confidence relation categories occur.

Categories:

- concession: `although/even though/despite/in spite of`;
- condition: `if/unless/provided that/as long as`;
- cause: `because/because of/given that`;
- contrast: `whereas`;
- time: `when/after/before/once/until`;
- purpose: `so that/in order to/so as to`.

Do not use ambiguous `as/since/while` as high-confidence relation signals.

Reason: `multiple logical relations`.

### High-value comparison/correlative framework

Use only high-specificity patterns in V1:

- `not so much A as B`;
- `as much A as B`;
- `the more/less X, the more/less Y`;
- `no more/less X than Y`.

Do not trigger solely on ordinary `more than`, `less than`, or `rather than`.

Reason: `high-value comparison/correlative framework`.

### Marked word order

Detect high-confidence inversion, cleft, or pseudo-cleft forms, including patterns such as:

- `Rarely/Never/Seldom/Hardly/Scarcely/Little + auxiliary ...`;
- `Not until ... + auxiliary ...`;
- `Only when/after/if/once/by/with/through/then ... + auxiliary ...`;
- `So + adjective + be ...`;
- `It is/was X that/who ...`;
- `What ... is/was ...`.

Require at least 8 words.

Reason: `marked word order`.

### Strong parallelism

Use high-confidence repeated frames only. V1 enables:

- at least 3 `by + V-ing` units;
- at least 3 `whether` units;
- explicit `not only ... but also ...`.

Do not infer parallelism from comma count alone. Ordinary `to ... / to ... / to ...` remains outside V1 until precision is tested.

Reason: `strong parallelism`.

### Single fronted compression

For sentences of at least 14 words, detect one clear fronted compressed structure ending at a comma, including:

- `By + V-ing ... ,`;
- `Having ... ,`;
- high-confidence initial `V-ing ... ,`;
- high-confidence initial participial forms such as `Given/Driven/Seen/Faced/Based/Compared ... ,`.

Exclude common non-participial `-ing` starters such as `According`, `Including`, and `During`.

Reason: `fronted compression`.

## Explicit exclusions

- Do not implement `nominalisation density` in this version.
- Do not manually add model-selected candidates outside the deterministic rules.
- Do not label Depth as difficulty; it controls breadth of sentence analysis.
