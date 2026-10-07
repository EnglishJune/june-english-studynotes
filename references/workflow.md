# Workflow

## Required sequence
1. Run `scripts/preflight.py` for the capabilities needed by this run. It verifies the bundled HTML fonts in addition to Python/package/PDF capabilities and reports the configured CEFR word-statistics adapter/data asset.
2. Canonicalise the input to `english-core-read-article-note-v1`.
   - DOCX: run `scripts/article/extract_docx.py`, then normalise.
   - TXT: run `scripts/article/extract_txt.py`, then normalise.
   - pasted text: create adapter JSON with `text`, then normalise.
   - PDF: use host document/PDF understanding to recover title/subtitle/headings/paragraphs/italics, then normalise. Do not use OCR unless a host explicitly provides a reliable path and the user asked for it.
3. Run `scripts/article/validate_article.py`. Stop if canonical article validation fails.
4. Run `scripts/study/build_study_skeleton.py`, using `config/study.json` unless the user explicitly supplies `sentence_analysis_depth=1|2|3` for the current run.
5. Fill semantic study content following `paragraph-notes.md`, `sentence-analysis.md`, and `vocabulary-selection.md`.
6. Run `scripts/vocabulary/prepare_vocabularies.py ... --ipa-status-json ipa_status.json`. It must attempt OALD9 then direct Youdao and mark every unresolved exact lemma `host_lookup_required` before any compound fallback. For those lemmas, use host web/search on `dict.youdao.com`, write exact British evidence as `{"lemma":{"ipa_uk":"/.../","source":"youdao_web"}}`, and run `scripts/vocabulary/resolve_ipa.py ... --runtime-ipa-json runtime_ipa.json`. An empty `{}` runtime file means the host-level Youdao stage was completed with no usable result and allows compound fallback to proceed. If still unresolved, optional broader reliable British evidence may be supplied separately through `--reliable-ipa-json`; otherwise leave `uk_phonetic` null. Fill blank lexical-master semantic fields (`pos`, `definition_en`, `meaning_zh`) from article context. Then run `scripts/vocabulary/finalize_vocabularies.py`.
7. If CEFR is enabled, follow `cefr.md`.
   - Set canonical `cefr.estimated_reading_level` by holistic full-article model judgement.
   - Keep canonical CEFR data limited to `estimated_reading_level`; do not store provider-specific CEFR metadata or word-level statistics in canonical study JSON.
   - If `config/cefr.json` enables word statistics and its configured adapter/data asset passes preflight, run `scripts/cefr/build_cefr_statistics.py prepare` on the canonical article.
   - Resolve only the adapter's `decision_required` occurrences by selecting a supplied contextual candidate ID or `null`; never invent word levels.
   - Run `scripts/cefr/build_cefr_statistics.py finalize` to produce temporary source-neutral `cefr_statistics.json`, then generate `cefr_statistics.png` with `scripts/cefr/render_cefr_chart.py` and pass it to both renderers.
   - Keep candidates, decisions, temporary statistics, and chart outside canonical study JSON.
   - If the configured word-level adapter/data asset is unavailable or fails, preserve the article-level CEFR judgement and omit only the word-level statistics/chart.
8. Run `scripts/study/validate_study_note.py`. Repair all fatal data errors before rendering.
9. Render HTML with `scripts/render/render_html.py`. It embeds per-document subsets from the bundled Lora/Noto Serif fonts so the learner-facing serif typography is self-contained and stable across computers; small UI/sans labels continue to use the system sans stack. When a CEFR chart exists, render it in a separate `单词难度统计` section between the body and vocabulary appendix.
10. Render LaTeX with `scripts/render/render_latex.py`, then compile the actual generated document via `scripts/render/compile_pdf.py`. For a new/unverified provider environment, inspect that document's PDF pages and compilation diagnostics before treating the provider as verified. Keep the PDF article fonts fixed to the existing TeX Live fonts; `paracol` columns must explicitly initialise text colour to black before content so page breaks cannot inherit white column colour. When a CEFR chart exists, force a page break after the article body, render `单词难度统计` plus the chart, then continue directly into the vocabulary appendix without another forced page break.
11. If PDF compilation is unavailable because providers/environments are unavailable, return HTML plus the `.tex` and a self-contained LaTeX project ZIP produced by `scripts/render/package_latex_project.py`.
12. Apply `config/output.json`: when `expose_structured_json=false`, do not return canonical article/study-note JSON files as deliverables, although they must still be generated and validated internally.

## Strict ordering
Do not continue past a fatal validation failure. CEFR/IPA/provider failures may degrade only according to `error-policy.md`.
