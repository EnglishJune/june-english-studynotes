#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from latex_text import italic_ranges


def sentence_offsets(paragraph):
    text=paragraph["text"]; cursor=0; out={}
    for s in paragraph.get("sentences",[]):
        st=s["text"]; idx=text.find(st,cursor)
        if idx<0: raise ValueError(f"P{paragraph['number']} sentence text cannot be located")
        out[s["number"]]=(idx,idx+len(st)); cursor=idx+len(st)
    return out


def build(data):
    entries_list=list(data.get("Vocabularies",{}).get("entries",[]))
    entries={e["lexical_id"]:e for e in entries_list}
    first_occurrence={}
    paragraph_refs={lid:set() for lid in entries}
    blocks=[]

    for b in data.get("body",[]):
        if b.get("type")=="heading":
            blocks.append({**b})
            continue

        pno=b["number"]
        offsets=sentence_offsets(b)
        study_ids={v.get("lexical_id") for v in b.get("vocabulary",[]) if v.get("lexical_id")}
        ranges=italic_ranges(b["text"], b.get("inline_runs", []))

        for e in entries_list:
            lid=e["lexical_id"]
            occ_index=0
            for occ in e.get("occurrences",[]):
                if occ["paragraph"]!=pno:
                    continue
                occ_index+=1
                ss,se=offsets[occ["sentence"]]
                start=ss+occ["start"]; end=ss+occ["end"]
                if b["text"][start:end] != occ["surface"]:
                    raise ValueError(f"P{pno} vocabulary occurrence mismatch for {lid}: {occ['surface']!r}")
                anchor=f"occ-{lid}-p{pno}-{occ_index}"
                first_occurrence.setdefault(lid,anchor)
                paragraph_refs.setdefault(lid,set()).add(pno)
                ranges.append({
                    "start":start,
                    "end":end,
                    "kind":"vocab",
                    "lexical_id":lid,
                    "anchor_id":anchor,
                    "study_notes":lid in study_ids,
                })

        for ph in b.get("phrase_notes",[]):
            surface=ph.get("surface") or ph.get("term") or ""
            if not surface:
                continue
            idx=b["text"].find(surface)
            if idx<0:
                raise ValueError(f"P{pno} phrase surface is not an exact substring: {surface!r}")
            ranges.append({"start":idx,"end":idx+len(surface),"kind":"phrase"})

        for s in b.get("sentences",[]):
            if s.get("sentence_note_zh"):
                ss,se=offsets[s["number"]]
                ranges.append({"start":ss,"end":se,"kind":"sentence"})

        enriched_vocab=[]
        for v in b.get("vocabulary",[]):
            lid=v.get("lexical_id")
            master=entries.get(lid)
            if master is None:
                raise ValueError(f"P{pno} vocabulary lexical_id does not resolve: {lid!r}")
            enriched_vocab.append({
                **v,
                "uk_phonetic":master.get("uk_phonetic"),
                "pos":master.get("pos",""),
                "labels":master.get("labels",[]),
            })

        blocks.append({
            **b,
            "translation_zh":"".join(s.get("translation_zh","") for s in b.get("sentences",[])),
            "vocabulary":enriched_vocab,
            "ranges":ranges,
        })

    vocab_entries=[]
    for e in entries_list:
        lid=e["lexical_id"]
        vocab_entries.append({
            **e,
            "target_id":f"lex-{lid}",
            "first_occurrence_anchor":first_occurrence.get(lid),
            "paragraph_refs":sorted(paragraph_refs.get(lid,set())),
        })

    return {
        "title":data["title"],
        "title_ranges":italic_ranges(data["title"], data.get("title_inline_runs", [])),
        "title_zh":data["title_zh"],
        "subtitle":data.get("subtitle"),
        "subtitle_ranges":italic_ranges(data.get("subtitle") or "", data.get("subtitle_inline_runs", [])),
        "subtitle_zh":data.get("subtitle_zh"),
        "source":data.get("source",{}),
        "audio":data.get("audio"),
        "intro_note":data.get("intro_note"),
        "cefr":data.get("cefr"),
        "body":blocks,
        "vocab_entries":vocab_entries,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("study_json"); ap.add_argument("output_json"); a=ap.parse_args()
    d=json.loads(Path(a.study_json).read_text(encoding="utf-8")); out=build(d); Path(a.output_json).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")


if __name__=="__main__": main()
