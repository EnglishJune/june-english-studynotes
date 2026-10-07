#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_FILES = [
    "Lora-Regular.ttf", "Lora-Bold.ttf", "Lora-Italic.ttf",
    "NotoSerifSC-Regular.ttf", "NotoSerifSC-Bold.ttf", "NotoSerif-Regular.ttf",
]


def load(name):
    return json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))


def check_host(host, port=443, timeout=2):
    try:
        old = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(host, port)
        socket.setdefaulttimeout(old)
        return True
    except OSError:
        return False


def check_cefr_word_statistics(config):
    result = {
        "enabled": False,
        "adapter": None,
        "asset": None,
        "asset_exists": False,
        "schema_ok": False,
        "chart_renderer_available": importlib.util.find_spec("matplotlib") is not None,
    }
    if not config.get("enabled"):
        return result
    word_cfg = config.get("word_statistics")
    if not isinstance(word_cfg, dict) or not word_cfg.get("enabled"):
        return result

    result["enabled"] = True
    result["adapter"] = word_cfg.get("adapter")
    result["asset"] = word_cfg.get("asset")
    if result["adapter"] != "evp_sqlite":
        result["error"] = f"unsupported adapter: {result['adapter']!r}"
        return result
    asset_value = result["asset"]
    if not isinstance(asset_value, str) or not asset_value.strip():
        result["error"] = "word_statistics.asset is missing"
        return result
    asset = Path(asset_value)
    if not asset.is_absolute():
        asset = ROOT / asset
    result["asset_exists"] = asset.exists()
    if not asset.exists():
        return result

    try:
        cefr_dir = ROOT / "scripts" / "cefr"
        if str(cefr_dir) not in sys.path:
            sys.path.insert(0, str(cefr_dir))
        from adapters import evp_sqlite
        asset_check = evp_sqlite.validate_asset(asset)
        result["schema_ok"] = bool(asset_check.get("schema_ok"))
        if asset_check.get("error"):
            result["error"] = asset_check["error"]
    except Exception as exc:
        result["error"] = str(exc)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-network", action="store_true")
    a = ap.parse_args()

    cefr_config = load("cefr.json")
    result = {
        "python": sys.version.split()[0],
        "packages": {},
        "xelatex": bool(shutil.which("xelatex")),
        "config": {},
        "network": {},
        "html_fonts": {},
        "cefr_word_statistics": {},
    }
    for m in ["jsonschema", "docx", "matplotlib", "requests", "fontTools", "pypdf"]:
        result["packages"][m] = importlib.util.find_spec(m) is not None
    for f in ["study.json", "cefr.json", "pdf.json", "output.json"]:
        result["config"][f] = load(f)
    result["pdf_template"] = (ROOT / "assets/templates/study_notes_preamble.tex").is_file()

    font_root = ROOT / "assets" / "fonts"
    for name in FONT_FILES:
        result["html_fonts"][name] = (font_root / name).exists()

    result["cefr_word_statistics"] = check_cefr_word_statistics(cefr_config)

    if a.check_network:
        for h in ["texlive.net", "dict.youdao.com"]:
            result["network"][h] = check_host(h)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # CEFR word statistics are degradable. A missing adapter asset or
    # matplotlib disables only the word-level chart, not the rest of the Skill.
    required = ["jsonschema", "docx", "requests", "fontTools"]
    if any(not result["packages"][x] for x in required):
        raise SystemExit(2)
    if any(not ok for ok in result["html_fonts"].values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
