# Canonical article contract

Schema version: `english-core-read-article-note-v1`. Validate with the bundled JSON Schema and semantic validator.

## Inputs
V1 supports text-layer PDF, DOCX, TXT, and pasted/direct text. Scanned or structurally ambiguous PDFs are not guaranteed; if reliable reading order/body structure cannot be recovered, stop rather than fabricate.

## Structure
Top-level title is required. Preserve source title when present (`title_origin=source`); otherwise generate one short neutral English title (`title_origin=generated`) and keep `title_inline_runs=[]`. Never generate a subtitle that is absent from the source. Unknown source metadata is `null`, not invented.

Body is one ordered array containing only headings and paragraphs. Heading levels are logical 1-3. Paragraph numbering starts at 1 and is continuous; headings have no paragraph number. Title/subtitle are not duplicated in body.

## Inline formatting
V1 preserves italics only. Plain `text` never contains Markdown/HTML. `inline_runs` concatenate exactly to `text`; only `marks:["italic"]` is allowed. Do not infer italics semantically.

## Cleaning principle
Preserve source order and body completeness. Remove only clearly non-body furniture/promotional/correction material when the evidence is strong. The old Economist-specific `sign up + newsletter`/correction rules are examples of conservative filtering, not universal phrases to delete in arbitrary publications.
