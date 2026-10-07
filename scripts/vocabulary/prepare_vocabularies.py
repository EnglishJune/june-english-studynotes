#!/usr/bin/env python3
"""Prepare lexical-master candidates from study-note paragraph vocabulary + NETEM/CET6.
This is a pre-finalisation draft: database-only entries may have blank pos/definition_en/meaning_zh.
Agent fills those semantic fields, then run finalize_vocabularies.py.
"""
from __future__ import annotations
import argparse,json,re,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"utils"))
from text import lexical_id
from youdao_ipa import STATUS_FOUND, query_youdao_uk_ipa_result, normalise_youdao_ipa
TOKEN_RE=re.compile(r"[A-Za-z]+(?:[-’'][A-Za-z]+)*")
FIXED_LABEL_ORDER=["研","CET-6","GRE/GMAT","IELTS","C1","C2"]

def nw(s): return str(s or "").replace("’","'").strip().lower()
def uniq(xs):
    out=[]; seen=set()
    for x in xs:
        if x and x not in seen: seen.add(x); out.append(x)
    return out

def labels(xs):
    vals=[]
    for x in xs or []:
        x=str(x).strip(); x="IELTS" if x.lower()=="ielts academic" else (x.upper() if x.lower() in {"c1","c2"} else x)
        if x and x not in vals: vals.append(x)
    return [x for x in FIXED_LABEL_ORDER if x in vals]+[x for x in vals if x not in FIXED_LABEL_ORDER]

def lemma_candidates(w):
    w=nw(w); out=[w]
    if w.endswith("ies") and len(w)>4: out.append(w[:-3]+"y")
    if w.endswith("ed") and len(w)>4: out += [w[:-1],w[:-2],w[:-2]+"e"]
    if w.endswith("ing") and len(w)>5: out += [w[:-3],w[:-3]+"e"]
    if w.endswith("s") and not w.endswith(("ss","us","is")) and len(w)>3: out.append(w[:-1])
    return uniq(out)

def ro(path): return sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro",uri=True)
def load_db(root):
    netem={}; cet={}; oald={}
    with ro(root/"June_netem_list.sqlite3") as c:
        for w,d,l in c.execute("SELECT word, definition, difficulty_level FROM netem_full_list WHERE is_function_word=0 AND difficulty_level IN ('B2','C1','C2')"):
            if isinstance(w,str) and w.strip() and not re.search(r"\s",w.strip()): netem.setdefault(nw(w),{"word":w.strip(),"definition":(d or "").strip(),"level":l})
    with ro(root/"cet_full_list.sqlite3") as c:
        for w,d in c.execute("SELECT word, definition FROM cet WHERE cet6='★'"):
            if isinstance(w,str) and w.strip() and not re.search(r"\s",w.strip()): cet.setdefault(nw(w),{"word":w.strip(),"definition":(d or "").strip()})
    with ro(root/"OALD9_ipa_uk.sqlite") as c:
        cols={r[1] for r in c.execute("PRAGMA table_info(OALD9_ipa_uk)")}
        lemma_col="lamma" if "lamma" in cols else "lemma"
        for w,ipa in c.execute(f"SELECT {lemma_col}, ipa_uk FROM OALD9_ipa_uk"):
            if w and ipa: oald[nw(w)]=str(ipa).strip().strip("/")
    return netem,cet,oald

def resolve_lemma(surface,available):
    for x in lemma_candidates(surface):
        if x in available: return x
    return nw(surface)

def fmt_ipa(x):
    x=str(x or "").strip().strip("/")
    return f"/{x}/" if x else None

def _youdao_result(key,youdao_cache):
    if key not in youdao_cache:
        youdao_cache[key]=query_youdao_uk_ipa_result(key)
    return youdao_cache[key]

def _youdao_ipa(key,youdao_cache):
    r=_youdao_result(key,youdao_cache)
    if r.status!=STATUS_FOUND or not r.ipa: return None
    return fmt_ipa(normalise_youdao_ipa(r.ipa))

def _hyphenated_parts(lemma):
    if "-" not in lemma: return None
    parts=[nw(x) for x in lemma.split("-") if x]
    return parts if len(parts)>=2 and all(re.fullmatch(r"[a-z]+",x) for x in parts) else None

def _unique_closed_compound_parts(lemma,oald):
    k=nw(lemma)
    if not re.fullmatch(r"[a-z]+",k) or len(k)<6: return None
    splits=[]
    for i in range(3,len(k)-2):
        a,b=k[:i],k[i:]
        if a in oald and b in oald: splits.append((a,b))
    return list(splits[0]) if len(splits)==1 else None

def _compound_ipa(lemma,oald,youdao_cache):
    parts=_hyphenated_parts(nw(lemma))
    if parts is None: parts=_unique_closed_compound_parts(lemma,oald)
    if not parts: return None
    vals=[]
    for part in parts:
        ipa=fmt_ipa(oald.get(part)) if part in oald else _youdao_ipa(part,youdao_cache)
        if not ipa: return None
        inner=ipa.strip().strip("/")
        if not inner or ";" in inner: return None
        vals.append(inner)
    return fmt_ipa("-".join(vals))

def resolve_ipa(lemma,oald,runtime_ipa=None,runtime_stage_complete=False,youdao_cache=None):
    """Resolve OALD -> direct Youdao -> host Youdao -> compound.

    When the host-level Youdao stage has not yet run, stop at
    ``host_lookup_required`` rather than entering compound fallback. This mirrors
    the proven two-stage behaviour in te-weekly-json-study-notes.
    """
    k=nw(lemma); runtime_ipa=runtime_ipa or {}; youdao_cache=youdao_cache if youdao_cache is not None else {}
    if k in oald:
        return fmt_ipa(oald[k]),"oald9",{"status":"found","source":"oald9"}
    r=_youdao_result(k,youdao_cache)
    diag={"youdao_json_status":r.status}
    if r.detail: diag["youdao_json_detail"]=r.detail
    if r.http_status is not None: diag["youdao_json_http_status"]=r.http_status
    if r.status==STATUS_FOUND and r.ipa:
        return fmt_ipa(normalise_youdao_ipa(r.ipa)),"youdao_json",{"status":"found","source":"youdao_json",**diag}
    if k in runtime_ipa:
        return runtime_ipa[k],"youdao_web",{"status":"found","source":"youdao_web",**diag}
    if not runtime_stage_complete:
        return None,"host_lookup_required",{"status":"host_lookup_required","source":None,**diag}
    ipa=_compound_ipa(k,oald,youdao_cache)
    if ipa:
        return ipa,"compound",{"status":"found","source":"compound",**diag}
    return None,"unresolved",{"status":"unresolved","source":None,**diag}

def write_ipa_status(path,diagnostics):
    if not path: return
    host=[k for k,v in diagnostics.items() if v.get("status")=="host_lookup_required"]
    unresolved=[k for k,v in diagnostics.items() if v.get("status")=="unresolved"]
    payload={"schema_version":"ipa-resolution-v1","host_lookup_required":host,"unresolved":unresolved,"resolutions":diagnostics}
    Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def token_rows(study,available):
    rows=[]
    for b in study.get("body",[]):
        if b.get("type")!="paragraph": continue
        p=b["number"]
        for s in b.get("sentences",[]):
            sn=s["number"]; text=s["text"]
            for m in TOKEN_RE.finditer(text):
                surface=m.group(0); lemma=resolve_lemma(surface,available)
                proper=surface[:1].isupper() and m.start()>0 and not re.search(r"[.!?][\"'”’)]*\s*$",text[:m.start()])
                rows.append({"paragraph":p,"sentence":sn,"start":m.start(),"end":m.end(),"surface":surface,"lemma":lemma,"proper":proper})
    return rows

def build(study,asset_root,ipa_diagnostics=None):
    netem,cet,oald=load_db(asset_root); available=set(netem)|set(cet)
    diagnostics=ipa_diagnostics if ipa_diagnostics is not None else {}; youdao_cache={}
    tokens=token_rows(study,available); by_lemma={}
    for t in tokens:
        if t["proper"] or (t["lemma"] not in netem and t["lemma"] not in cet): continue
        e=by_lemma.setdefault(t["lemma"],{"lemma": (netem.get(t["lemma"]) or cet.get(t["lemma"]) or {"word":t["lemma"]})["word"],"forms_in_article":[],"uk_phonetic":None,"pos":"","definition_en":"","meaning_zh":"","labels":[],"occurrences":[],"_sources":[]})
        e["forms_in_article"].append(t["surface"]); e["occurrences"].append({k:t[k] for k in ["paragraph","sentence","start","end","surface"]})
        if t["lemma"] in netem: e["labels"].append("研"); e["_sources"].append("netem")
        if t["lemma"] in cet: e["labels"].append("CET-6"); e["_sources"].append("cet6")
    # Study-selected words. Temporary draft may contain pos/labels; these are removed from paragraph items later.
    for b in study.get("body",[]):
        if b.get("type")!="paragraph": continue
        for v in b.get("vocabulary",[]):
            surface=v.get("surface",""); lemma=nw(v.get("lemma") or surface); pos=str(v.get("pos","")).strip()
            matches=[t for t in tokens if t["paragraph"]==b["number"] and (nw(t["surface"])==nw(surface) or nw(t["lemma"])==lemma)]
            if not matches: raise ValueError(f"P{b['number']} study vocabulary surface not found: {surface!r}")
            # Key by lemma+pos when pos is known; keep DB-only lemma bucket otherwise.
            key=(lemma,pos) if pos else lemma
            e=by_lemma.get(key)
            if e is None:
                # If a database lemma-only entry exists and no conflicting study POS, promote it.
                base=by_lemma.pop(lemma,None) if lemma in by_lemma else None
                e=base or {"lemma":v.get("lemma") or lemma,"forms_in_article":[],"uk_phonetic":None,"pos":pos,"definition_en":"","meaning_zh":"","labels":[],"occurrences":[],"_sources":[]}
                e["pos"]=e.get("pos") or pos; by_lemma[key]=e
            e["meaning_zh"] = e.get("meaning_zh") or str(v.get("meaning_zh","")).strip()
            e["definition_en"] = e.get("definition_en") or str(v.get("definition_en","")).strip()
            e["labels"] += list(v.get("labels",[]) or [])
            e["_sources"].append("study")
            for t in matches:
                e["forms_in_article"].append(t["surface"])
                occ={k:t[k] for k in ["paragraph","sentence","start","end","surface"]}
                if occ not in e["occurrences"]: e["occurrences"].append(occ)
            # retain temporary pos for finaliser, but strip labels/pos from paragraph final shape later
            v["_pos"]=pos
    entries=[]
    for key,e in by_lemma.items():
        e["forms_in_article"]=uniq(e["forms_in_article"]); e["labels"]=labels(e["labels"]); e["_sources"]=uniq(e["_sources"])
        e["occurrences"]=sorted(e["occurrences"],key=lambda x:(x["paragraph"],x["sentence"],x["start"],x["end"]))
        ipa,source,diag=resolve_ipa(e["lemma"],oald,runtime_stage_complete=False,youdao_cache=youdao_cache); e["uk_phonetic"]=ipa; e["_ipa_source"]=source; diagnostics[nw(e["lemma"])]=diag
        entries.append(e)
    entries.sort(key=lambda e:(e["occurrences"][0]["paragraph"],e["occurrences"][0]["sentence"],e["occurrences"][0]["start"]))
    study["Vocabularies"]={"entries":entries}
    return study

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("study_json"); ap.add_argument("output_json"); ap.add_argument("--ipa-status-json"); ap.add_argument("--asset-root",default=str(Path(__file__).resolve().parents[2]/"assets/vocabulary")); a=ap.parse_args()
    d=json.loads(Path(a.study_json).read_text(encoding="utf-8")); diagnostics={}; out=build(d,Path(a.asset_root),ipa_diagnostics=diagnostics)
    Path(a.output_json).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8"); write_ipa_status(a.ipa_status_json,diagnostics)
    host=[k for k,v in diagnostics.items() if v.get("status")=="host_lookup_required"]
    print(f"prepared {len(out['Vocabularies']['entries'])} lexical entries")
    if host: print("host-level Youdao lookup required for: "+", ".join(host))
if __name__=="__main__": main()
