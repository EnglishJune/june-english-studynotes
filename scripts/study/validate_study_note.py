#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from jsonschema import Draft202012Validator

def norm_join(sentences):
    return " ".join(" ".join(s.get("text","").split()) for s in sentences).strip()
def norm_text(text): return " ".join(str(text).split())
def validate(data,schema):
    errors=[e.message for e in Draft202012Validator(schema).iter_errors(data)]
    if bool(data.get("is_complete_article")) != (data.get("intro_note") is not None):
        errors.append("intro_note must be non-null iff is_complete_article is true")
    if data.get("subtitle") is None and data.get("subtitle_zh") is not None:
        errors.append("subtitle_zh must be null when subtitle is null")
    if data.get("subtitle") is not None and not str(data.get("subtitle_zh") or "").strip():
        errors.append("subtitle_zh must be non-empty when subtitle exists")
    para_by_num={}
    pno=0
    lexical={}
    for i,b in enumerate(data.get("body",[])):
        if b.get("inline_runs") and "".join(r.get("text","") for r in b["inline_runs"])!=b.get("text",""):
            errors.append(f"body[{i}] inline_runs mismatch")
        if b.get("type")!="paragraph": continue
        pno+=1; para_by_num[pno]=b
        if b.get("number")!=pno: errors.append(f"paragraph numbering mismatch at body[{i}]")
        sns=b.get("sentences",[])
        for j,s in enumerate(sns,1):
            if s.get("number")!=j: errors.append(f"P{pno} sentence numbering mismatch")
            if s.get("inline_runs") and "".join(r.get("text","") for r in s["inline_runs"])!=s.get("text",""):
                errors.append(f"P{pno}S{j} inline_runs mismatch")
        if norm_join(sns)!=norm_text(b.get("text","")): errors.append(f"P{pno} sentences do not reconstruct paragraph text")
        for v in b.get("vocabulary",[]):
            if v.get("surface") not in b.get("text",""): errors.append(f"P{pno} vocabulary surface not in paragraph: {v.get('surface')}")
        for ph in b.get("phrase_notes",[]):
            if ph.get("surface") not in b.get("text",""): errors.append(f"P{pno} phrase surface not in paragraph: {ph.get('surface')}")
    for e in data.get("Vocabularies",{}).get("entries",[]):
        lid=e.get("lexical_id")
        if lid in lexical: errors.append(f"duplicate lexical_id {lid}")
        lexical[lid]=e
        for occ in e.get("occurrences",[]):
            p=para_by_num.get(occ.get("paragraph"));
            if not p: errors.append(f"occurrence {lid} invalid paragraph"); continue
            si=occ.get("sentence",0)-1
            if si<0 or si>=len(p.get("sentences",[])): errors.append(f"occurrence {lid} invalid sentence"); continue
            text=p["sentences"][si]["text"]; a=occ.get("start",-1); z=occ.get("end",-1)
            if not (0<=a<z<=len(text)) or text[a:z]!=occ.get("surface"):
                errors.append(f"occurrence {lid} offset mismatch at P{occ.get('paragraph')}S{occ.get('sentence')}")
    for p in para_by_num.values():
        for v in p.get("vocabulary",[]):
            if v.get("lexical_id") not in lexical: errors.append(f"paragraph vocabulary missing lexical master: {v.get('lexical_id')}")
    return errors

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("study_json"); ap.add_argument("--schema",default=str(Path(__file__).resolve().parents[2]/"schemas/june-english-core-read-study-note-v1.schema.json")); a=ap.parse_args()
    d=json.loads(Path(a.study_json).read_text(encoding="utf-8")); s=json.loads(Path(a.schema).read_text(encoding="utf-8")); errs=validate(d,s)
    if errs:
        print("INVALID"); [print("-",x) for x in errs]; raise SystemExit(1)
    print("VALID")
if __name__=="__main__": main()
