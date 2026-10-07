#!/usr/bin/env python3
"""Compile the same self-contained project locally or with TeXLive.net."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import requests

from latex_assets import AssetError, prepare_project

TEXLIVE_URL = "https://texlive.net/cgi-bin/latexcgi"
FATAL_RE = re.compile(r"(?m)^! .+|^[^\n]*\.tex:\d+: .+|^xdvipdfmx:fatal:.+")


class CompileError(RuntimeError):
    def __init__(self, kind, message, log_path=None):
        super().__init__(message)
        self.kind = kind
        self.log_path = str(log_path) if log_path else None


def first_error(text):
    match = FATAL_RE.search(text)
    if match:
        return text[match.start():].split("\n\n", 1)[0]
    return text.strip()[:1000] or "Provider returned no diagnostic text."


def classify_log(text):
    error = re.sub(r"(?m)^\([^)]*\)\s*", "", first_error(text).lower())
    error = re.sub(r"\s+", " ", error)
    if "fontspec error" in error and any(x in error for x in ("cannot be found", "not found", "font-not-found")):
        return "environment_incompatible"
    if re.search(r"file\s+.+\.(sty|cls|def|otf|ttf).+not found", error):
        return "environment_incompatible"
    if FATAL_RE.search(text) or any(x in error for x in (
        "reconstruction failed", "runaway argument", "undefined control sequence",
        "missing } inserted", "extra }, or forgotten", "emergency stop",
        "png file corrupted", "file ended prematurely",
    )):
        return "source_error"
    return "unknown_error"


def save_log(path, provider, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"\n[{stamp}] {provider}\n{text}\n")
    return path


def failure(kind, text, log_file, provider):
    path = save_log(log_file, provider, text)
    return CompileError(kind, f"{first_error(text)}\nFull log: {path}", path)


def _project(tex, assets, remote):
    try:
        return prepare_project(tex, assets, remote=remote)
    except AssetError as exc:
        raise CompileError(exc.kind, str(exc)) from exc
    except (OSError, ValueError) as exc:
        raise CompileError("source_error", str(exc)) from exc


def _write_pdf(data, output):
    if not data.startswith(b"%PDF-"):
        raise CompileError("unknown_error", "Compiler did not produce a PDF signature")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix="." + output.name + "-",
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        os.replace(temporary, output)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def local_compile(tex, output, assets=(), log_file=None):
    log_file = Path(log_file or Path(output).with_suffix(".compile.log"))
    engine = shutil.which("xelatex")
    if not engine:
        raise failure("provider_unavailable", "xelatex not found", log_file, "local")
    text, records = _project(tex, assets, remote=False)
    with tempfile.TemporaryDirectory(prefix="june-xelatex-") as directory:
        work = Path(directory)
        (work / "document.tex").write_text(text, encoding="utf-8")
        for name, data in records.items():
            (work / name).write_bytes(data)
        for attempt in range(2):
            result = subprocess.run(
                [engine, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "document.tex"],
                cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            log = work / "document.log"
            complete = log.read_text(encoding="utf-8", errors="replace") if log.exists() else result.stdout
            if result.returncode:
                raise failure(classify_log(complete), complete, log_file, "local")
            save_log(log_file, f"local pass {attempt + 1}", complete)
        pdf = work / "document.pdf"
        if not pdf.is_file():
            raise failure("unknown_error", "xelatex returned success but PDF is missing", log_file, "local")
        _write_pdf(pdf.read_bytes(), output)
    return {"provider": "local", "log_file": str(log_file)}


def _remote_response(text, records, return_kind):
    files = [
        ("filename[]", (None, "document.tex")),
        ("filecontents[]", (None, text)),
    ]
    for name, data in records.items():
        files.extend([("filename[]", (None, name)), ("filecontents[]", (None, data))])
    data = {"engine": "xelatex", "return": return_kind}
    prepared = requests.Request("POST", TEXLIVE_URL, data=data, files=files).prepare()
    if len(prepared.body) > 1_000_000:
        raise CompileError("environment_incompatible", "TeXLive.net request exceeds its 1,000,000-byte limit")
    try:
        return requests.post(TEXLIVE_URL, data=data, files=files, timeout=45, allow_redirects=True)
    except requests.RequestException as exc:
        raise CompileError("provider_unavailable", str(exc)) from exc


def remote_compile(tex, output, assets=(), log_file=None, diagnostic_log=False):
    log_file = Path(log_file or Path(output).with_suffix(".compile.log"))
    text, records = _project(tex, assets, remote=True)
    try:
        response = _remote_response(text, records, "pdf")
    except CompileError as exc:
        raise failure(exc.kind, str(exc), log_file, "texlive_net") from exc
    if response.status_code >= 400:
        raise failure("provider_unavailable", f"HTTP {response.status_code}\n{response.text}",
                      log_file, "texlive_net")
    if not response.content.startswith(b"%PDF-"):
        raise failure(classify_log(response.text), response.text, log_file, "texlive_net")
    _write_pdf(response.content, output)
    result = {"provider": "texlive_net", "log_file": str(log_file)}
    if diagnostic_log:
        # The server returns either the PDF or the log, and removes the other.
        # Request the log separately only for explicit compatibility/QA runs.
        try:
            diagnostic = _remote_response(text, records, "log")
            if diagnostic.status_code >= 400 or diagnostic.content.startswith(b"%PDF-"):
                raise CompileError("provider_unavailable", "TeXLive.net did not return the requested log")
            save_log(log_file, "texlive_net diagnostics", diagnostic.text)
        except CompileError as exc:
            result["diagnostic_warning"] = str(exc)
            save_log(log_file, "texlive_net diagnostics unavailable", str(exc))
    else:
        save_log(log_file, "texlive_net", "PDF returned successfully; compile log not requested.")
    return result


def compile_document(tex, output, provider="auto", assets=(), log_file=None, diagnostic_log=False):
    order = {"auto": ["local", "texlive_net"], "local": ["local"],
             "texlive_net": ["texlive_net"]}[provider]
    attempts = []
    metadata_path = Path(output).with_suffix(".compile.json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    for name in order:
        try:
            if name == "local":
                result = local_compile(tex, output, assets, log_file)
            else:
                result = remote_compile(tex, output, assets, log_file, diagnostic_log)
            attempts.append({"provider": name, "status": "success", **result})
            metadata_path.write_text(json.dumps({"attempts": attempts}, indent=2), encoding="utf-8")
            return result
        except CompileError as exc:
            attempts.append({"provider": name, "status": exc.kind,
                             "message": str(exc), "log_file": exc.log_path})
            metadata_path.write_text(json.dumps({"attempts": attempts}, indent=2), encoding="utf-8")
            if exc.kind not in {"provider_unavailable", "environment_incompatible"} or name == order[-1]:
                raise
    raise CompileError("provider_unavailable", "no PDF provider available")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tex")
    parser.add_argument("output_pdf")
    parser.add_argument("--provider", choices=["auto", "local", "texlive_net"], default="auto")
    parser.add_argument("--asset", action="append", default=[])
    parser.add_argument("--log-file")
    parser.add_argument("--diagnostic-log", action="store_true")
    args = parser.parse_args()
    try:
        result = compile_document(args.tex, args.output_pdf, args.provider, args.asset,
                                  args.log_file, args.diagnostic_log)
    except CompileError as exc:
        parser.exit(1, f"{exc.kind}: {exc}\n")
    print(f"PDF compiled via {result['provider']}; log: {result['log_file']}")
    if result.get("diagnostic_warning"):
        print("Diagnostic warning: " + result["diagnostic_warning"])


if __name__ == "__main__":
    main()
