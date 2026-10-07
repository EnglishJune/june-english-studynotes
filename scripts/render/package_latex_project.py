#!/usr/bin/env python3
"""Build a relocatable project containing every generated graphics reference."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile
import zipfile

from latex_assets import prepare_project


def package_project(tex, output_zip, asset_dir=None):
    text, records = prepare_project(tex, asset_dir=asset_dir)
    output = Path(output_zip)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix="." + output.name + "-",
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("document.tex", text)
            for name, data in records.items():
                archive.writestr(name, data)
        os.replace(temporary, output)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tex")
    parser.add_argument("output_zip")
    parser.add_argument("--asset-dir")
    args = parser.parse_args()
    print(package_project(args.tex, args.output_zip, args.asset_dir))


if __name__ == "__main__":
    main()
