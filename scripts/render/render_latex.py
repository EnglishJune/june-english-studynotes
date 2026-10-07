#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from build_presentation import build
from latex_text import esc, esc_en, esc_mixed, escurl, ranges_tex, inline_tex

TEMPLATE = Path(__file__).resolve().parents[2] / "assets/templates/study_notes_preamble.tex"
PRE = TEMPLATE.read_text(encoding="utf-8")

def labeltex(labels,brackets=True): return ' '.join(('['+esc(x)+']') if brackets else esc(x) for x in labels or [])

def heading_tex(b):
    sizes={1:(14,17),2:(12.5,15),3:(11,13.5)};s,bs=sizes[b['level']]
    return '\n'.join([r'\par\vspace{3mm}\noindent\textcolor{RuleGreen}{\rule{\textwidth}{0.45pt}}\par\vspace{1mm}',rf'{{\fontsize{{{s}}}{{{bs}}}\selectfont\bfseries \StudyEN{{{inline_tex(b["text"],b.get("inline_runs",[]))}}}\par}}',rf'{{\fontsize{{{max(9,s-2)}}}{{{max(11,bs-2)}}}\selectfont {esc_mixed(b["translation_zh"])}\par}}'])
def right_notes_tex(block):
    parts=[];vocabulary=block.get('vocabulary',[]) or [];phrases=block.get('phrase_notes',[]) or []
    if vocabulary:
        parts.append(r'{\fontsize{9.6}{12.2}\selectfont\begin{itemize}[leftmargin=1.2em,itemsep=0.22em,topsep=0pt,parsep=0pt]')
        for v in vocabulary:
            labels=labeltex(v.get('labels',[]),brackets=False)
            label_part=(r' \hspace{0.35em}{\fontsize{7.4}{8.6}\selectfont\color{gray} '+labels+r'}') if labels else ''
            phonetic=r'\StudyEN{'+esc_en(v.get('uk_phonetic') or '')+'}';pos=r'\StudyEN{'+esc_en(v.get('pos') or '')+'}';note=esc_mixed(v.get('note_zh')) if v.get('note_zh') else ''
            line=(rf'\item \hyperlink{{lex-{esc(v["lexical_id"])}}}{{\color{{StudyRed}} \StudyEN{{{esc_en(v["surface"])}}}}} '
                  rf'{{\fontsize{{8.4}}{{10}}\selectfont {phonetic}}} '
                  rf'{{\fontsize{{8.4}}{{10}}\selectfont {pos}}}{label_part}'
                  rf'\\[-0.15em]{{\fontsize{{9.6}}{{12.2}}\selectfont {esc_mixed(v["meaning_zh"])}}}')
            if note:line+=rf'\\[-0.15em]{{\fontsize{{8.6}}{{10.8}}\selectfont\color{{darkgray}} {note}}}'
            parts.append(line)
        parts.append(r'\end{itemize}}')
    if vocabulary and phrases:parts.append(r'\vspace{0.45em}\hrule\vspace{0.42em}')
    if phrases:
        parts.append(r'{\fontsize{9.6}{12.2}\selectfont\begin{itemize}[leftmargin=1.2em,itemsep=0.22em,topsep=0pt,parsep=0pt]')
        for ph in phrases:
            labels=labeltex(ph.get('labels',[]),brackets=False)
            label_part=(r'\hspace{0.35em}{\fontsize{7.4}{8.6}\selectfont\color{gray} '+labels+r'}') if labels else ''
            parts.append(rf'\item {{\color{{StudyRed}} \StudyEN{{{esc_en(ph["term"])}}}}}{label_part}\\[-0.15em]{{\fontsize{{9.6}}{{12.2}}\selectfont {esc_mixed(ph["explanation_zh"])}}}')
        parts.append(r'\end{itemize}}')
    return '\n'.join(parts)

def render_latex(data,cefr_chart=None):
    p=build(data);o=[PRE,r'\centering',rf'{{\fontsize{{16}}{{18}}\selectfont\bfseries \StudyEN{{{ranges_tex(p["title"],p["title_ranges"])}}}\par}}',rf'{{\fontsize{{10}}{{12}}\selectfont {esc_mixed(p["title_zh"])}\par}}']
    if p.get('subtitle'):o += [rf'\vspace{{1mm}}{{\fontsize{{11}}{{13}}\selectfont\bfseries \StudyEN{{{ranges_tex(p["subtitle"],p["subtitle_ranges"])}}}\par}}',rf'{{\fontsize{{9.5}}{{11.5}}\selectfont {esc_mixed(p.get("subtitle_zh"))}\par}}']
    src=p.get('source',{}) or {}
    meta=[esc_en(x) for x in [src.get('name'),src.get('published_date')] if x]
    if src.get('url'):meta.append(r'\href{'+escurl(src['url'])+'}{source}')
    audio=p.get('audio')
    if isinstance(audio,dict) and audio.get('url'):meta.append(r'\href{'+escurl(audio['url'])+'}{audio}')
    o.append(rf'\vspace{{1mm}}{{\fontsize{{8.3}}{{9.8}}\selectfont\color{{gray}} \StudyEN{{{ " · ".join(meta)}}}\par}}')
    if p.get('cefr'):o.append(rf'\vspace{{1mm}}{{\fontsize{{8.8}}{{10.5}}\selectfont\color{{gray}} CEFR level: \textbf{{{esc(p["cefr"]["estimated_reading_level"])}}}\par}}')
    o.append(r'\par\vspace{2.8mm}\RaggedRight')
    intro=p.get('intro_note')
    if intro:
        o.append(r'\begin{tcolorbox}[enhanced,breakable,colback=SummaryBG,colframe=SummaryBG,boxrule=0pt,borderline west={2pt}{0pt}{RuleGreen},left=3mm,right=3mm,top=2mm,bottom=2.4mm]')
        o.append(r'{\fontsize{11.3}{13.8}\selectfont\bfseries 全文导读｜Summary}\par\vspace{1.3mm}')
        o.append(r'\begingroup\leftskip=4mm\rightskip=1mm\setlength{\parskip}{1.5mm}')
        for lab,k in [('全文概要：','summary_zh'),('结构主线：','structure_zh'),('写作特色：','writing_features_zh')]:o.append(rf'{{\fontsize{{10.1}}{{14.4}}\selectfont\bfseries {lab}}}{{\fontsize{{10.1}}{{14.4}}\selectfont {esc_mixed(intro[k])}}}\par')
        o += [r'\endgroup',r'\end{tcolorbox}']
    for b in p['body']:
        if b['type']=='heading':o.append(heading_tex(b));continue
        n=b['number'];o += [rf'\hypertarget{{p-{n}}}{{}}',r'\needspace{7\baselineskip}',r'\par\vspace{2.2mm}\noindent\textcolor{RuleGreen}{\rule{\textwidth}{0.45pt}}\par\vspace{1mm}',rf'\noindent\textcolor{{StudyRed}}{{\fontsize{{10.2}}{{12.4}}\selectfont\bfseries \textbullet\;{esc_mixed(b["paragraph_function_zh"])}}}\vspace{{1.15mm}}',r'\begin{paracol}{2}',r'\columncolor{black}',r'\begin{StudyEnglish}',rf'{{\fontsize{{11.4}}{{19.7}}\selectfont\raggedright {ranges_tex(b["text"],b["ranges"])}\par}}',r'\end{StudyEnglish}',r'\par\vspace{1.5mm}',rf'{{\fontsize{{10.4}}{{18}}\selectfont {esc_mixed(b["translation_zh"])}\par}}']
        for s in b.get('sentences',[]):
            if s.get('sentence_note_zh'):
                o += [r'\par\vspace{1.7mm}',r'\begin{tcolorbox}[enhanced,breakable,colback=SentenceBG,colframe=SentenceBG,boxrule=0pt,borderline west={2.1pt}{0pt}{SentenceRule},left=2.2mm,right=2.2mm,top=1.2mm,bottom=1.2mm,before skip=0pt,after skip=0pt]',rf'{{\fontsize{{9.6}}{{16.6}}\selectfont\bfseries 重点句解析：}}\;{{\fontsize{{9.6}}{{16.6}}\selectfont {esc_mixed(s["sentence_note_zh"])}\par}}',r'\end{tcolorbox}']
        o += [r'\switchcolumn',r'\columncolor{black}',r'\begin{tcolorbox}[enhanced,breakable,colback=NoteBG,colframe=NoteBG,boxrule=0pt,left=1.7mm,right=1.7mm,top=1.05mm,bottom=1.05mm,before skip=0pt,after skip=0pt]',right_notes_tex(b),r'\end{tcolorbox}',r'\end{paracol}']
    has_cefr_chart=bool(cefr_chart)
    if cefr_chart and not Path(cefr_chart).is_file():raise FileNotFoundError(f'CEFR chart missing: {cefr_chart}')
    o.append(r'\clearpage')
    if has_cefr_chart:
        o.append(r'\begin{center}{\fontsize{15.5}{18}\selectfont\bfseries 单词难度统计}\end{center}')
        o.append(rf'\vspace{{1mm}}\begin{{center}}\includegraphics[width=.78\textwidth]{{{chart_filename(cefr_chart)}}}\end{{center}}\vspace{{1.5mm}}')
    o.append(r'\begin{center}{\fontsize{17}{20}\selectfont\bfseries Vocabularies｜生词表}\end{center}')
    o.append(r'\raggedcolumns\begin{multicols*}{2}')
    for e in p['vocab_entries']:
        refs=' '.join(rf'\hyperlink{{p-{x}}}{{\textcolor{{gray}}{{\textit{{P{x}}}}}}}' for x in sorted({z['paragraph'] for z in e.get('occurrences',[])}));labs=labeltex(e.get('labels',[]))
        o += [r'\Needspace{2.7\baselineskip}',rf'\hypertarget{{lex-{esc(e["lexical_id"])}}}{{}}{{\fontsize{{10.5}}{{12.2}}\selectfont\bfseries\color{{StudyRed}} \StudyEN{{{esc_en(e["lemma"])}}}}} {{\fontsize{{7.4}}{{8.6}}\selectfont\color{{gray}} {labs}}}\hspace{{.4em}}{refs}\\[-.08em]',rf'{{\fontsize{{8.7}}{{10.5}}\selectfont \StudyEN{{{esc_en(e.get("uk_phonetic") or "")}}}\hspace{{.45em}}\StudyEN{{{esc_en(e["pos"])}}}\hspace{{.6em}}{{\fontsize{{9.3}}{{10.9}}\selectfont {esc_mixed(e["meaning_zh"])}}}}}\par\vspace{{2.3mm}}']
    o += [r'\end{multicols*}',r'\end{document}']
    return '\n'.join(o)+'\n'


def chart_filename(path):
    return 'cefr_chart'+Path(path).suffix.lower()


def write_latex(data,output_tex,cefr_chart=None):
    text=render_latex(data,cefr_chart)
    output=Path(output_tex)
    output.parent.mkdir(parents=True,exist_ok=True)
    if cefr_chart:
        source=Path(cefr_chart)
        destination=output.parent/chart_filename(source)
        if source.resolve()!=destination.resolve():shutil.copy2(source,destination)
    output.write_text(text,encoding='utf-8')
    return output


def main():
    ap=argparse.ArgumentParser();ap.add_argument('study_json');ap.add_argument('output_tex');ap.add_argument('--cefr-chart');a=ap.parse_args()
    data=json.loads(Path(a.study_json).read_text(encoding='utf-8'))
    print(write_latex(data,a.output_tex,a.cefr_chart))


if __name__=='__main__':main()
