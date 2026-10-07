#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from jsonschema import Draft202012Validator

def validate(data,schema):
    errors=[e.message for e in Draft202012Validator(schema).iter_errors(data)]
    if data.get("title_origin")=="generated" and data.get("title_inline_runs"):
        errors.append("generated title must have empty title_inline_runs")
    p=0
    for i,b in enumerate(data.get("body",[])):
        runs=b.get("inline_runs",[])
        if runs and "".join(r.get("text","") for r in runs)!=b.get("text",""):
            errors.append(f"body[{i}] inline_runs do not reconstruct text")
        for r in runs:
            if any(m!="italic" for m in r.get("marks",[])): errors.append(f"body[{i}] has unsupported mark")
        if b.get("type")=="paragraph":
            p+=1
            if b.get("number")!=p: errors.append(f"paragraph numbering mismatch at body[{i}]")
    if data.get("title_inline_runs") and "".join(r.get("text","") for r in data["title_inline_runs"])!=data.get("title"):
        errors.append("title_inline_runs do not reconstruct title")
    sub=data.get("subtitle")
    if sub is None and data.get("subtitle_inline_runs"): errors.append("null subtitle must have empty subtitle_inline_runs")
    if sub is not None and data.get("subtitle_inline_runs") and "".join(r.get("text","") for r in data["subtitle_inline_runs"])!=sub:
        errors.append("subtitle_inline_runs do not reconstruct subtitle")
    return errors

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("article_json"); ap.add_argument("--schema",default=str(Path(__file__).resolve().parents[2]/"schemas/english-core-read-article-note-v1.schema.json")); a=ap.parse_args()
    d=json.loads(Path(a.article_json).read_text(encoding="utf-8")); s=json.loads(Path(a.schema).read_text(encoding="utf-8")); errs=validate(d,s)
    if errs:
        print("INVALID"); [print("-",e) for e in errs]; raise SystemExit(1)
    print("VALID")
if __name__=="__main__": main()
