# Rendering contract

Canonical JSON optimises future functionality; presentation preserves the established `te-notes-html-pdf` learner experience. Keep rendering logic separate from learning analysis.

## Shared behaviour

HTML and LaTeX/PDF consume the same structured study data. Renderers do no learning analysis. Sentence-aligned translations are reconstructed into one continuous Chinese paragraph. Preserve the established JEnglish title, summary, paragraph-card, note-panel, highlighting, and vocabulary-appendix hierarchy while allowing General Studynote additions such as source headings and optional CEFR information.

`definition_en` remains canonical lexical data for downstream/API use. Do not display it in learner-facing HTML or PDF.

## Title area

Keep English/Chinese title, optional English/Chinese subtitle, available source metadata, source link, and audio control when an audio URL exists. If CEFR exists, place `estimated_reading_level` at the bottom of the title area using the exact learner-facing label `CEFR level: X`.

## Summary

When `intro_note` is present, preserve the established `全文导读｜Summary` block with the three inline SVG icons and the `全文概要`, `结构主线`, and `写作特色` items. When `intro_note=null`, omit the block rather than inventing summary content.

## Headings

Preserve source heading positions and hierarchy 1/2/3 in HTML and LaTeX. Render headings full-width outside paragraph cards, with English heading and Chinese translation. Level controls visual hierarchy/spacing. Do not flatten levels.

## HTML typography

Use the bundled HTML fonts under `assets/fonts/` for the learner-facing serif content:

- English serif: Lora Regular/Bold/Italic;
- Chinese serif: Noto Serif SC Regular/Bold;
- IPA: Noto Serif Regular.

At render time, create per-document font subsets from the exact study content and embed those subsets in the HTML as data-URI `@font-face` resources. The resulting HTML must be self-contained and must not depend on the viewer computer having Lora/Noto installed. Small UI/sans elements (paragraph-function labels, block labels, pills, controls) keep the existing system sans stack; emoji and inline SVG icons remain unchanged.

The HTML font-subset step requires `fontTools`; fail clearly if the dependency or any required bundled font asset is missing rather than silently changing the learner-facing serif font.

## HTML paragraph cards

Match the established TE screen layout rather than the PDF column ratio:

- default screen left width is 61%, with the note panel taking the remaining width around a 14px divider;
- keep the draggable divider and allow the established 42%-72% interactive left-width range;
- use the full-width `💡` + paragraph-function row;
- left panel shows `English original`, the complete English paragraph, `中文直译`, the continuous Chinese paragraph, then all non-null sentence analyses;
- right panel shows `笔记｜Note`, `重点单词` first, then `短语 / 表达`;
- recover paragraph-vocabulary IPA, POS, and labels from the top-level lexical master through `lexical_id`; do not duplicate those fields in canonical paragraph vocabulary;
- paragraph-selected study vocabulary is red; top-level/database-only vocabulary keeps the established ordinary-text dotted underline unless another active phrase/sentence highlight applies;
- preserve right-panel background `#e2e7bf`, divider `#83a78d`, red learning highlights, sentence underlining, internal vocabulary links/return links, and the established 840px responsive breakpoint;
- preserve the TE print CSS behaviour, including the 62% HTML-print left width and vocabulary two-column rules;
- end the screen HTML with exactly `© JEnglish | AI-generated.`.

## CEFR word-difficulty section

When a word-level CEFR chart was generated from current-run temporary statistics, render an independent section after the final body block and before the vocabulary appendix.

- center the section title exactly as `单词难度统计`;
- place the CEFR chart immediately below the title;
- keep the chart outside canonical study JSON and do not add source/provider details to the learner-facing section;
- use the minimal chart contract from `cefr.md`: A1-C2 x-axis labels, a thin green baseline, percentage labels above bars, and no y-axis/grid/chart title/explanatory text;
- in HTML screen layout, keep normal document flow between the article body, this section, and the vocabulary appendix;
- in HTML print CSS, start this section on a new page and allow the vocabulary appendix to continue immediately after it without another forced page break.

If no word-level chart exists, omit this section completely and retain the normal vocabulary appendix separation/page-break behaviour.

## Vocabularies appendix

Render `Vocabularies｜生词表` using the established two-column grid, target highlighting, and return-to-first-occurrence control. Show lemma, labels, British IPA when available, POS, and Chinese meaning. Do not show `definition_en`.

When a CEFR word-difficulty section is present, the vocabulary appendix follows it directly. When that section is absent, preserve the existing standalone vocabulary appendix spacing/page-break behaviour.

## PDF

Read `pdf-runtime.md` for the shared template, deterministic punctuation/spacing, whole-sentence underline nesting, graphics transport, and diagnostics.

Keep the General PDF data contract and article typography unchanged, but match the established `te-notes-html-pdf` learner-facing PDF presentation for the following elements:

- keep A4 portrait with 10mm top, 12mm bottom, 9mm left/right margins, 58/42 columns with 4mm gap, centered current/total page number, and the two-column vocabulary appendix;
- keep the existing fixed PDF article fonts: Libertinus for English, FandolSong/FandolHei for CJK, and the approved independent watermark font policy; do not reuse the bundled HTML fonts for PDF;
- in `全文导读｜Summary`, use 1.3mm after the title, then `leftskip=4mm`, `rightskip=1mm`, and `parskip=1.5mm` for the three summary paragraphs;
- in the green right note panel, omit the `笔记｜Note` heading; render vocabulary and phrases as TE-style bullet lists, show vocabulary British IPA/POS/labels, put Chinese meaning on the following line, render `note_zh` smaller/dark gray, and separate vocabulary from phrases with the established thin rule; use zero before/after skip on the note box;
- render sentence-analysis boxes with 1.7mm preceding space, 2.2mm left/right padding, 1.2mm top/bottom padding, and a 2.1pt `#8A5A2B` west rule while preserving the existing 9.6/16.6 text size/leading;
- in English text, keep study vocabulary and phrases red, render database-only vocabulary with the established gray dotted underline when no active sentence/phrase highlight overrides it, and render sentence-analysis ranges with the established red underline;
- immediately after entering the left `paracol` column and immediately after `\switchcolumn`, explicitly set `\columncolor{black}`. This is required to prevent a breakable right-note box from leaking white text colour into the next page when a paragraph crosses a page boundary;
- when a CEFR chart exists, force a page break after the article body, render the centered `单词难度统计` title and chart, then render `Vocabularies｜生词表` and the vocabulary grid directly afterwards with no second forced page break. The chart size/spacing may be adjusted modestly so the vocabulary appendix can normally begin on the same page;
- when no CEFR chart exists, preserve the existing forced new page before the vocabulary appendix;
- render the `JUNE` watermark at page centre, 60 degrees, gray 0.58, opacity 0.16, Multiply blend mode, and 218pt. Use an independent watermark font that prefers Arimo, then Noto Sans, then the current General sans family. Do not change the article fonts.

Keep `definition_en` in canonical JSON but do not display it in the learner-facing PDF. Keep the existing XeLaTeX provider policy unchanged.
