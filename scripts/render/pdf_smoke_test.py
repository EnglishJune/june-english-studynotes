#!/usr/bin/env python3
"""Exercise the production template with punctuation and overlapping styles."""
from __future__ import annotations

import argparse
import hashlib

from render_latex import write_latex


def marked_runs(text, italic_text):
    start = text.index(italic_text)
    return [
        {"text": text[:start]},
        {"text": italic_text, "marks": ["italic"]},
        {"text": text[start + len(italic_text):]},
    ]


def smoke_data():
    sentences = [
        "Labuan Bajo, a port on the Indonesian island of Flores, has been at the sharp end of Indonesia’s tourism boom.",
        "“Visitors shouldn’t lose their spaces,” she said, explaining that phenomenal growth can bring a nasty shock to places struggling to cope with crowds.",
        """This sentence keeps 'straight quotes', "double quotes", ‘curly singles’, “curly doubles”, and italic words unchanged.""",
        r"Plain symbols: 50% & $5; tag_name #1, {braces}, \ paths, ~ and ^.",
        "Fullwidth quotes remain ＇ and ＂; tourists can follow the vocabulary links.",
    ]
    text = " ".join(sentences)
    paragraph = {
        "type": "paragraph", "number": 1, "text": text,
        "inline_runs": marked_runs(text, "italic words"),
        "paragraph_function_zh": "验证原文标点、连续整句下划线、词汇链接与原文斜体。",
        "sentences": [
            {
                "number": number, "text": sentence,
                "inline_runs": marked_runs(sentence, "italic words") if "italic words" in sentence else [],
                "translation_zh": [
                    "拉布安巴焦是印度尼西亚弗洛勒斯岛的港口，处于旅游热潮的前沿。",
                    "她指出，游客需要保留词间空格；迅速增长可能给应对人群的地方带来冲击。",
                    "本句保留直引号、单双弯引号和原文斜体。",
                    "本句检查百分号、货币符号、下划线、井号、花括号与反斜线。",
                    "全角引号保留原字符，词汇链接可跳转至生词表。",
                ][number - 1],
                "sentence_note_zh": "兼容性样例：Indonesia’s plan 是英文主语，‘游客’ 是中文引文；本句整体加红色下划线，允许自动换行，词间空格和标点均保留。" if number <= 3 else None,
            }
            for number, sentence in enumerate(sentences, 1)
        ],
        "vocabulary": [],
        "phrase_notes": [
            {"term": "at the sharp end of", "surface": "at the sharp end of", "labels": [], "explanation_zh": "处于某种活动的前沿。"},
            {"term": "cope with", "surface": "cope with", "labels": [], "explanation_zh": "应对；处理。"},
        ],
    }
    entries = []
    for lemma, surface, number, meaning, ipa, study in [
        ("tourism", "tourism", 1, "旅游业", "/ˈtʊərɪzəm/", True),
        ("phenomenal", "phenomenal", 2, "非凡的", "/fəˈnɒmɪnəl/", True),
        ("tourist", "tourists", 5, "游客", "/ˈtʊərɪst/", False),
    ]:
        pos = "adj." if lemma == "phenomenal" else "n."
        lid = "lex-" + hashlib.sha1((lemma + "\x1f" + pos).encode()).hexdigest()[:12]
        start = sentences[number - 1].index(surface)
        entries.append({
            "lexical_id": lid, "lemma": lemma, "pos": pos, "labels": [],
            "uk_phonetic": ipa, "meaning_zh": meaning, "definition_en": "A compatibility fixture.",
            "occurrences": [{"paragraph": 1, "sentence": number, "start": start, "end": start + len(surface), "surface": surface}],
        })
        if study:
            paragraph["vocabulary"].append({
                "lexical_id": lid, "surface": surface, "meaning_zh": meaning,
                "note_zh": "格式叠加时仍保留空格、原文标点和可用的词汇链接。",
            })
    title = "English punctuation and italic words"
    subtitle = "The template keeps Indonesia’s quotes"
    heading = "Quotes, links and formatting"
    return {
        "schema_version": "june-english-core-read-study-note-v1", "language": "en",
        "title": title, "title_origin": "source", "title_zh": "英文标点与原文斜体兼容性核验",
        "title_inline_runs": marked_runs(title, "italic words"),
        "subtitle": subtitle, "subtitle_zh": "模板保留原文引号",
        "subtitle_inline_runs": marked_runs(subtitle, "Indonesia’s"),
        "source": {"name": "Template verification", "published_date": None, "url": "https://example.com/a_b?x=1&title=quote%20test#s1"},
        "audio": {"url": "https://example.com/audio_sample.mp3"},
        "is_complete_article": True, "sentence_analysis_depth": 3, "cefr": {"estimated_reading_level": "B2"},
        "intro_note": {
            "summary_zh": "检查英文撇号、单双弯引号、直引号和全角引号的区别，保留原字符。",
            "structure_zh": "原文、中文译文、重点句解析和右侧词汇笔记共同使用正式模板。",
            "writing_features_zh": "覆盖连续下划线、自动换行、颜色、链接、标题斜体、音标与中文粗体。",
        },
        "body": [
            {"type": "heading", "level": 1, "text": heading, "inline_runs": marked_runs(heading, "formatting"), "translation_zh": "引号、链接与格式"},
            paragraph,
        ],
        "Vocabularies": {"entries": entries},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_tex")
    parser.add_argument("--cefr-chart")
    args = parser.parse_args()
    print(write_latex(smoke_data(), args.output_tex, args.cefr_chart))


if __name__ == "__main__":
    main()
