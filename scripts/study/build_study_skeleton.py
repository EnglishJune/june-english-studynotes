#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from sentence_analysis_rules import split_sentences, sentence_analysis_candidates, validate_depth

def slice_runs(text,runs,start,end):
    if not runs: return []
    out=[]; pos=0
    for r in runs:
        rt=r.get("text",""); rs, re = pos, pos+len(rt); pos=re
        a=max(start,rs); b=min(end,re)
        if a<b:
            item={"text":rt[a-rs:b-rs]}
            if r.get("marks"): item["marks"]=list(r["marks"])
            out.append(item)
    return out if "".join(x["text"] for x in out)==text[start:end] else []

def sentence_spans(text):
    parts=split_sentences(text)
    spans=[]; cursor=0
    for part in parts:
        idx=text.find(part,cursor)
        if idx<0: raise ValueError("sentence splitter output not found in paragraph")
        # Include whitespace between prior sentence and this sentence in this sentence only if it is leading source whitespace.
        start=idx; end=idx+len(part); spans.append((start,end,part)); cursor=end
    if not spans: spans=[(0,len(text),text)]
    return spans

def build(article,depth=1):
    depth=validate_depth(depth)
    body=[]
    for b in article["body"]:
        if b["type"]=="heading":
            body.append({**b,"translation_zh":""}); continue
        text=b["text"]; candidates={c["sentence"] for c in sentence_analysis_candidates(text,analysis_depth=depth)}
        sentences=[]
        for n,(start,end,s) in enumerate(sentence_spans(text),1):
            sentences.append({"number":n,"text":s,"inline_runs":slice_runs(text,b.get("inline_runs",[]),start,end),"translation_zh":"","sentence_note_zh":"" if s in candidates else None})
        body.append({"type":"paragraph","number":b["number"],"text":text,"inline_runs":b.get("inline_runs",[]),"paragraph_function_zh":"","sentences":sentences,"vocabulary":[],"phrase_notes":[]})
    return {
      "schema_version":"june-english-core-read-study-note-v1","language":"en",
      "title":article["title"],"title_origin":article["title_origin"],"title_inline_runs":article.get("title_inline_runs",[]),"title_zh":"",
      "subtitle":article.get("subtitle"),"subtitle_inline_runs":article.get("subtitle_inline_runs",[]),"subtitle_zh":"" if article.get("subtitle") else None,
      "source":article["source"],"audio":article.get("audio"),"is_complete_article":True,
      "intro_note":{"summary_zh":"","structure_zh":"","writing_features_zh":""},
      "sentence_analysis_depth":depth,"cefr":None,"body":body,"Vocabularies":{"entries":[]}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("article_json"); ap.add_argument("output_json"); ap.add_argument("--sentence-analysis-depth",type=int,choices=[1,2,3],default=1); a=ap.parse_args()
    article=json.loads(Path(a.article_json).read_text(encoding="utf-8")); out=build(article,a.sentence_analysis_depth)
    Path(a.output_json).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"built study skeleton depth={a.sentence_analysis_depth}")
if __name__=="__main__": main()
