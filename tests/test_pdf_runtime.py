from __future__ import annotations

import copy
from html.parser import HTMLParser
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

RENDER = Path(__file__).resolve().parents[1] / "scripts/render"
sys.path.insert(0, str(RENDER))
import compile_pdf
from build_presentation import build
from latex_assets import AssetError, ascii_pdf_bytes, prepare_project
from latex_text import esc_mixed, escurl, italic_ranges, ranges_tex
from package_latex_project import package_project
from pdf_smoke_test import smoke_data
import render_html
from render_latex import render_latex, write_latex


def pdf_bytes():
    writer = PdfWriter()
    page = writer.add_blank_page(width=100, height=80)
    stream = DecodedStreamObject()
    stream.set_data(b"0 0 10 10 re f\n%\r\nbinary-comment-\xff\n")
    page[NameObject("/Contents")] = writer._add_object(stream.flate_encode())
    writer.add_metadata({"/Title": "标点 ‘quotes’"})
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def png_bytes(color=(255, 0, 0, 128)):
    output = io.BytesIO()
    Image.new("RGBA", (3, 2), color).save(output, format="PNG")
    return output.getvalue()


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.italic = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "em":
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == "em":
            self.depth -= 1

    def handle_data(self, text):
        self.parts.append(text)
        if self.depth:
            self.italic.append(text)


class SourceProjectionTests(unittest.TestCase):
    def test_mixed_notes_keep_chinese_quotes_and_english_apostrophes(self):
        self.assertEqual(esc_mixed("‘游客’ 与 Indonesia’s plan"),
                         "‘游客’ 与 Indonesia" + r"\StudyEN{’}" + "s plan")
        data = smoke_data()
        data["body"][1]["sentences"][0]["sentence_note_zh"] = "Indonesia’s plan 是主语，‘游客’ 是中文引文。"
        self.assertIn("Indonesia" + r"\StudyEN{’}" + "s plan 是主语，‘游客’", render_latex(data))

    def test_sentence_is_one_outer_underline_with_spacing(self):
        data = smoke_data()
        block = build(data)["body"][1]
        tex = ranges_tex(block["text"], block["ranges"])
        self.assertEqual(tex.count(r"\StudySentenceUL{"), 3)
        self.assertNotIn(r"\ul{", tex)
        self.assertIn("Indonesia’s", tex)
        self.assertIn(r"\textit{italic} \textit{words}", tex)
        self.assertIn("'straight quotes'", tex)

    def test_html_source_and_italic_text_are_exact(self):
        block = build(smoke_data())["body"][1]
        parser = VisibleText()
        parser.feed(render_html.render_ranges(block["text"], block["ranges"]))
        self.assertEqual("".join(parser.parts), block["text"])
        self.assertEqual("".join(parser.italic), "italic words")

    def test_title_subtitle_and_heading_preserve_original_italics(self):
        data = smoke_data()
        with patch.object(render_html, "_font_face_css", return_value=""):
            html = render_html.render_html(data)
        self.assertIn("<em>italic words</em>", html)
        self.assertIn("<em>Indonesia’s</em>", html)
        self.assertIn("<em>formatting</em>", html)
        tex = render_latex(data)
        self.assertIn(r"\textit{formatting}", tex)

    def test_incomplete_inline_runs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "reconstruct"):
            italic_ranges("original", [{"text": "changed", "marks": ["italic"]}])

    def test_overlapping_vocabulary_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlapping vocab"):
            ranges_tex("original", [
                {"kind": "vocab", "start": 0, "end": 5, "lexical_id": "a"},
                {"kind": "vocab", "start": 3, "end": 8, "lexical_id": "b"},
            ])

    def test_rendering_never_mutates_canonical_input(self):
        data = smoke_data()
        before = copy.deepcopy(data)
        render_latex(data)
        with patch.object(render_html, "_font_face_css", return_value=""):
            render_html.render_html(data)
        self.assertEqual(data, before)

    def test_url_spaces_and_percent_escapes_remain_tex_safe(self):
        self.assertEqual(escurl("https://example.com/a b?x=1&y=a_b#s"),
                         r"https://example.com/a\%20b?x=1\&y=a\_b\#s")
        self.assertIn(r"quote\%20test\#s1", render_latex(smoke_data()))


class ProjectAssetTests(unittest.TestCase):
    def test_ascii_pdf_survives_gateway_line_normalisation(self):
        original = pdf_bytes()
        payload = ascii_pdf_bytes(original)
        self.assertTrue(payload.isascii())
        self.assertNotIn(b"\r", payload)
        transported = b"\n".join(payload.splitlines()) + b"\n"
        before = PdfReader(io.BytesIO(original), strict=True)
        after = PdfReader(io.BytesIO(transported), strict=True)
        self.assertEqual(after.metadata.title, before.metadata.title)
        self.assertEqual(after.pages[0].get_contents().get_data(),
                         before.pages[0].get_contents().get_data())
        self.assertEqual(after.pages[0].mediabox, before.pages[0].mediabox)

    def test_remote_png_is_a_decodable_pdf_with_alpha(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "chart.png").write_bytes(png_bytes())
            (root / "document.tex").write_text(r"\includegraphics{chart.png}")
            text, records = prepare_project(root / "document.tex", remote=True)
            self.assertIn("asset-001.pdf", text)
            payload = records["asset-001.pdf"]
            self.assertTrue(payload.isascii())
            page = PdfReader(io.BytesIO(payload), strict=True).pages[0]
            images = [ref.get_object() for ref in page["/Resources"]["/XObject"].values()]
            self.assertTrue(any("/SMask" in item for item in images))

    def test_nested_duplicate_filenames_package_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder, color in [("first", (255, 0, 0, 255)), ("second", (0, 0, 255, 255))]:
                (root / folder).mkdir()
                (root / folder / "same.png").write_bytes(png_bytes(color))
            tex = root / "article.tex"
            tex.write_text(r"\includegraphics{first/same.png}\includegraphics{second/same.png}")
            output = package_project(tex, root / "project.zip")
            relocated = root / "relocated"
            with zipfile.ZipFile(output) as archive:
                archive.extractall(relocated)
            text, records = prepare_project(relocated / "document.tex")
            self.assertEqual(len(records), 2)
            self.assertNotEqual(*records.values())
            self.assertNotIn("first/", text)
            self.assertNotIn("second/", text)

    def test_chart_outside_output_directory_is_copied(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            graphic = root / "中文 图表.png"
            graphic.write_bytes(png_bytes())
            output = write_latex(smoke_data(), root / "output/notes.tex", graphic)
            self.assertEqual((output.parent / "cefr_chart.png").read_bytes(), graphic.read_bytes())
            text, records = prepare_project(output)
            self.assertEqual(len(records), 1)
            self.assertIn("asset-001.png", text)

    def test_missing_asset_does_not_replace_an_existing_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tex = root / "document.tex"
            tex.write_text(r"\includegraphics{missing.png}")
            output = root / "project.zip"
            output.write_bytes(b"previous archive")
            with self.assertRaises(AssetError):
                package_project(tex, output)
            self.assertEqual(output.read_bytes(), b"previous archive")


class CompilerTests(unittest.TestCase):
    def test_first_source_error_wins_over_package_and_font_noise(self):
        text = "Package: fontspec\nPackage: soul\n" + (
            "! Package soul Error: Reconstruction failed.\n\n"
        ) + "Fontconfig warning\n" * 1000
        self.assertEqual(compile_pdf.classify_log(text), "source_error")

    def test_font_missing_with_wrapped_message_is_environmental(self):
        text = '! Package fontspec Error: The font "Fandol" cannot be\n(fontspec) found.\n\n'
        self.assertEqual(compile_pdf.classify_log(text), "environment_incompatible")

    def test_missing_package_is_environmental_but_missing_image_is_source(self):
        self.assertEqual(compile_pdf.classify_log("! LaTeX Error: File 'missing.sty' not found."),
                         "environment_incompatible")
        self.assertEqual(compile_pdf.classify_log("! LaTeX Error: File 'missing.png' not found."),
                         "source_error")

    def test_local_compilation_can_output_beside_its_tex(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tex = root / "notes.tex"
            tex.write_text(r"\documentclass{article}\begin{document}Test\end{document}")
            expected = pdf_bytes()
            def run_engine(*args, **kwargs):
                work = Path(kwargs["cwd"])
                (work / "document.pdf").write_bytes(expected)
                (work / "document.log").write_text("Output written on document.pdf")
                return SimpleNamespace(returncode=0, stdout="compiled")
            with patch.object(compile_pdf.shutil, "which", return_value="/mock/xelatex"), \
                 patch.object(compile_pdf.subprocess, "run", side_effect=run_engine):
                compile_pdf.local_compile(tex, root / "notes.pdf")
            self.assertEqual((root / "notes.pdf").read_bytes(), expected)
            self.assertFalse((root / "document.log").exists())
            self.assertFalse((root / "notes.aux").exists())

    def test_pdf_mime_with_error_body_preserves_previous_pdf_and_full_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tex = root / "notes.tex"
            tex.write_text(r"\documentclass{article}")
            output = root / "notes.pdf"
            output.write_bytes(pdf_bytes())
            before = output.read_bytes()
            log = "! Package soul Error: Reconstruction failed.\n\n" + "warning\n" * 1500
            response = SimpleNamespace(status_code=200, content=log.encode(), text=log,
                                       headers={"content-type": "application/pdf"})
            with patch.object(compile_pdf.requests, "post", return_value=response):
                with self.assertRaises(compile_pdf.CompileError) as error:
                    compile_pdf.remote_compile(tex, output)
            self.assertEqual(error.exception.kind, "source_error")
            self.assertEqual(output.read_bytes(), before)
            self.assertIn(log, (root / "notes.compile.log").read_text())

    def test_source_error_never_switches_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "notes.pdf"
            with patch.object(compile_pdf, "local_compile",
                              side_effect=compile_pdf.CompileError("source_error", "bad macro")), \
                 patch.object(compile_pdf, "remote_compile") as remote:
                with self.assertRaises(compile_pdf.CompileError):
                    compile_pdf.compile_document("unused.tex", output)
                remote.assert_not_called()

    def test_environment_failure_switches_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "notes.pdf"
            with patch.object(compile_pdf, "local_compile",
                              side_effect=compile_pdf.CompileError("environment_incompatible", "missing font")), \
                 patch.object(compile_pdf, "remote_compile",
                              return_value={"provider": "texlive_net", "log_file": "test.log"}) as remote:
                result = compile_pdf.compile_document("unused.tex", output)
                self.assertEqual(result["provider"], "texlive_net")
                remote.assert_called_once()

    def test_type_error_is_not_hidden_by_retrying_local_compilation(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(compile_pdf, "local_compile", side_effect=TypeError("programming error")), \
                 patch.object(compile_pdf, "remote_compile") as remote:
                with self.assertRaises(TypeError):
                    compile_pdf.compile_document("unused.tex", Path(directory) / "notes.pdf")
                remote.assert_not_called()


if __name__ == "__main__":
    unittest.main()
