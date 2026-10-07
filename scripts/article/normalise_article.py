#!/usr/bin/env python3
"""Normalise adapter/model structured data into english-core-read-article-note-v1."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path


def is_non_body_paragraph(text: str) -> bool:
    lower=" ".join(text.split()).lower()
    if not lower: return True
    if lower.startswith("correction:"): return True
    if "curious about the world" in lower and "newsletter" in lower: return True
    if "sign up" in lower and "newsletter" in lower: return True
    if re.search(r"\bto enjoy our\b.*\bcoverage\b", lower) and "sign up" in lower: return True
    return False

def _runs(text, runs):
    if not runs: return []
    if "".join(str(x.get("text","")) for x in runs)==text: return runs
    raise ValueError("inline_runs do not reconstruct text")

def _guess_plain_text(text: str):
    chunks=[x.strip() for x in re.split(r"\n\s*\n", text) if x.strip()]
    if not chunks: raise ValueError("text input is empty")
    title=None; body=[]; pno=0
    if len(chunks[0])<=140 and "\n" not in chunks[0]:
        title=chunks.pop(0)
    for chunk in chunks:
        one=" ".join(chunk.split())
        if len(one)<=90 and not re.search(r"[.!?][\"')\]]?$",one) and len(one.split())<=12:
            body.append({"type":"heading","level":1,"text":one,"inline_runs":[]})
        else:
            pno+=1; body.append({"type":"paragraph","number":pno,"text":one,"inline_runs":[]})
    return title,body

def normalise(data: dict):
    title=data.get("title"); title_origin="source" if title else "generated"
    subtitle=data.get("subtitle")
    body=[]
    if isinstance(data.get("blocks"),list):
        for b in data["blocks"]:
            if not isinstance(b,dict): continue
            kind=b.get("kind") or b.get("type")
            text=str(b.get("text","")).strip()
            if not text: continue
            if kind=="title" and not title:
                title=text; title_origin="source"; title_runs=b.get("inline_runs",[]); continue
            if kind=="subtitle" and subtitle is None:
                subtitle=text; subtitle_runs=b.get("inline_runs",[]); continue
            if kind=="heading": body.append({"type":"heading","level":int(b.get("level",1)),"text":text,"inline_runs":_runs(text,b.get("inline_runs",[]))})
            elif kind=="paragraph":
                clean=" ".join(text.split())
                if is_non_body_paragraph(clean): continue
                body.append({"type":"paragraph","number":0,"text":clean,"inline_runs":_runs(text,b.get("inline_runs",[])) if clean==text and text=="".join(x.get("text","") for x in b.get("inline_runs",[])) else []})
    elif isinstance(data.get("text"),str):
        guessed_title,body=_guess_plain_text(data["text"])
        if not title and guessed_title: title=guessed_title; title_origin="source"
    elif isinstance(data.get("body"),list):
        body=data["body"]
    else: raise ValueError("input must contain blocks, text, or body")
    if not title:
        title=(data.get("generated_title") or "Untitled English Article").strip(); title_origin="generated"
    pno=0
    for b in body:
        if b.get("type")=="paragraph": pno+=1; b["number"]=pno
    if not body: raise ValueError("article body is empty")
    src=data.get("source") if isinstance(data.get("source"),dict) else {}
    audio=data.get("audio") if isinstance(data.get("audio"),dict) and data["audio"].get("url") else None
    return {
      "schema_version":"english-core-read-article-note-v1","language":"en","title":title,
      "title_origin":title_origin,"title_inline_runs":([] if title_origin=="generated" else data.get("title_inline_runs",locals().get("title_runs",[])) or []),
      "subtitle":subtitle if subtitle else None,"subtitle_inline_runs":data.get("subtitle_inline_runs",locals().get("subtitle_runs",[])) or [],
      "source":{"name":src.get("name"),"url":src.get("url"),"published_date":src.get("published_date")},
      "audio":audio,"body":body}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input_json"); ap.add_argument("output_json"); a=ap.parse_args()
    out=normalise(json.loads(Path(a.input_json).read_text(encoding="utf-8")))
    Path(a.output_json).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
