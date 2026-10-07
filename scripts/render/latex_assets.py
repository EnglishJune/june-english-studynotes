"""Bundle graphics and encode binary assets for TeXLive.net's text fields."""
from __future__ import annotations

import io
from pathlib import Path
import re

GRAPHIC_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
GRAPHIC_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg")


class AssetError(RuntimeError):
    def __init__(self, message, kind="source_error"):
        super().__init__(message)
        self.kind = kind


def _resolve_graphic(name, roots, supplied):
    paths = [Path(name)] if Path(name).is_absolute() else [root / name for root in roots]
    for path in paths:
        candidates = [path] if path.suffix else [path.with_suffix(ext) for ext in GRAPHIC_SUFFIXES]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
    matches = [path for path in supplied if path.name == Path(name).name]
    if len(matches) == 1 and matches[0].is_file():
        return matches[0].resolve()
    if len(matches) > 1:
        raise AssetError(f"ambiguous LaTeX asset: {name}")
    raise AssetError(f"missing LaTeX asset: {name}")


def image_pdf_bytes(data, suffix):
    try:
        from matplotlib.figure import Figure
        import matplotlib.image as mpimg
    except ImportError as exc:
        raise AssetError("matplotlib is required to transport PNG/JPEG graphics to TeXLive.net",
                         "environment_incompatible") from exc
    image = mpimg.imread(io.BytesIO(data), format="jpeg" if suffix in {".jpg", ".jpeg"} else "png")
    height, width = image.shape[:2]
    figure = Figure(figsize=(width / 72, height / 72), dpi=72, frameon=False)
    axes = figure.add_axes([0, 0, 1, 1], frameon=False)
    axes.imshow(image, interpolation="none", aspect="auto")
    axes.set_axis_off()
    output = io.BytesIO()
    figure.savefig(output, format="pdf", transparent=True)
    return output.getvalue()


def ascii_pdf_bytes(data):
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, NameObject, NullObject, StreamObject
    except ImportError as exc:
        raise AssetError("pypdf is required to transport PDF graphics to TeXLive.net",
                         "environment_incompatible") from exc
    reader = PdfReader(io.BytesIO(data), strict=True)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    # Preserve the existing filters and predictor parameters. Only add an
    # outer ASCIIHex layer; every stream remains decodable with the same data.
    for obj in writer._objects:
        if not isinstance(obj, StreamObject):
            continue
        obj._data = obj._data.hex().encode("ascii") + b">"
        old_filter = obj.get("/Filter")
        old_params = obj.get("/DecodeParms")
        filters = list(old_filter) if isinstance(old_filter, ArrayObject) else ([old_filter] if old_filter else [])
        obj[NameObject("/Filter")] = ArrayObject([NameObject("/ASCIIHexDecode"), *filters])
        if old_params is not None:
            params = list(old_params) if isinstance(old_params, ArrayObject) else [old_params]
            obj[NameObject("/DecodeParms")] = ArrayObject([NullObject(), *params])
    output = io.BytesIO()
    writer.write(output)
    # Keep the header's byte count unchanged, so the xref offsets stay valid.
    payload = output.getvalue().replace(b"%\xe2\xe3\xcf\xd3", b"%ASCI", 1)
    if not payload.isascii() or b"\r" in payload:
        raise AssetError("PDF asset could not be encoded for line-normalising text transport")
    return payload


def prepare_project(tex, assets=(), asset_dir=None, remote=False):
    tex = Path(tex).resolve()
    text = tex.read_text(encoding="utf-8-sig")
    roots = [tex.parent]
    if asset_dir:
        roots.insert(0, Path(asset_dir).resolve())
    supplied = [Path(path).resolve() for path in assets]
    records = {}
    aliases = {}
    replacements = []
    for match in GRAPHIC_RE.finditer(text):
        path = _resolve_graphic(match.group(1), roots, supplied)
        if path not in aliases:
            suffix = path.suffix.lower()
            if suffix not in GRAPHIC_SUFFIXES:
                raise AssetError(f"unsupported XeLaTeX graphic: {path.name}")
            payload = path.read_bytes()
            if remote:
                if suffix != ".pdf":
                    payload = image_pdf_bytes(payload, suffix)
                payload = ascii_pdf_bytes(payload)
                suffix = ".pdf"
            alias = f"asset-{len(aliases) + 1:03d}{suffix}"
            aliases[path] = alias
            records[alias] = payload
        replacements.append((match.start(1), match.end(1), aliases[path]))
    for start, end, alias in reversed(replacements):
        text = text[:start] + alias + text[end:]
    return text, records
