#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from adapters import evp_sqlite

ADAPTERS = {
    "evp_sqlite": evp_sqlite,
}


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_config(path: str | Path | None) -> tuple[dict, Path]:
    config_path = Path(path) if path else ROOT / "config" / "cefr.json"
    config = load_json(config_path)
    return config, config_path


def active_adapter(config: dict, config_path: Path):
    if not config.get("enabled"):
        raise ValueError("CEFR is disabled in config/cefr.json")
    word_cfg = config.get("word_statistics")
    if not isinstance(word_cfg, dict) or not word_cfg.get("enabled"):
        raise ValueError("CEFR word_statistics is disabled or not configured")
    name = word_cfg.get("adapter")
    if name not in ADAPTERS:
        raise ValueError(f"unsupported CEFR word-statistics adapter: {name!r}")
    asset_value = word_cfg.get("asset")
    if not isinstance(asset_value, str) or not asset_value.strip():
        raise ValueError("CEFR word_statistics.asset must be a non-empty path")
    asset = Path(asset_value)
    if not asset.is_absolute():
        asset = ROOT / asset
    return name, ADAPTERS[name], asset


def cmd_prepare(args) -> None:
    config, config_path = load_config(args.config)
    name, adapter, asset = active_adapter(config, config_path)
    article = load_json(args.article_json)
    result = adapter.prepare(article, asset)
    if result.get("adapter") != name:
        raise ValueError("adapter returned an inconsistent adapter name")
    Path(args.output_candidates).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output_candidates)


def cmd_finalize(args) -> None:
    config, config_path = load_config(args.config)
    name, adapter, _asset = active_adapter(config, config_path)
    candidates = load_json(args.candidates_json)
    if candidates.get("adapter") != name:
        raise ValueError(
            f"candidate file adapter {candidates.get('adapter')!r} does not match active adapter {name!r}"
        )
    decisions = load_json(args.decisions_json)
    result = adapter.finalize(candidates, decisions)
    Path(args.output_statistics).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output_statistics)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="CEFR config path; defaults to config/cefr.json")
    sub = ap.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare", help="prepare source-specific CEFR lookup candidates")
    prep.add_argument("article_json")
    prep.add_argument("output_candidates")
    prep.set_defaults(func=cmd_prepare)

    final = sub.add_parser("finalize", help="finalize CEFR percentages from host sense decisions")
    final.add_argument("candidates_json")
    final.add_argument("decisions_json")
    final.add_argument("output_statistics")
    final.set_defaults(func=cmd_finalize)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
