---
name: june-smart-english-general-studynote
license: JEnglish Noncommercial License 1.0 (see LICENSE); third-party resources retain their own licenses.
description: Create structured Chinese study notes for general English articles from text-layer PDFs, DOCX, TXT, or pasted text, preserving article structure and italics, producing the established JEnglish learner-facing HTML and 58/42 XeLaTeX/PDF outputs with vocabulary, phrases, sentence analysis, optional CEFR statistics, and British IPA enrichment. Use when a user asks to turn an English article/document into JEnglish-style study notes, bilingual learning material, study-note HTML/PDF, or canonical article/study-note data.
---

# June Smart English General Studynote

Create general English study notes while preserving the proven pedagogical behaviour of `te-weekly-json-study-notes` and the established learner-facing layout of `te-notes-html-pdf`.

Treat canonical JSON as the source of truth. Keep learning analysis separate from rendering. Do not redesign the student-facing layout merely because the canonical data is more granular.

## Repository maintenance

This complete skill directory is independently versioned in [EnglishJune/june-english-studynotes](https://github.com/EnglishJune/june-english-studynotes). Read [AGENTS.md](AGENTS.md) when maintaining its source; [README.md](README.md) is the GitHub-facing usage guide. When this directory lives at `AI_Skills/skills/src/june-smart-english-general-studynote/`, also follow the actual project's root `AGENTS.md` and `skills/AGENTS.md`, and use its target-specific backup/release tooling. A standalone clone does not require that parent project or a private plugin. Git synchronization, packaging, installation, and GitHub Releases are separate operations. Keep the skill identity and the learning workflow below unchanged unless the user requests a functional change.

## Read these references as needed

- Read `references/workflow.md` before running the full workflow.
- Read `references/article-contract.md` when canonicalising PDF/DOCX/TXT/pasted input.
- Read `references/study-note-contract.md` before filling the study skeleton.
- Read `references/paragraph-notes.md` for intro, paragraph-function, and translation rules.
- Read `references/sentence-analysis.md` for Depth 1-3 sentence selection.
- Read `references/vocabulary-selection.md` while selecting paragraph words and phrases.
- Read `references/vocabulary-enrichment.md` for lexical master, occurrences, database supplement, and IPA.
- Read `references/cefr.md` only when CEFR is enabled or requested.
- Read `references/rendering.md` before rendering HTML/LaTeX/PDF.
- Read `references/pdf-runtime.md` before PDF compilation or template/provider verification.
- Read `references/error-policy.md` when any stage fails.

## Configuration

Load defaults from:

- `config/study.json`: `sentence_analysis_depth` defaults to `1`. Accept explicit per-run override `1`, `2`, or `3` without mutating the config file.
- `config/cefr.json`: controls article-level CEFR plus optional word statistics. By default, word statistics are enabled with adapter `evp_sqlite` and asset `assets/cefr/evp.sqlite`. Keep the adapter/data source replaceable without changing canonical study JSON or renderers.
- `config/pdf.json`: PDF defaults to enabled; provider defaults to `auto`; engine is XeLaTeX.
- `config/output.json`: controls whether canonical article/study JSON files are exposed as deliverables. Still generate and validate them internally in every run; return them only when `expose_structured_json=true`.

Do not add DOCX as an output format.

## Preflight

Run:

```bash
python scripts/preflight.py
```

Preflight must also verify the bundled HTML font assets, the `fontTools` dependency used to create self-contained HTML font subsets, and the configured CEFR word-statistics adapter/data asset. CEFR word-statistics failures are degradable and must disable only the derived word-level chart. Use `--check-network` only when direct HTTP capability is relevant. Do not install packages or modify the user's environment. If a required dependency is missing, report the exact dependency and stop only the affected capability.

Do not assume direct script networking exists in every host. Treat host web search and script HTTP access as separate capabilities.

## Canonicalise the article

Produce `english-core-read-article-note-v1` before any learning analysis.

### DOCX

Run:

```bash
python scripts/article/extract_docx.py input.docx adapter.json
python scripts/article/normalise_article.py adapter.json <sanitized_title>_article.json
python scripts/article/validate_article.py <sanitized_title>_article.json
```

Preserve logical title/subtitle/headings/paragraphs and effective italics only.

### TXT

Run:

```bash
python scripts/article/extract_txt.py input.txt adapter.json
python scripts/article/normalise_article.py adapter.json <sanitized_title>_article.json
python scripts/article/validate_article.py <sanitized_title>_article.json
```

Support UTF-8, UTF-8 BOM, and BOM-marked UTF-16 LE/BE. Do not guess legacy encodings after UTF-8 failure.

### Pasted text

Write an adapter object containing `text`, then normalise and validate as above. Preserve explicit Markdown italics when constructing canonical inline runs if the host/model can do so reliably.

### PDF

Use the host's document/PDF understanding first. Recover title/subtitle, logical heading levels 1-3, paragraph order, page-furniture exclusions, cross-page paragraph continuity, and italics only when reliable. Convert the recovered structure to the canonical article contract and validate it.

If a scanned/complex PDF cannot yield reliable body text and reading order, stop. Do not fabricate missing content and do not make OCR a V1 requirement.

## Build the study skeleton

Determine the effective `sentence_analysis_depth` from an explicit user override or `config/study.json`, then run:

```bash
python scripts/study/build_study_skeleton.py <sanitized_title>_article.json study_skeleton.json --sentence-analysis-depth <1|2|3>
```

Do not alter canonical English body text/order while filling the skeleton.

## Fill semantic learning content

Read the complete article first.

Fill:

- `title_zh` and optional `subtitle_zh`;
- `is_complete_article` and `intro_note` according to completeness;
- heading `translation_zh`;
- paragraph `paragraph_function_zh`;
- sentence-aligned `translation_zh` generated from whole-paragraph context;
- non-null `sentence_note_zh` only for sentences selected by the deterministic Depth rules already represented in the skeleton;
- paragraph `vocabulary` and `phrase_notes` following the established learner profile.

During this draft stage, paragraph vocabulary may temporarily carry `pos`, `labels`, and `definition_en` for enrichment. These helper fields must not remain in final paragraph vocabulary.

Do not manually add sentence analyses outside the deterministic Depth selection.

## Enrich vocabulary

Run the first IPA stage and always request an internal status report:

```bash
python scripts/vocabulary/prepare_vocabularies.py study_draft.json vocab_prepared.json --ipa-status-json ipa_status.json
```

This stage follows the proven `te-weekly-json-study-notes` order exactly for Youdao: bundled OALD9 -> direct Youdao JSON for the exact lemma. If direct Youdao does not resolve the lemma, do **not** enter compound fallback yet. `ipa_status.json` marks that lemma as `host_lookup_required` and preserves whether the direct request failed because of DNS/network/timeout/HTTP/JSON/schema problems or returned a valid response with no British IPA.

For every `host_lookup_required` lemma, use the host's web/search capability to look up the exact lemma on `dict.youdao.com`. Accept only explicit British/UK pronunciation evidence. Save current-run evidence in exactly this shape:

```json
{
  "exact-lemma": {
    "ipa_uk": "/.../",
    "source": "youdao_web"
  }
}
```

If the host lookup was completed but Youdao supplied no usable British IPA for some lemmas, still create an empty or partial runtime JSON; the presence of `--runtime-ipa-json` marks the host-level Youdao stage complete. Then rerun the IPA resolver:

```bash
python scripts/vocabulary/resolve_ipa.py vocab_prepared.json vocab_resolved.json --runtime-ipa-json runtime_ipa.json --ipa-status-json ipa_status_final.json
```

Only after the host-level Youdao stage is complete may the resolver use conservative compound fallback. If entries still remain unresolved and the host can obtain other reliable British-pronunciation evidence, save only those explicit values as objects with `ipa_uk` plus `source: "reliable_web"` and rerun with `--reliable-ipa-json`. Runtime evidence is ephemeral and must never be persisted to OALD9. Never infer IPA from model knowledge. Final unresolved IPA is allowed and remains `null`.

Review every prepared top-level lexical entry. Fill any blank `pos`, `definition_en`, and `meaning_zh` from the actual article context. Keep one contextual learner-dictionary-style English definition and concise Chinese meaning. Preserve database labels and occurrence data.

Then run:

```bash
python scripts/vocabulary/finalize_vocabularies.py vocab_prepared_filled.json <sanitized_title>_study_note.json
```

This generates deterministic `lexical_id` values from `(lemma, POS)`, links paragraph vocabulary to the lexical master, and removes temporary paragraph helper fields.

Never invent British IPA. Unresolved IPA may remain `null`.

## Optional CEFR

If CEFR is disabled, keep `cefr=null`.

If enabled:

1. Read `references/cefr.md`.
2. Make a holistic full-article model judgement for `estimated_reading_level` A1-C2.
3. Store only that article-level judgement in canonical study JSON:

```json
{
  "cefr": {
    "estimated_reading_level": "C1"
  }
}
```

4. Keep the canonical CEFR object limited to the article-level reading judgement; do not store provider-specific CEFR word data, coverage, lookup diagnostics, or statistics in canonical study JSON.
5. Read `config/cefr.json`. If `word_statistics.enabled=true`, use the configured adapter/data asset. The default is `evp_sqlite` with `assets/cefr/evp.sqlite`; do not silently ignore this setting or fall back to a different provider.
6. Prepare adapter candidates from the canonical article:

```bash
python scripts/cefr/build_cefr_statistics.py prepare <sanitized_title>_article.json cefr_candidates.json
```

7. For every candidate item with `status: "decision_required"`, inspect its full paragraph context and supplied candidate rows. Write `cefr_decisions.json` by selecting only a supplied `candidate_id`; use `null` only for a proper name or when none of the supplied senses reliably matches. Never invent a word-level CEFR value.
8. Finalize the source-neutral percentages and render the chart:

```bash
python scripts/cefr/build_cefr_statistics.py finalize cefr_candidates.json cefr_decisions.json cefr_statistics.json
python scripts/cefr/render_cefr_chart.py cefr_statistics.json cefr_statistics.png
```

The core chart displays the supplied A1-C2 percentages as six vertical bars with A1-C2 x-axis labels, a thin green horizontal baseline, and percentage labels above the bars. It has no y-axis, grid, title, legend, or explanatory text, and uses a transparent background. Provider-specific lookup/sense/counting logic stays inside the adapter layer. If the configured word-statistics adapter/data asset is unavailable or fails, keep the article-level CEFR judgement and omit only the word-level statistics/chart.

## Validate final canonical study data

Run:

```bash
python scripts/study/validate_study_note.py <sanitized_title>_study_note.json
```

Repair every fatal validation/invariant error. Never render from invalid canonical data.

Validation must protect source paragraph order/text, sentence reconstruction, inline runs, lexical links, exact sentence-relative occurrences, the article-level CEFR value, and completeness/intro consistency.

## Render HTML

Run:

```bash
python scripts/render/render_html.py <sanitized_title>_study_note.json <sanitized_title>_study_notes.html [--cefr-chart cefr_statistics.png]
```

Keep the established `te-notes-html-pdf` screen presentation: 61% default left column with draggable divider, full Summary hierarchy, English/Chinese block labels, structured right-note sections, study-vocabulary vs database-only highlighting, internal vocabulary navigation, responsive/print behaviour, and the vocabulary appendix. When `--cefr-chart` is supplied, render a separate centered `单词难度统计` section after the article body and before `Vocabularies｜生词表`; HTML print should start that section on a new page and must not force another page break before the vocabulary appendix. Render sentence-aligned Chinese translations as one continuous paragraph. Preserve full-width heading hierarchy 1/2/3 at the original positions. Use the bundled Lora/Noto Serif font assets to build per-document embedded font subsets: Lora Regular/Bold/Italic for English serif content, Noto Serif SC Regular/Bold for Chinese serif content, and Noto Serif Regular for IPA. Keep small UI/sans elements on the existing system sans stack. Keep `definition_en` in canonical JSON but do not display it in learner-facing HTML. Display CEFR as exactly `CEFR level: X`. End the screen HTML with exactly `© JEnglish | AI-generated.`.

## Render LaTeX and PDF

Use the shared template and deterministic helpers described in `references/pdf-runtime.md`. The renderer preserves original punctuation and italics; each selected sentence gets one continuous outer underline, including spaces and punctuation. TeX environments scope English/Chinese punctuation rules, so no per-article model rewriting is needed.

Generate LaTeX:

```bash
python scripts/render/render_latex.py <sanitized_title>_study_note.json <sanitized_title>_study_notes.tex [--cefr-chart cefr_statistics.png]
```

Do not render `definition_en` in the learner-facing PDF; retain it only in canonical JSON/downstream data. Display CEFR as exactly `CEFR level: X`. When `--cefr-chart` is supplied, force a page break after the body, render centered `单词难度统计` plus the chart, then continue directly into `Vocabularies｜生词表` with no second forced page break. Keep the General article fonts unchanged. Match the established `te-notes-html-pdf` PDF presentation for Summary spacing, TE-style bullet note panels with IPA/POS/labels, vocabulary/phrase separation, sentence-analysis box border/padding, study-vocabulary vs database-only highlighting, sentence-analysis red underlining, and the JUNE watermark. In every `paracol` paragraph card, explicitly initialise both left and right column text colour with `\columncolor{black}` so a breakable note box cannot make continued text white after a page break. The watermark must use 218pt, opacity 0.16, gray 0.58, 60-degree rotation, Multiply blending, and an independent font that prefers Arimo, then Noto Sans, then the current General sans family.

For a new/unverified environment/provider, generate and compile the smoke test first:

```bash
python3 scripts/render/pdf_smoke_test.py document.tex [--cefr-chart cefr_statistics.pdf]
```

Keep the existing article-font policy: Libertinus via `libertinus-otf`, `FandolSong-Regular.otf`, and `FandolHei-Regular.otf`. Do not change the article fonts. The watermark font may prefer Arimo or Noto Sans when available, but must fall back to the current General sans family so those fonts are never required for successful compilation. Do not require bundled font files.

Compile according to `config/pdf.json`:

```bash
python3 scripts/render/compile_pdf.py <sanitized_title>_study_notes.tex <sanitized_title>_study_notes.pdf --provider <auto|local|texlive_net> [--asset cefr_statistics.png] [--diagnostic-log]
```

`auto` tries local XeLaTeX first, then TeXLive.net for provider/environment failures. Do not switch providers to hide a LaTeX source/template bug.

Graphics are collected automatically. Prefer a vector chart from current-run CEFR statistics for LaTeX; PNG remains supported. Remote graphics need `pypdf` (plus `matplotlib` for PNG/JPEG); report missing dependencies without installing them. Logs/attempt metadata stay internal. Use `--diagnostic-log` to verify a provider/template, then inspect warnings and pages.

If both providers are unavailable for environmental/network reasons, create a self-contained fallback:

```bash
python scripts/render/package_latex_project.py <sanitized_title>_study_notes.tex <sanitized_title>_latex_project.zip --asset-dir <output-dir>
```

Return HTML + `.tex` + the LaTeX project ZIP. The ZIP must contain `document.tex` and every referenced local asset such as a generated CEFR chart.

## Filename contract

Use the exact sanitisation algorithm in `scripts/utils/filename.py`, inherited from `te-weekly-json-study-notes`. Do not lowercase, transliterate, truncate, or invent a different sanitiser.

Normal outputs:

```text
<sanitized_title>_study_notes.html
<sanitized_title>_study_notes.pdf
```

PDF-provider fallback:

```text
<sanitized_title>_study_notes.html
<sanitized_title>_study_notes.tex
<sanitized_title>_latex_project.zip
```

When `expose_structured_json=true`, additionally return:

```text
<sanitized_title>_article.json
<sanitized_title>_study_note.json
```

## Final checks

Before returning results:

- require canonical article and final study-note validation success;
- ensure visible English text is unchanged;
- ensure headings retain levels 1-3 in both renderers;
- ensure HTML paragraph cards use the established 61% default draggable screen split and PDF paragraph cards remain 58/42;
- ensure the HTML footer is exactly `© JEnglish | AI-generated.`;
- ensure PDF Summary spacing, right-note bullets/details/separator, sentence-analysis boxes, study/database vocabulary highlighting, explicit black `paracol` column colour, and JUNE watermark match the approved TE presentation rules in `references/rendering.md`;
- ensure CEFR level sits at the bottom of the title area when enabled and the learner-facing label is exactly `CEFR level: X`;
- when word-level CEFR statistics were produced for the run, ensure HTML renders a centered `单词难度统计` section between the article body and `Vocabularies｜生词表`; ensure PDF forces a page break after the body, renders the same centered title plus chart, and then continues directly into the vocabulary appendix without another forced page break;
- ensure every paragraph vocabulary link resolves through `lexical_id` and every occurrence offset is exact;
- ensure no renderer/debug/audit fields leaked into final canonical JSON;
- ensure public output hides structured JSON when configured;
- ensure PDF font smoke test passes for the actual provider before treating that provider as verified;
- ensure the LaTeX fallback ZIP recompiles independently when PDF providers are unavailable.
