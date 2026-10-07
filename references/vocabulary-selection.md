# Vocabulary and phrase selection

Use the same learner profile and pedagogical selection logic proven in `te-weekly-json-study-notes`: upper-intermediate to advanced Chinese learners targeting high-quality reading/writing plus GRE/GMAT and IELTS.

Scan sentence by sentence and select by comprehension value, register, reusability, and local importance. Do not impose quotas or balance counts for layout.

## Paragraph vocabulary
Use standalone words only. Prioritise words that materially affect comprehension, higher-register/abstract GRE/GMAT vocabulary, IELTS Academic reading vocabulary, and useful news/business/politics/science/policy vocabulary. Ordinary A1-B1 words are normally excluded unless the contextual sense is special or misleading.

During the semantic draft, each selected word may temporarily include `pos`, `labels`, and `definition_en` so deterministic enrichment can build the lexical master. Final paragraph shape is only: `surface`, `lemma`, `lexical_id`, `meaning_zh`, `note_zh`.

## Phrase notes
Use multi-word expressions, collocations, cohesion/discourse expressions, and reusable constructions. `term` is the canonical/base learning form; `surface` is an exact source substring. Keep `explanation_zh` and shared labels.

## Labels
Define labels once for both words and phrases. Normalise `IELTS Academic` to `IELTS`. Paragraph learning CEFR labels are C1/C2 only; do not add A1-B2, and never add both C1 and C2 to one item. Preserve useful labels such as `GRE/GMAT`, `IELTS`, `C1`, `C2`, `business`, `cohesion`.
