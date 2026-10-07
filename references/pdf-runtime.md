# PDF runtime and template

The renderer and fallback project use the same preamble at `assets/templates/study_notes_preamble.tex`. Generated TeX embeds it and does not need the skill directory when compiled.

## Source text and highlighting

- Keep canonical JSON unchanged. Project `inline_runs` into original italics for titles, subtitles, headings, and body text in both HTML and PDF.
- English fields use the local `StudyEnglish` environment. It disables automatic TeX punctuation mapping and gives U+2018/U+2019/U+201C/U+201D the Latin character class. Assignments restore on leaving it; Chinese fields retain xeCJK punctuation behaviour.
- U+2019 in `Indonesia’s` is a right single quotation mark used as an apostrophe. It differs from right double U+201D, ASCII U+0027/U+0022, and fullwidth U+FF07/U+FF02. Preserve characters; do not globally normalise quotes.
- In mixed Chinese notes, `esc_mixed` treats U+2019 between ASCII Latin letters as an English apostrophe. Other Chinese quotation marks keep xeCJK's punctuation rules; no model repair is needed.
- Fullwidth U+FF07/U+FF02 retain their characters and Fandol glyphs via `StudyFWQuote`; surrounding English spaces remain ordinary word spaces.
- Each selected sentence has one outer `StudySentenceUL` using `CJKunderline*`. The continuous red line includes words, spaces, and punctuation and continues after line breaks. Interior colours, links, and italics do not create more underlines.
- Keep word separators outside inline colour/link/italic groups and inside the sentence underline. Do not box entire sentences or multiword phrases.
- Study vocabulary/phrases stay red. Database-only vocabulary keeps grey dotted underlining unless a sentence/phrase highlight overrides it. Vector dots keep decorative periods out of source text extraction.
- Preserve Libertinus/Fandol families and all approved page/type/column/box/watermark settings. Real Fandol bold faces are explicit; English paragraphs use ragged-right line breaking.

## Graphics and transport

HTML still uses PNG. Prefer a vector PDF for LaTeX from the same validated current-run statistics:

~~~bash
python3 scripts/cefr/render_cefr_chart.py cefr_statistics.json cefr_statistics.pdf
python3 scripts/render/render_latex.py article_study_note.json article_study_notes.tex --cefr-chart cefr_statistics.pdf
~~~

The renderer copies the chart beside output TeX with a stable ASCII name. Compilation/ZIP packaging discover graphics automatically; `--asset` supports explicitly supplied graphics outside that directory.

TeXLive.net's `filecontents[]` fields normalise line endings. `latex_assets.py` encodes PDF streams with ASCIIHex and uses portable graphic aliases. PNG/JPEG becomes a PDF image with alpha preserved, then uses the same encoding. No per-article model conversion is needed.

- Remote PDF graphics need `pypdf`; PNG/JPEG also needs `matplotlib`, already used by CEFR rendering.
- Local XeLaTeX and fallback ZIP use original graphics without remote encoding.
- Report missing dependencies; do not install automatically. When providers are unavailable for environment/network reasons, retain the standalone TeX/ZIP fallback and chart.

## Compilation and diagnostics

`auto` tries local XeLaTeX, then TeXLive.net only for provider/environment failure. Source/template errors stop the attempt.

Local compilation uses a temporary build directory and atomically writes the PDF, including when TeX and PDF share a directory. Require a PDF signature; HTTP MIME alone is insufficient.

Complete failure logs go to `<output-stem>.compile.log`, attempts to `<output-stem>.compile.json`. Retries append labelled logs. Classify the first fatal diagnostic, not routine package/font messages or a truncated tail.

For an unverified provider, compile the actual generated study-note document with the production template and inspect the resulting pages and diagnostics:

~~~bash
python3 scripts/render/compile_pdf.py article_study_notes.tex article_study_notes.pdf --provider <auto|local|texlive_net> --diagnostic-log
~~~

`--diagnostic-log` requests the TeXLive.net log in a second compilation because the service returns either PDF or log. Routine successful remote output avoids this second request. Keep logs/metadata internal.

Inspect pages and logs: exact punctuation/spaces, continuous underlines across lines, overlapping colour/link/italic styles, Chinese bold, IPA, cross-page boxes, black continued column text, chart, and appendix. Require no fatal errors, missing glyphs, undefined font shapes, or material line overflow before treating the provider/template as verified.

Fallback ZIP contains `document.tex` and all graphics with matching aliases. Extract into a fresh directory and compile there to verify independence.
