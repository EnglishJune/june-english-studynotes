#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,html,io,json,mimetypes,re
from pathlib import Path
from urllib.parse import urlparse
from build_presentation import build
from latex_text import italic_ranges

SKILL_ROOT=Path(__file__).resolve().parents[2]
FONT_ROOT=SKILL_ROOT/"assets"/"fonts"
FONT_FILES={
    "lora_regular":"Lora-Regular.ttf",
    "lora_bold":"Lora-Bold.ttf",
    "lora_italic":"Lora-Italic.ttf",
    "noto_serif_sc_regular":"NotoSerifSC-Regular.ttf",
    "noto_serif_sc_bold":"NotoSerifSC-Bold.ttf",
    "noto_serif_regular":"NotoSerif-Regular.ttf",
}


def _subset_font_data_uri(path,text):
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError("fontTools is required to build self-contained HTML font subsets") from exc
    if not path.exists():
        raise FileNotFoundError(f"bundled HTML font missing: {path}")
    options=subset.Options()
    subsetter=subset.Subsetter(options=options)
    subsetter.populate(text=text)
    font=TTFont(str(path))
    subsetter.subset(font)
    buf=io.BytesIO();font.save(buf);font.close()
    return "data:font/ttf;base64,"+base64.b64encode(buf.getvalue()).decode("ascii")


def _font_face_css(data):
    # Use all study text as the glyph seed. Unsupported characters are ignored by each font.
    seed=json.dumps(data,ensure_ascii=False)+" 全文导读结构主线写作特色重点句解析生词表中文直译 English original CEFR level JEnglish AI-generated ©｜·→"
    uris={key:_subset_font_data_uri(FONT_ROOT/name,seed) for key,name in FONT_FILES.items()}
    return f'''
@font-face {{font-family:"JEnglish Lora";src:url("{uris["lora_regular"]}") format("truetype");font-weight:400;font-style:normal;font-display:block;}}
@font-face {{font-family:"JEnglish Lora";src:url("{uris["lora_bold"]}") format("truetype");font-weight:700;font-style:normal;font-display:block;}}
@font-face {{font-family:"JEnglish Lora";src:url("{uris["lora_italic"]}") format("truetype");font-weight:400;font-style:italic;font-display:block;}}
@font-face {{font-family:"JEnglish Noto Serif SC";src:url("{uris["noto_serif_sc_regular"]}") format("truetype");font-weight:400;font-style:normal;font-display:block;}}
@font-face {{font-family:"JEnglish Noto Serif SC";src:url("{uris["noto_serif_sc_bold"]}") format("truetype");font-weight:700;font-style:normal;font-display:block;}}
@font-face {{font-family:"JEnglish IPA";src:url("{uris["noto_serif_regular"]}") format("truetype");font-weight:400;font-style:normal;font-display:block;}}
'''

CSS='\n:root {\n  --bg: #EFEFEF;\n  --paper: #fffdf8;\n  --note-bg: #e2e7bf;\n  --ink: #1f2933;\n  --muted: #5f6f86;\n  --line: #83a78d;\n  --soft-line: #83a78d;\n  --accent: #8a5a2b;\n  --accent-dark: #5d3a1a;\n  --red: #b0122c;\n  --left-width: 61%;\n}\n* { box-sizing: border-box; }\nbody {\n  margin: 0;\n  background: var(--bg);\n  color: var(--ink);\n  font-family: "JEnglish Lora", "JEnglish Noto Serif SC", serif;\n  font-size: 16px;\n  line-height: 1.72;\n  text-rendering: optimizeLegibility;\n}\n.page {\n  max-width: 1220px;\n  margin: 0 auto;\n  padding: 34px 20px 62px;\n}\n.header {\n  background: transparent;\n  border: 0;\n  border-radius: 0;\n  padding: 20px 24px 26px;\n  text-align: center;\n}\nh1 {\n  margin: 0 auto 10px;\n  max-width: 980px;\n  font-size: clamp(1.55rem, 3.1vw, 2.45rem);\n  line-height: 1.12;\n  letter-spacing: -0.025em;\n  font-weight: 800;\n}\n.title-zh {\n  margin: 0 auto 18px;\n  max-width: 900px;\n  font-size: 1.12rem;\n  line-height: 1.45;\n  font-weight: 700;\n  color: #374151;\n}\n.subtitle {\n  margin: 0 auto 6px;\n  max-width: 900px;\n  color: #374151;\n  font-size: 1.14rem;\n  font-weight: 600;\n}\n.subtitle-zh {\n  margin: 0 auto 14px;\n  max-width: 900px;\n  color: #475569;\n  font-size: 1rem;\n}\n.meta {\n  color: var(--muted);\n  font-size: 0.9rem;\n}\na { color: var(--accent-dark); }\n.audio-link,\n.audio-play-button {\n  display: inline-flex;\n  align-items: center;\n  justify-content: center;\n  width: 1.05em;\n  height: 1.05em;\n  margin-left: 0.35em;\n  color: var(--red);\n  vertical-align: -0.16em;\n}\n.audio-link svg,\n.audio-play-button svg {\n  display: block;\n  width: 1.05em;\n  height: 1.05em;\n  fill: currentColor;\n}\n.audio-play-button {\n  appearance: none;\n  border: 0;\n  padding: 0;\n  background: transparent;\n  cursor: pointer;\n  font: inherit;\n}\n.audio-player-wrap {\n  margin: 10px auto 0;\n  max-width: 520px;\n}\n.audio-player-wrap[hidden] { display: none; }\n.audio-player-wrap audio {\n  width: 100%;\n  height: 32px;\n}\n.intro-note {\n  margin: 22px 0 30px;\n  background: #DCDDDF;\n  border: 0;\n  border-left: 9px solid #4f5d52;\n  border-radius: 0;\n  padding: 14px 20px;\n  font-size: 0.875rem;\n  line-height: 1.65;\n}\n.intro-note h2 {\n  margin: 0 0 9px;\n  font-size: 1.02rem;\n}\n.intro-item {\n  display: flex;\n  align-items: flex-start;\n  gap: 0.42rem;\n  margin: 7px 0;\n}\n.intro-icon {\n  display: block;\n  width: 1rem;\n  height: 1rem;\n  flex: 0 0 1rem;\n  margin-top: 0.28em;\n  color: #53645a;\n}\n.intro-item-content { min-width: 0; }\n.paragraph-card {\n  display: grid;\n  grid-template-columns: minmax(0, var(--left-width)) 14px minmax(0, 1fr);\n  gap: 0;\n  align-items: stretch;\n  margin: 0;\n  padding: 22px 0;\n  border-top: 1px solid var(--soft-line);\n}\n.paragraph-card:first-of-type { border-top: 0; }\n.paragraph-function {\n  grid-column: 1 / -1;\n  display: flex;\n  align-items: baseline;\n  gap: 0.42rem;\n  margin: 0 0 10px;\n  color: #526b76;\n  font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;\n  font-size: 0.79rem;\n  font-weight: 600;\n  line-height: 1.45;\n}\n.paragraph-function-icon {\n  flex: 0 0 auto;\n  position: relative;\n  top: 0.03em;\n  font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif;\n  font-size: 0.95rem;\n  line-height: 1;\n}\n.paragraph-function-text { min-width: 0; color: var(--red); }\n.left-panel,\n.right-panel {\n  border: 0;\n  border-radius: 0;\n  box-shadow: none;\n}\n.left-panel {\n  background: transparent;\n  padding: 0 24px 0 0;\n}\n.right-panel {\n  background: var(--note-bg);\n  padding: 14px 18px;\n  font-size: 0.76rem;\n  line-height: 1.54;\n}\n.splitter {\n  position: relative;\n  cursor: col-resize;\n  min-height: 100%;\n  touch-action: none;\n}\n.splitter::before {\n  content: "";\n  position: absolute;\n  top: 0;\n  bottom: 0;\n  left: 50%;\n  width: 2px;\n  transform: translateX(-50%);\n  background: var(--line);\n}\n.splitter::after {\n  content: "";\n  position: absolute;\n  top: 50%;\n  left: 50%;\n  width: 10px;\n  height: 42px;\n  transform: translate(-50%, -50%);\n  border-radius: 999px;\n  background: #ffffffcc;\n  border: 1px solid var(--line);\n}\nbody.resizing { cursor: col-resize; user-select: none; }\n.block-label {\n  margin: 0 0 6px;\n  color: var(--muted);\n  font-size: 0.74rem;\n  text-transform: uppercase;\n  letter-spacing: .09em;\n  font-weight: 700;\n  font-family: "Noto Sans", "Noto Sans SC", "PingFang SC", Arial, sans-serif;\n}\n.block-label.translation-label { margin-top: 15px; }\n.original {\n  font-size: 1.02rem;\n  color: #172033;\n}\n.translation {\n  color: #243247;\n  border-top: 1px dashed var(--soft-line);\n  margin-top: 13px;\n  padding-top: 10px;\n}\n.sentence-note {\n  margin-top: 13px;\n  border-left: 4px solid #8a5a2b;\n  background: #f8efe4;\n  padding: 10px 12px;\n  font-size: 0.92rem;\n}\n.right-panel h3 {\n  margin: 0 0 10px;\n  color: var(--accent-dark);\n  font-size: 0.95rem;\n  font-weight: 800;\n}\n.note-section {\n  border-top: 1px solid var(--soft-line);\n  padding-top: 10px;\n  margin-top: 10px;\n}\n.note-section:first-of-type {\n  border-top: 0;\n  padding-top: 0;\n  margin-top: 0;\n}\n.note-section h4 {\n  margin: 0 0 6px;\n  font-size: 0.86rem;\n  color: #25401a;\n  font-weight: 800;\n}\nul { margin: 7px 0 0 1.05rem; padding: 0; }\nli { margin: 7px 0; }\n.note-term {\n  font-weight: 800;\n  color: #9f1239;\n}\n.ipa {\n  color: #475569;\n  font-family: "JEnglish IPA", "JEnglish Lora", serif;\n  font-size: 0.92em;\n  margin-left: 4px;\n}\n.pos {\n  display: inline-block;\n  font-size: 0.68rem;\n  line-height: 1.35;\n  padding: 1px 5px;\n  border-radius: 999px;\n  background: #f4ecd6;\n  color: #5d3a1a;\n  margin: 0 4px;\n  vertical-align: middle;\n  font-family: "Noto Sans", "Noto Sans SC", Arial, sans-serif;\n}\n.note-label {\n  display: inline-block;\n  font-size: 0.58rem;\n  line-height: 1.35;\n  padding: 1px 6px;\n  border-radius: 999px;\n  background: rgba(255,255,255,0.66);\n  color: #38451f;\n  border: 1px solid rgba(93, 58, 26, 0.18);\n  margin-left: 4px;\n  vertical-align: middle;\n  font-family: "Noto Sans", "Noto Sans SC", Arial, sans-serif;\n}\n.vocab-meaning { font-weight: 650; }\n.note-extra { color: #334155; margin-top: 2px; }\n.muted { color: var(--muted); }\n.hl-word,\n.hl-phrase,\n.hl-gre,\n.hl-ielts {\n  color: var(--red);\n  font-weight: 780;\n}\n.hl-syntax {\n  text-decoration: underline;\n  text-decoration-color: #b0122c;\n  text-decoration-thickness: 2px;\n  text-underline-offset: 4px;\n}\n.hl-translation {\n  color: var(--red);\n  border-bottom: 2px wavy #dc2626;\n  padding: 0 1px;\n}\n.vocab-link {\n  color: inherit;\n  text-decoration: none;\n}\n.exam-vocab-link {\n  color: inherit;\n  text-decoration: none;\n  border-bottom: 1px dotted currentColor;\n  padding-bottom: 0.04em;\n}\n.vocab-link:focus-visible,\n.exam-vocab-link:focus-visible {\n  outline: 2px solid var(--accent);\n  outline-offset: 2px;\n}\n.article-vocabulary {\n  margin-top: 34px;\n  padding-top: 24px;\n  border-top: 1px solid var(--line);\n  scroll-margin-top: 18px;\n}\n.article-vocabulary h2 {\n  margin: 0 0 16px;\n  color: #000;\n  font-size: 1.24rem;\n  line-height: 1.3;\n  text-align: center;\n}\n.vocabularies-grid {\n  display: grid;\n  grid-template-columns: repeat(2, minmax(0, 1fr));\n  gap: 0 26px;\n}\n.vocabulary-entry {\n  padding: 10px 0 11px;\n  border-top: 0;\n  break-inside: avoid;\n  page-break-inside: avoid;\n  scroll-margin-top: 20px;\n}\n.vocabulary-entry:target {\n  background: rgba(226, 231, 191, 0.72);\n  box-shadow: 0 0 0 5px rgba(226, 231, 191, 0.72);\n}\n.vocabulary-head {\n  display: flex;\n  align-items: baseline;\n  flex-wrap: wrap;\n  gap: 4px;\n  min-width: 0;\n}\n.vocabulary-return-link {\n  display: inline-flex;\n  align-items: center;\n  justify-content: center;\n  flex: 0 0 auto;\n  width: 13px;\n  height: 13px;\n  color: #64748b;\n  line-height: 1;\n  text-decoration: none;\n}\n.vocabulary-return-link:hover,\n.vocabulary-return-link:focus-visible {\n  color: #000;\n}\n.vocabulary-return-link:focus-visible {\n  outline: 2px solid var(--accent);\n  outline-offset: 2px;\n}\n.vocabulary-return-link svg {\n  width: 13px;\n  height: 13px;\n  fill: none;\n  stroke: currentColor;\n  stroke-linecap: round;\n  stroke-linejoin: round;\n  stroke-width: 1.8;\n}\n.vocabulary-word {\n  color: #9f1239;\n  font-size: 1rem;\n  font-weight: 800;\n  overflow-wrap: anywhere;\n}\n.vocabulary-details {\n  margin-top: 2px;\n  color: #334155;\n  font-size: 0.86rem;\n  line-height: 1.5;\n}\n.vocabulary-details .ipa { margin-left: 0; }\n.vocabulary-empty { color: var(--muted); }\n.footer {\n  color: var(--muted);\n  text-align: center;\n  font-size: 0.82rem;\n  margin-top: 28px;\n}\n@media (max-width: 840px) {\n  .page { padding: 20px 12px 40px; }\n  .header { padding: 22px; }\n  .paragraph-card { grid-template-columns: 1fr; gap: 14px; }\n  .left-panel { padding-right: 0; }\n  .splitter { display: none; }\n  .vocabularies-grid { grid-template-columns: 1fr; }\n}\n@media print {\n  :root { --left-width: 62%; }\n  body { background: white; font-size: 11pt; }\n  .page { max-width: none; padding: 0; }\n  .header, .intro-note { border-radius: 0; }\n  .paragraph-card { break-inside: avoid; page-break-inside: avoid; padding: 14pt 0; }\n  .paragraph-function {\n    color: #3f4f56;\n    break-after: avoid;\n    page-break-after: avoid;\n  }\n  .splitter { cursor: default; }\n  .splitter::after { display: none; }\n  .right-panel { background: #e2e7bf !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }\n  .cefr-statistics {\n    break-before: page;\n    page-break-before: always;\n    margin-top: 0;\n    padding-top: 0;\n    border-top: 0;\n  }\n  .cefr-statistics h2,\n  .cefr-chart-wrap { break-after: avoid; page-break-after: avoid; }\n  .article-vocabulary {\n    break-before: page;\n    page-break-before: always;\n    margin-top: 0;\n    padding-top: 0;\n    border-top: 0;\n  }\n  .article-vocabulary.after-cefr {\n    break-before: auto;\n    page-break-before: auto;\n  }\n  .article-vocabulary h2 { break-after: avoid; page-break-after: avoid; }\n  .vocabularies-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 18pt; }\n  .vocabulary-entry { break-inside: avoid; page-break-inside: avoid; }\n  .vocabulary-entry:target { background: transparent; box-shadow: none; }\n}\n\n.cefr-level {\n  margin: 10px 0 0;\n  color: var(--muted);\n  font-size: 0.9rem;\n}\n.doc-heading {\n  border-top: 1px solid var(--line);\n  padding-top: 14px;\n  margin: 24px 0 8px;\n}\n.doc-heading h2,\n.doc-heading h3,\n.doc-heading h4 { margin: 0; color: #172033; }\n.doc-heading.level-1 h2 { font-size: 1.35rem; line-height: 1.3; }\n.doc-heading.level-2 h3 { font-size: 1.15rem; line-height: 1.35; }\n.doc-heading.level-3 h4 { font-size: 1rem; line-height: 1.4; }\n.heading-zh { color: #58606a; margin-top: 3px; }\n.cefr-statistics {\n  margin-top: 34px;\n  padding-top: 24px;\n  border-top: 1px solid var(--line);\n  text-align: center;\n}\n.cefr-statistics h2 {\n  margin: 0 0 10px;\n  color: #000;\n  font-size: 1.24rem;\n  line-height: 1.3;\n}\n.cefr-chart-wrap { margin: 0 auto 18px; text-align: center; }\n.cefr-chart { display: inline-block; max-width: min(760px, 92%); height: auto; }\n.article-vocabulary.after-cefr {\n  margin-top: 16px;\n  padding-top: 0;\n  border-top: 0;\n}\n@media print {\n  .cefr-statistics { margin-top: 0; padding-top: 0; border-top: 0; }\n  .article-vocabulary.after-cefr { margin-top: 0; padding-top: 0; border-top: 0; }\n}\n'
JS="\n<script>\n(function () {\n  const root = document.documentElement;\n  let active = false;\n  let activeCard = null;\n\n  function setWidthFromEvent(event) {\n    if (!active || !activeCard) return;\n    const rect = activeCard.getBoundingClientRect();\n    const x = event.clientX - rect.left;\n    let pct = (x / rect.width) * 100;\n    pct = Math.max(42, Math.min(72, pct));\n    root.style.setProperty('--left-width', pct.toFixed(2) + '%');\n  }\n\n  document.querySelectorAll('.splitter').forEach(function (splitter) {\n    splitter.addEventListener('pointerdown', function (event) {\n      active = true;\n      activeCard = splitter.closest('.paragraph-card');\n      document.body.classList.add('resizing');\n      splitter.setPointerCapture(event.pointerId);\n      setWidthFromEvent(event);\n    });\n  });\n\n  window.addEventListener('pointermove', setWidthFromEvent);\n  window.addEventListener('pointerup', function () {\n    active = false;\n    activeCard = null;\n    document.body.classList.remove('resizing');\n  });\n  document.querySelectorAll('[data-audio-toggle]').forEach(function (button) {\n    button.addEventListener('click', function () {\n      const playerWrap = document.querySelector(button.getAttribute('data-audio-toggle'));\n      if (!playerWrap) return;\n      const audio = playerWrap.querySelector('audio');\n      const wasHidden = playerWrap.hasAttribute('hidden');\n      playerWrap.toggleAttribute('hidden', !wasHidden);\n      if (audio && wasHidden) {\n        const playPromise = audio.play();\n        if (playPromise && typeof playPromise.catch === 'function') {\n          playPromise.catch(function () { /* browser may require a second click */ });\n        }\n      }\n    });\n  });\n})();\n</script>\n"


def esc(value):
    return html.escape(str(value or ""), quote=True)


def normalize_label(label):
    text=str(label).strip()
    return "IELTS" if text.lower()=="ielts academic" else text


def render_labels(labels):
    return " ".join(f'<span class="note-label">{esc(normalize_label(x))}</span>' for x in (labels or []) if str(x).strip())


def is_direct_audio_url(url):
    if not url: return False
    return urlparse(url).path.lower().endswith((".mp3",".m4a",".aac",".wav",".ogg",".opus",".flac"))


def headphone_svg():
    return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 3a7 7 0 0 0-7 7v2a3 3 0 0 0-2 2.83V18a3 3 0 0 0 3 3h1a1 1 0 0 0 1-1v-7a1 1 0 0 0-1-1H7v-2a5 5 0 0 1 10 0v2h-.05a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1H18a3 3 0 0 0 3-3v-3.17A3 3 0 0 0 19 12v-2a7 7 0 0 0-7-7Z"/></svg>'


def intro_summary_svg():
    return '<svg class="intro-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" aria-hidden="true" focusable="false"><path fill="currentColor" d="m512 863.36 384-54.848v-638.72L525.568 222.72a96 96 0 0 1-27.136 0L128 169.792v638.72zM137.024 106.432l370.432 52.928a32 32 0 0 0 9.088 0l370.432-52.928A64 64 0 0 1 960 169.792v638.72a64 64 0 0 1-54.976 63.36l-388.48 55.488a32 32 0 0 1-9.088 0l-388.48-55.488A64 64 0 0 1 64 808.512v-638.72a64 64 0 0 1 73.024-63.36"/><path fill="currentColor" d="M480 192h64v704h-64z"/></svg>'


def intro_structure_svg():
    return '<svg class="intro-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" fill="none" aria-hidden="true" focusable="false"><rect x="376" y="48" width="272" height="176" rx="24" stroke="currentColor" stroke-width="48"/><path d="M512 224V760M160 496H864M160 496V760M864 496V760" stroke="currentColor" stroke-width="48" stroke-linecap="round" stroke-linejoin="round"/><rect x="32" y="760" width="272" height="176" rx="24" stroke="currentColor" stroke-width="48"/><rect x="376" y="760" width="272" height="176" rx="24" stroke="currentColor" stroke-width="48"/><rect x="720" y="760" width="272" height="176" rx="24" stroke="currentColor" stroke-width="48"/></svg>'


def intro_writing_svg():
    return '<svg class="intro-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" aria-hidden="true" focusable="false"><path fill="currentColor" d="m512 747.84 228.16 119.936a6.4 6.4 0 0 0 9.28-6.72l-43.52-254.08 184.512-179.904a6.4 6.4 0 0 0-3.52-10.88l-255.104-37.12L517.76 147.904a6.4 6.4 0 0 0-11.52 0L392.192 379.072l-255.104 37.12a6.4 6.4 0 0 0-3.52 10.88L318.08 606.976l-43.584 254.08a6.4 6.4 0 0 0 9.28 6.72zM313.6 924.48a70.4 70.4 0 0 1-102.144-74.24l37.888-220.928L88.96 472.96A70.4 70.4 0 0 1 128 352.896l221.76-32.256 99.2-200.96a70.4 70.4 0 0 1 126.208 0l99.2 200.96 221.824 32.256a70.4 70.4 0 0 1 39.04 120.064L774.72 629.376l37.888 220.928a70.4 70.4 0 0 1-102.144 74.24L512 820.096l-198.4 104.32z"/></svg>'


def strip_tags(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


def render_ranges(text,ranges):
    boundaries={0,len(text)}
    for r in ranges:
        boundaries.add(r["start"]); boundaries.add(r["end"])
    points=sorted(boundaries); out=[]; anchored=set()
    for left,right in zip(points,points[1:]):
        if right<=left: continue
        active=[r for r in ranges if r["start"]<=left and right<=r["end"]]
        vocab=[r for r in active if r["kind"]=="vocab"]
        if len(vocab)>1: raise ValueError("overlapping vocabulary ranges are not supported")
        classes=[]
        if any(r["kind"]=="sentence" for r in active): classes.append("hl-syntax")
        if any(r["kind"]=="phrase" for r in active): classes.append("hl-phrase")
        if vocab and vocab[0].get("study_notes"): classes.append("hl-word")
        piece=esc(text[left:right])
        if any(r["kind"]=="italic" for r in active):
            piece=f'<em>{piece}</em>'
        if vocab:
            v=vocab[0]; cls="vocab-link" if v.get("study_notes") else "exam-vocab-link"
            anchor=""
            aid=v.get("anchor_id")
            if aid and aid not in anchored:
                anchor=f' id="{esc(aid)}"'; anchored.add(aid)
            piece=f'<a{anchor} class="{cls}" href="#lex-{esc(v["lexical_id"])}">{piece}</a>'
        if classes: piece=f'<span class="{" ".join(classes)}">{piece}</span>'
        out.append(piece)
    result="".join(out)
    if strip_tags(result)!=text: raise ValueError("rendered English text changed visible original")
    return result


def render_vocabulary(items):
    if not items: return ""
    rows=[]
    for v in items:
        surface=esc(v.get("surface")); meaning=esc(v.get("meaning_zh")); ipa=esc(v.get("uk_phonetic")); pos=esc(v.get("pos")); labels=render_labels(v.get("labels",[])); note=esc(v.get("note_zh"))
        if not surface or not meaning: continue
        ipa_html=f'<span class="ipa">{ipa}</span>' if ipa else ""
        pos_html=f'<span class="pos">{pos}</span>' if pos else ""
        note_html=f'<div class="note-extra">{note}</div>' if note else ""
        rows.append(f'<li><a class="vocab-link" href="#lex-{esc(v.get("lexical_id"))}"><span class="note-term">{surface}</span></a>{ipa_html} {pos_html} <span class="vocab-meaning">{meaning}</span> {labels}{note_html}</li>')
    return '<div class="note-section"><h4>重点单词</h4><ul>'+"".join(rows)+'</ul></div>' if rows else ""


def render_phrases(items):
    if not items: return ""
    rows=[]
    for ph in items:
        term=esc(ph.get("term")); explanation=esc(ph.get("explanation_zh")); labels=render_labels(ph.get("labels",[]))
        if term and explanation: rows.append(f'<li><span class="note-term">{term}</span> {labels}<br>{explanation}</li>')
    return '<div class="note-section"><h4>短语 / 表达</h4><ul>'+"".join(rows)+'</ul></div>' if rows else ""


def render_notes(block):
    content="".join(x for x in [render_vocabulary(block.get("vocabulary",[])),render_phrases(block.get("phrase_notes",[]))] if x)
    return content or '<p class="muted">本段无额外精读笔记。</p>'


def chart_data_uri(path):
    p=Path(path)
    mime=mimetypes.guess_type(p.name)[0] or "image/png"
    return f'data:{mime};base64,{base64.b64encode(p.read_bytes()).decode("ascii")}'


def render_cefr_statistics(cefr_chart=None):
    if not cefr_chart or not Path(cefr_chart).exists():
        return ""
    return (
        '<section class="cefr-statistics" aria-labelledby="cefr-statistics-heading">'
        '<h2 id="cefr-statistics-heading">单词难度统计</h2>'
        f'<div class="cefr-chart-wrap"><img class="cefr-chart" src="{chart_data_uri(cefr_chart)}" '
        'alt="A1至C2单词难度分布"></div></section>'
    )


def render_vocabularies(entries,after_cefr=False):
    rows=[]
    for e in entries:
        lemma=esc(e.get("lemma")); ipa=esc(e.get("uk_phonetic")); pos=esc(e.get("pos")); meaning=esc(e.get("meaning_zh")); labels=render_labels(e.get("labels",[])); target=esc(e.get("target_id"))
        if not lemma or not pos or not meaning or not target: continue
        ret=""
        if e.get("first_occurrence_anchor"):
            ret=f'<a class="vocabulary-return-link" href="#{esc(e["first_occurrence_anchor"])}" title="返回原文" aria-label="返回原文中首次出现的位置"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 7 4 12l5 5"></path><path d="M4 12h9a7 7 0 0 1 7 7"></path></svg></a>'
        ipa_html=f'<span class="ipa">{ipa}</span> ' if ipa else ""
        rows.append(f'<article class="vocabulary-entry" id="{target}"><div class="vocabulary-head"><span class="vocabulary-word">{lemma}</span> {labels}{ret}</div><div class="vocabulary-details">{ipa_html}<span>{pos}</span> <span>{meaning}</span></div></article>')
    content="".join(rows) or '<p class="vocabulary-empty">本篇无新增生词。</p>'
    extra_class=" after-cefr" if after_cefr else ""
    return f'<section class="article-vocabulary{extra_class}" aria-labelledby="vocabularies-heading"><h2 id="vocabularies-heading">Vocabularies｜生词表</h2><div class="vocabularies-grid">{content}</div></section>'


def render_html(data,cefr_chart=None):
    p=build(data); out=[]
    src=p.get("source",{}) or {}
    meta_bits=[esc(x) for x in [src.get("name"),src.get("published_date")] if x]
    meta=" · ".join(meta_bits)
    if src.get("url"):
        link=f'<a href="{esc(src["url"])}" target="_blank" rel="noopener noreferrer">source</a>'
        meta=f'{meta} · {link}' if meta else link
    audio_html=""
    audio=(p.get("audio") or {}).get("url") if isinstance(p.get("audio"),dict) else None
    if audio:
        if is_direct_audio_url(audio):
            meta += (' · ' if meta else '') + '<button type="button" class="audio-play-button" data-audio-toggle="#article-audio-player" aria-label="play audio" title="play audio">'+headphone_svg()+'</button>'
            audio_html=f'<div id="article-audio-player" class="audio-player-wrap" hidden><audio controls preload="none" src="{esc(audio)}"></audio></div>'
        else:
            meta += (' · ' if meta else '') + f'<a class="audio-link" href="{esc(audio)}" target="_blank" rel="noopener noreferrer" aria-label="open audio" title="open audio">{headphone_svg()}</a>'

    out.append('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">')
    out.append(f'<title>{esc(p["title"])}</title><style>{_font_face_css(data)}{CSS}</style></head><body><main class="page"><header class="header">')
    out.append(f'<h1>{render_ranges(p["title"],p["title_ranges"])}</h1><p class="title-zh">{esc(p["title_zh"])}</p>')
    if p.get("subtitle"):
        out.append(f'<p class="subtitle">{render_ranges(p["subtitle"],p["subtitle_ranges"])}</p><p class="subtitle-zh">{esc(p.get("subtitle_zh"))}</p>')
    if meta: out.append(f'<p class="meta">{meta}</p>')
    if audio_html: out.append(audio_html)
    if p.get("cefr"):
        out.append(f'<p class="cefr-level">CEFR level: <strong>{esc(p["cefr"].get("estimated_reading_level"))}</strong></p>')
    out.append('</header>')

    intro=p.get("intro_note")
    if intro:
        out.append('<section class="intro-note"><h2>全文导读｜Summary</h2>')
        out.append(f'<p class="intro-item">{intro_summary_svg()}<span class="intro-item-content"><strong>全文概要：</strong>{esc(intro.get("summary_zh"))}</span></p>')
        out.append(f'<p class="intro-item">{intro_structure_svg()}<span class="intro-item-content"><strong>结构主线：</strong>{esc(intro.get("structure_zh"))}</span></p>')
        out.append(f'<p class="intro-item">{intro_writing_svg()}<span class="intro-item-content"><strong>写作特色：</strong>{esc(intro.get("writing_features_zh"))}</span></p></section>')

    for b in p["body"]:
        if b["type"]=="heading":
            tag={1:"h2",2:"h3",3:"h4"}[b["level"]]
            heading_text=render_ranges(b["text"],italic_ranges(b["text"],b.get("inline_runs",[])))
            out.append(f'<section class="doc-heading level-{b["level"]}"><{tag}>{heading_text}</{tag}><div class="heading-zh">{esc(b["translation_zh"])}</div></section>')
            continue
        n=b["number"]; func=esc(b["paragraph_function_zh"])
        out.append(f'<section class="paragraph-card" id="p{n}" aria-label="Paragraph {n}"><div class="paragraph-function" aria-label="段落功能：{func}"><span class="paragraph-function-icon" aria-hidden="true">💡</span><span class="paragraph-function-text">{func}</span></div>')
        out.append('<div class="left-panel"><div class="block-label">English original</div>')
        out.append(f'<div class="original">{render_ranges(b["text"],b["ranges"])}</div><div class="block-label translation-label">中文直译</div><div class="translation">{esc(b["translation_zh"])}</div>')
        for s in b.get("sentences",[]):
            if s.get("sentence_note_zh"): out.append(f'<div class="sentence-note"><strong>重点句解析：</strong>{esc(s["sentence_note_zh"])}</div>')
        out.append('</div><div class="splitter" role="separator" aria-orientation="vertical" aria-label="Drag to adjust column width"></div><aside class="right-panel"><h3>笔记｜Note</h3>')
        out.append(render_notes(b)); out.append('</aside></section>')

    has_cefr_chart=bool(cefr_chart and Path(cefr_chart).exists())
    if has_cefr_chart:
        out.append(render_cefr_statistics(cefr_chart))
    out.append(render_vocabularies(p["vocab_entries"],after_cefr=has_cefr_chart))
    out.append('<footer class="footer">© JEnglish | AI-generated.</footer></main>')
    out.append(JS); out.append('</body></html>')
    return "".join(out)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("study_json"); ap.add_argument("output_html"); ap.add_argument("--cefr-chart"); a=ap.parse_args()
    d=json.loads(Path(a.study_json).read_text(encoding="utf-8")); Path(a.output_html).write_text(render_html(d,a.cefr_chart),encoding="utf-8"); print(a.output_html)


if __name__=="__main__": main()
