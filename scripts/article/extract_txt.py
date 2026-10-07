#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def decode_txt(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le").lstrip("\ufeff")
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be").lstrip("\ufeff")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("unsupported/unknown TXT encoding: expected UTF-8 or BOM-marked UTF-16") from exc

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("input_txt")
    ap.add_argument("output_json")
    args=ap.parse_args()
    text=decode_txt(Path(args.input_txt).read_bytes())
    Path(args.output_json).write_text(json.dumps({"text": text},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
