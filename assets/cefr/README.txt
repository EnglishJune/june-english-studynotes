CEFR data assets

The bundled `evp.sqlite` is the current default word-level CEFR data asset. It is selected by `config/cefr.json` through the `evp_sqlite` adapter.

Provider-specific lookup, sense disambiguation, eligibility, and counting rules belong to `scripts/cefr/adapters/evp_sqlite.py`. They must not leak into canonical study-note JSON or the HTML/PDF renderers. The source-neutral orchestration script `scripts/cefr/build_cefr_statistics.py` produces temporary candidate/decision artifacts and the minimal `cefr_statistics.json` A1-C2 percentage contract documented in `references/cefr.md`.

The adapter and data asset remain replaceable. To use another CEFR source in the future, add a compatible adapter, select it in `config/cefr.json`, and keep the canonical study-note schema and renderer contract unchanged.
