#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from docx import Document

def effective_italic(run) -> bool:
    if run.italic is not None:
        return bool(run.italic)
    style = getattr(run, "style", None)
    seen=set()
    while style is not None and id(style) not in seen:
        seen.add(id(style))
        font=getattr(style,"font",None)
        if font is not None and font.italic is not None:
            return bool(font.italic)
        style=getattr(style,"base_style",None)
    return False

def runs_for_paragraph(p):
    out=[]
    for r in p.runs:
        if not r.text: continue
        item={"text":r.text}
        if effective_italic(r): item["marks"]=["italic"]
        out.append(item)
    text="".join(x["text"] for x in out)
    return text,out

def style_level(name: str):
    m=re.match(r"Heading\s*([1-3])\b", name or "", re.I)
    return int(m.group(1)) if m else None

def extract(path: Path):
    doc=Document(path)
    blocks=[]
    for p in doc.paragraphs:
        text,runs=runs_for_paragraph(p)
        if not text.strip(): continue
        style_name=getattr(getattr(p,"style",None),"name","") or ""
        if style_name.lower()=="title": kind="title"
        elif style_name.lower()=="subtitle": kind="subtitle"
        else:
            lvl=style_level(style_name)
            kind="heading" if lvl else "paragraph"
        item={"kind":kind,"text":text,"inline_runs":runs}
        if kind=="heading": item["level"]=lvl
        blocks.append(item)
    return {"blocks":blocks}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input_docx"); ap.add_argument("output_json"); a=ap.parse_args()
    Path(a.output_json).write_text(json.dumps(extract(Path(a.input_docx)),ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
