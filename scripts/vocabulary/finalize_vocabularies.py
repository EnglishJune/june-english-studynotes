#!/usr/bin/env python3
"""Finalize lexical IDs and paragraph links after the Agent fills semantic blanks."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"utils"))
from text import lexical_id

def finalize(study):
    masters={}; by_lemma={}
    clean=[]
    for e in study.get("Vocabularies",{}).get("entries",[]):
        lemma=str(e.get("lemma","")).strip(); pos=str(e.get("pos","")).strip()
        if not lemma or not pos: raise ValueError(f"lexical entry requires lemma + pos before finalization: {lemma!r} {pos!r}")
        lid=lexical_id(lemma,pos)
        if lid in masters: raise ValueError(f"duplicate lexical identity: {lemma} {pos}")
        e["lexical_id"]=lid; e.pop("_sources",None); e.pop("_ipa_source",None)
        masters[lid]=e; by_lemma.setdefault(lemma.lower(),[]).append(e); clean.append(e)
    # Link each paragraph item. Temporary _pos/pos may be supplied by model in draft only.
    for b in study.get("body",[]):
        if b.get("type")!="paragraph": continue
        for v in b.get("vocabulary",[]):
            lemma=str(v.get("lemma") or v.get("surface","")).strip(); hint=str(v.pop("_pos",v.pop("pos","")) or "").strip()
            candidates=by_lemma.get(lemma.lower(),[])
            if hint: candidates=[e for e in candidates if e.get("pos")==hint]
            if len(candidates)!=1:
                raise ValueError(f"cannot uniquely link paragraph vocabulary {lemma!r}; pos hint={hint!r}; candidates={[(e['lemma'],e['pos']) for e in candidates]}")
            v["lexical_id"]=candidates[0]["lexical_id"]
            v.pop("labels",None); v.pop("definition_en",None); v.pop("uk_phonetic",None)
            v.setdefault("note_zh","")
    study["Vocabularies"]={"entries":clean}
    return study

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("study_json"); ap.add_argument("output_json"); a=ap.parse_args()
    d=json.loads(Path(a.study_json).read_text(encoding="utf-8")); out=finalize(d)
    Path(a.output_json).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8"); print("finalized lexical identities")
if __name__=="__main__": main()
