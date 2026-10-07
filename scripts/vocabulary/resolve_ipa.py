#!/usr/bin/env python3
"""Complete British IPA after the host-level Youdao lookup stage.

The runtime Youdao file mirrors te-weekly-json-study-notes exactly:
  {"exact-lemma": {"ipa_uk": "...", "source": "youdao_web"}}

A separate reliable-web file may be used only after the Youdao + compound stages
remain unresolved, preserving this skill's existing broader-web fallback.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from prepare_vocabularies import load_db, resolve_ipa, fmt_ipa, nw, write_ipa_status


def _strict_runtime_map(path,expected_source):
    if not path:return {}
    raw=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw,dict): raise ValueError("runtime IPA JSON must be an object keyed by exact lemma strings")
    out={}
    for lemma,payload in raw.items():
        if not isinstance(lemma,str) or not lemma.strip() or not isinstance(payload,dict):
            raise ValueError("runtime IPA entries must use non-empty lemma keys and object values")
        if payload.get("source")!=expected_source:
            raise ValueError(f"runtime IPA for {lemma!r} must have source={expected_source!r}")
        ipa=payload.get("ipa_uk")
        if not isinstance(ipa,str) or not fmt_ipa(ipa):
            raise ValueError(f"runtime IPA for {lemma!r} must contain non-empty string ipa_uk")
        out[nw(lemma)]=fmt_ipa(ipa)
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("study_json"); ap.add_argument("output_json")
    ap.add_argument("--runtime-ipa-json",required=True,help="host-level exact Youdao evidence; may be an empty {} after the host lookup stage is completed")
    ap.add_argument("--reliable-ipa-json",help="optional broader reliable British-IPA evidence used only after Youdao and compound fallback")
    ap.add_argument("--ipa-status-json")
    ap.add_argument("--asset-root",default=str(Path(__file__).resolve().parents[2]/"assets/vocabulary"))
    a=ap.parse_args()
    d=json.loads(Path(a.study_json).read_text(encoding="utf-8")); _,_,oald=load_db(Path(a.asset_root))
    runtime=_strict_runtime_map(a.runtime_ipa_json,"youdao_web")
    reliable=_strict_runtime_map(a.reliable_ipa_json,"reliable_web") if a.reliable_ipa_json else {}
    diagnostics={}; youdao_cache={}
    for e in d.get("Vocabularies",{}).get("entries",[]):
        if e.get("uk_phonetic"):
            continue
        key=nw(e.get("lemma",""))
        ipa,source,diag=resolve_ipa(key,oald,runtime_ipa=runtime,runtime_stage_complete=True,youdao_cache=youdao_cache)
        if ipa is None and key in reliable:
            ipa=reliable[key]; source="reliable_web"; diag={**diag,"status":"found","source":"reliable_web"}
        e["uk_phonetic"]=ipa
        e["_ipa_source"]=source
        diagnostics[key]=diag
    write_ipa_status(a.ipa_status_json,diagnostics)
    Path(a.output_json).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
    unresolved=[k for k,v in diagnostics.items() if v.get("status")=="unresolved"]
    if unresolved: print("British IPA unresolved after automatic fallbacks: "+", ".join(unresolved))

if __name__=="__main__":main()
