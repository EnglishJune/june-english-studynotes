# Optional CEFR module

Controlled by `config/cefr.json`.

## Overall reading level

When CEFR is enabled, set `cefr.estimated_reading_level` to A1-C2 by holistic model judgement from the complete article. This is canonical study-note data.

The canonical CEFR object contains only the article-level judgement:

```json
{
  "estimated_reading_level": "C1"
}
```

Do not store word-level CEFR statistics, provider names, provider metadata, lookup diagnostics, coverage, or source-specific fields in canonical study JSON.

## Word-level CEFR statistics

Treat word-level CEFR statistics as a separate derived rendering artifact. `config/cefr.json` selects whether word statistics are enabled and which source-specific adapter/data asset is active. The current default is the bundled `evp_sqlite` adapter using `assets/cefr/evp.sqlite`.

Keep provider-specific lookup, sense selection, counting rules, and diagnostics inside the adapter layer. Do not hard-code EVP schema details into the canonical study-note contract or HTML/PDF renderers. A future adapter may replace EVP without changing canonical study JSON or the chart/rendering contract.

### Current default adapter workflow

Prepare candidate EVP matches from the canonical article:

```bash
python scripts/cefr/build_cefr_statistics.py prepare <sanitized_title>_article.json cefr_candidates.json
```

The adapter counts body-paragraph lexical word occurrences only and currently includes EVP noun, verb, adjective, and adverb entries. A conservative closed class of function-like/grammatical words is excluded so the chart reflects lexical difficulty rather than grammar-word frequency. Title/subtitle/headings are excluded. Proper names are not counted.

For every item with `status: "decision_required"`, inspect the full paragraph context and the supplied EVP candidates (`candidate_id`, `base_word`, `guideword`, `level`, `part_of_speech`, and `topics`). Write `cefr_decisions.json` in this shape:

```json
{
  "decisions": {
    "p1:12-16": 1234,
    "p2:8-11": null
  }
}
```

Choose only a supplied `candidate_id` that matches the contextual sense. Use `null` when the occurrence is a proper name or no supplied EVP sense reliably matches. Never invent a level or candidate. A missing required decision is an error.

Finalize the source-neutral statistics:

```bash
python scripts/cefr/build_cefr_statistics.py finalize cefr_candidates.json cefr_decisions.json cefr_statistics.json
```

The denominator is classified lexical word occurrences only. The final renderer input contains only A1-C2 percentages:

```json
{
  "levels": {
    "A1": {"percentage": 8.0},
    "A2": {"percentage": 15.0},
    "B1": {"percentage": 26.0},
    "B2": {"percentage": 30.0},
    "C1": {"percentage": 17.0},
    "C2": {"percentage": 4.0}
  }
}
```

Generate the chart with:

```bash
python scripts/cefr/render_cefr_chart.py cefr_statistics.json cefr_statistics.png
```

## Chart contract

The chart is intentionally minimal and presentation-neutral:

- vertical bars ordered A1, A2, B1, B2, C1, C2;
- use the established pale-to-deep green palette aligned with the HTML theme;
- keep only the A1-C2 x-axis labels, a thin `#83A78D` horizontal baseline, and the percentage above each bar;
- omit the y-axis, y-axis labels, grid, chart title, legend, and explanatory text;
- export with a transparent background so the same PNG works naturally in HTML and PDF;
- small output-size adjustments are allowed as long as this overall visual contract is preserved.

If the configured word-statistics adapter/data asset is unavailable or fails, preserve the article-level `estimated_reading_level` and omit only the word-level statistics/chart. Do not replace unavailable source data with model-guessed word levels.
