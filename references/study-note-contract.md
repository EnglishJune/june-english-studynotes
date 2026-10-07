# Study-note contract

Schema version: `june-english-core-read-study-note-v1`.

The canonical JSON is learning data, not HTML/LaTeX cache. Rendering-specific anchors/classes/logs must not be stored in it.

## Top level
Preserve canonical article fields and add `title_zh`, `subtitle_zh`, `is_complete_article`, `intro_note`, `sentence_analysis_depth`, optional `cefr`, enriched `body`, and top-level `Vocabularies.entries`.

`sentence_analysis_depth` defaults to 1 and may be explicitly set to 2 or 3 per run. It controls generation breadth. Final renderers display every non-null `sentence_note_zh`; there is no separate renderer display-depth filter.

When `cefr` is non-null, it contains only `estimated_reading_level`. Word-level CEFR statistics and charts are derived rendering artifacts and are never stored in canonical study JSON.

## Completeness
Judge completeness semantically from the provided text, not from length or English percentage. If complete, write all three `intro_note` fields. If incomplete, set `intro_note=null` and describe paragraph roles only within the provided text.

## Heading
Study headings retain `level`, `text`, `inline_runs`, plus `translation_zh`. Do not add paragraph function, vocabulary, phrase notes, or sentence analysis to headings.

## Paragraph
Keep canonical paragraph `text` and `inline_runs`. Add `paragraph_function_zh`, `sentences[]`, paragraph `vocabulary[]`, and `phrase_notes[]`.

Sentence translations are stored sentence-by-sentence, but must be generated from whole-paragraph/whole-article understanding. The presentation layer reconstructs one continuous Chinese paragraph; it must not turn the student-facing layout into sentence cards.
