import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import warnings

from PIL import Image, ImageOps
import pymupdf


MAX_SOURCE_BYTES = 128 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_RENDER_EDGE = 2400
MAX_CACHE_BYTES = 128 * 1024 * 1024
CACHE_AGE_SECONDS = 7 * 24 * 60 * 60
CACHE_VERSION = 1
REMOTE_CHUNK_BYTES = 32 * 1024
REMOTE_BATCH_CHUNKS = 4
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
warnings.simplefilter("error", Image.DecompressionBombWarning)


def signature(source):
    stat = source.stat()
    if not source.is_file():
        raise ValueError("This path is not a file")
    if stat.st_size > MAX_SOURCE_BYTES:
        raise ValueError("Preview is limited to files smaller than 128 MiB")
    return [str(source), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]


def render_document(source, page_number, kind):
    with pymupdf.open(source) as document:
        if document.needs_pass:
            raise ValueError("This PDF is password protected")
        if kind == "pdf" and not document.is_pdf:
            raise ValueError("This file is not a valid PDF")
        pages = document.page_count
        if not 1 <= page_number <= pages:
            raise ValueError(f"Page must be between 1 and {pages}")
        page = document.load_page(page_number - 1)
        width, height = page.rect.width, page.rect.height
        if not all(math.isfinite(value) and value > 0 for value in (width, height)):
            raise ValueError("This page has invalid dimensions")
        scale = min(3, MAX_RENDER_EDGE / max(width, height))
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(scale, scale),
            colorspace=pymupdf.csRGB,
            alpha=kind != "pdf",
        )
        return pixmap.tobytes("png"), {
            "width": pixmap.width,
            "height": pixmap.height,
            "pages": pages,
            "page": page_number,
            "kind": kind,
        }


def render_image(source):
    with Image.open(source) as original:
        if original.width * original.height > MAX_IMAGE_PIXELS:
            raise ValueError("Preview is limited to images of 40 megapixels")
        oriented = ImageOps.exif_transpose(original)
        width, height = oriented.size
        oriented.thumbnail((MAX_RENDER_EDGE, MAX_RENDER_EDGE), Image.Resampling.LANCZOS)
        preview = oriented.convert("RGBA")
        output = io.BytesIO()
        preview.save(output, format="PNG")
        return output.getvalue(), {
            "width": preview.width,
            "height": preview.height,
            "sourceWidth": width,
            "sourceHeight": height,
            "pages": 1,
            "page": 1,
            "kind": "image",
        }


def atomic_write(path, data):
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.part")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def prune_cache(cache, keep):
    entries = sorted(
        ((entry.stat().st_mtime, entry.stat().st_size, entry)
         for entry in cache.iterdir() if entry.is_file() and not entry.name.startswith(".")),
        reverse=True,
    )
    used = 0
    cutoff = time.time() - CACHE_AGE_SECONDS
    for modified, size, entry in entries:
        used += size
        if entry not in keep and (modified < cutoff or used > MAX_CACHE_BYTES):
            entry.unlink(missing_ok=True)


def remote_exec(hc, machine, reader, *args, timeout=15):
    try:
        completed = subprocess.run(
            [hc, "exec", "--json", "--on", machine, "--timeout", str(timeout - 2), "--",
             "python3", "-c", reader, *[str(arg) for arg in args]],
            capture_output=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise ValueError("Remote preview transfer timed out; retry to continue downloading") from None
    if completed.returncode != 0:
        raise ValueError(completed.stderr.decode("utf-8", errors="replace").strip()
                         or completed.stdout.decode("utf-8", errors="replace").strip()
                         or "Cannot reach the remote machine")
    result = json.loads(completed.stdout)
    if result.get("truncated") or result.get("timed_out"):
        raise ValueError("Remote preview transfer was truncated or timed out; retry the preview")
    if result["code"] != 0:
        error = base64.b64decode(result["stderr"], validate=True).decode("utf-8", errors="replace")
        raise ValueError(error.strip() or "Cannot read the remote file")
    return base64.b64decode(result["stdout"], validate=True)


def remote_source(app_home, machine, path):
    hc = shutil.which("hc")
    if hc is None:
        raise ValueError("herdr-core (hc) is not available on this Mac")
    reader = Path(__file__).with_name("remote_read.py").read_text(encoding="utf-8")
    info = json.loads(remote_exec(hc, machine, reader, path, timeout=5))
    size = info["version"][0]
    if not 0 <= size <= MAX_SOURCE_BYTES:
        raise ValueError("Preview is limited to files smaller than 128 MiB")
    identity = [machine, info["path"], info["version"]]
    digest = hashlib.sha256(json.dumps(identity).encode("utf-8")).hexdigest()
    cache = app_home / "cache" / "files-preview-sources"
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / f"{digest}{Path(path).suffix.lower()}"
    if destination.exists() and destination.stat().st_size == size:
        return destination
    chunks = [(offset, min(REMOTE_CHUNK_BYTES, size - offset), cache / f"{digest}.{offset}.chunk")
              for offset in range(0, size, REMOTE_CHUNK_BYTES)]
    missing = [(offset, length, part) for offset, length, part in chunks
               if not part.exists() or part.stat().st_size != length]

    def download(item):
        offset, length, part = item
        chunk = remote_exec(hc, machine, reader, path, json.dumps(info["version"]), offset, length)
        if len(chunk) != length:
            raise ValueError("Remote file transfer was incomplete; retry the preview")
        atomic_write(part, chunk)

    with ThreadPoolExecutor(max_workers=REMOTE_BATCH_CHUNKS) as executor:
        list(executor.map(download, missing[:REMOTE_BATCH_CHUNKS]))
    pending = [(offset, length, part) for offset, length, part in chunks
               if not part.exists() or part.stat().st_size != length]
    keep = {part for _, _, part in chunks}
    if pending:
        prune_cache(cache, keep)
        return {"pending": True, "received": size - sum(length for _, length, _ in pending), "total": size}
    if json.loads(remote_exec(hc, machine, reader, path, timeout=5)) != info:
        raise ValueError("The remote file changed while loading; retry the preview")
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.part")
    try:
        with temporary.open("wb") as output:
            for _, _, part in chunks:
                output.write(part.read_bytes())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    for _, _, part in chunks:
        part.unlink(missing_ok=True)
    prune_cache(cache, {destination})
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-home", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--machine")
    args = parser.parse_args()
    source = (remote_source(args.app_home, args.machine, str(args.source))
              if args.machine else args.source.resolve(strict=True))
    if isinstance(source, dict):
        print(json.dumps(source))
        return
    before = signature(source)
    kind = "pdf" if source.suffix.lower() == ".pdf" else "image"
    page_number = args.page if kind == "pdf" else 1
    digest = hashlib.sha256(
        json.dumps([CACHE_VERSION, before, page_number]).encode("utf-8")
    ).hexdigest()
    cache = args.app_home / "cache" / "files-preview"
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / f"{digest}.png"
    metadata = cache / f"{digest}.json"
    if destination.exists() and metadata.exists():
        result = json.loads(metadata.read_text(encoding="utf-8"))
        destination.touch()
        metadata.touch()
    else:
        if kind == "pdf" or source.suffix.lower() == ".svg":
            payload, result = render_document(source, page_number, kind)
        else:
            payload, result = render_image(source)
        if signature(source) != before:
            raise ValueError("The file changed while its preview was loading; open it again")
        result["asset"] = f"cache/files-preview/{destination.name}"
        atomic_write(destination, payload)
        atomic_write(metadata, json.dumps(result).encode("utf-8"))
    prune_cache(cache, {destination, metadata})
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"error": str(error) or type(error).__name__}))
        sys.exit(1)
