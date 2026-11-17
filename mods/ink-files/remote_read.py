import json
import os
from pathlib import Path
import stat
import sys


MAX_SOURCE_BYTES = 128 * 1024 * 1024
MAX_CHUNK_BYTES = 2 * 1024 * 1024


def version(file):
    info = os.fstat(file.fileno())
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("This path is not a regular file")
    if info.st_size > MAX_SOURCE_BYTES:
        raise ValueError("Preview is limited to files smaller than 128 MiB")
    return [info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_dev, info.st_ino]


def main():
    source = Path(sys.argv[1]).expanduser().resolve(strict=True)
    with source.open("rb") as file:
        before = version(file)
        if len(sys.argv) == 2:
            print(json.dumps({"path": str(source), "version": before}))
            return
        expected = json.loads(sys.argv[2])
        offset, length = int(sys.argv[3]), int(sys.argv[4])
        if before != expected:
            raise ValueError("The remote file changed while loading; retry the preview")
        if offset < 0 or not 0 < length <= MAX_CHUNK_BYTES or offset + length > before[0]:
            raise ValueError("Invalid preview read range")
        file.seek(offset)
        chunk = file.read(length)
        if len(chunk) != length or version(file) != before:
            raise ValueError("The remote file changed while loading; retry the preview")
        sys.stdout.buffer.write(chunk)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error) or type(error).__name__, file=sys.stderr)
        sys.exit(1)
