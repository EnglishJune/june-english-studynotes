# Error and degradation policy

`scripts/render/compile_pdf.py` classifies the first fatal PDF diagnostic and saves complete logs; routine package messages do not establish environment failure. Read `pdf-runtime.md` for the shared template, automatic graphics encoding, and diagnostics.

## Fatal data errors
Stop after attempted repair when input cannot be reliably read, PDF reading order/body cannot be recovered, canonical article validation fails, study structure loses/changes source text, sentence reconstruction fails, lexical links/occurrence offsets are inconsistent, or final schema/semantic validation fails.

## Degradable enrichment failures
IPA unresolved -> `uk_phonetic:null`. Word-level CEFR data source/adapter unavailable or fails -> preserve the canonical model `estimated_reading_level` and omit only the derived word-level CEFR statistics/chart. Never replace unavailable source data with model-guessed word levels.

## Isolated rendering failures
HTML renderer bugs are rendering failures but do not invalidate already validated canonical data. PDF environment/provider failures do not invalidate JSON/HTML. In PDF provider failure, return HTML + `.tex` + a self-contained LaTeX project ZIP. A LaTeX source/template bug is not a provider failure: do not silently switch providers to hide it.

## Network
Do not assume every host permits outbound HTTP. Preflight network-dependent capabilities. ChatGPT/container hosts may block direct script networking; API/self-hosted deployments should explicitly allow required domains (`texlive.net`, `dict.youdao.com`) according to the host's network policy. Host web-search fallback is separate from script HTTP access.
