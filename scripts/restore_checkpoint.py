#!/usr/bin/env python3
"""Validate or restore a tagged Ink Study archive. Defaults to a dry run."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--home', type=Path, default=Path.home()/'.config/herdr-app')
    parser.add_argument('--apply', action='store_true', help='Write files after validation and backup')
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    with zipfile.ZipFile(args.archive) as archive:
        if archive.testzip() is not None:
            raise SystemExit('Archive CRC validation failed')
        manifest = json.loads(archive.read('checkpoint-manifest.json'))
        files = manifest['runtime_files']
        with tempfile.TemporaryDirectory(prefix='ink-checkpoint-') as tmp:
            staging = Path(tmp)
            for name, expected in files.items():
                relative = Path(name)
                allowed = (relative.parts[0] == 'mods' and len(relative.parts) >= 3
                           and relative.parts[1].startswith('ink-')) or name in (
                               'layouts/ink-study.json', 'themes/ink-study.json')
                if relative.is_absolute() or '..' in relative.parts or not allowed:
                    raise SystemExit(f'Unsafe archive member: {name}')
                data = archive.read(name)
                if hashlib.sha256(data).hexdigest() != expected:
                    raise SystemExit(f'Hash mismatch: {name}')
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            print(f'Validated {len(files)} runtime files for {manifest["tag"]}')
            print(f'Destination: {home}')
            if not args.apply:
                print('Dry run only; pass --apply to restore. No destination files changed.')
                return
            # Refuse symlinks leading outside the chosen home.
            for name in files:
                target = home / name
                if not target.resolve().is_relative_to(home):
                    raise SystemExit(f'Destination escapes home via symlink: {target}')
            stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            backup = home / 'backups' / f'before-checkpoint-restore-{stamp}.zip'
            backup.parent.mkdir(parents=True, exist_ok=True)
            absent = []
            with zipfile.ZipFile(backup, 'w', zipfile.ZIP_DEFLATED) as saved:
                for name in files:
                    old = home / name
                    if old.is_file():
                        saved.write(old, name)
                    elif old.exists():
                        raise SystemExit(f'Destination is not a file: {old}')
                    else:
                        absent.append(name)
                saved.writestr('restore-backup-info.json', json.dumps({'previously_absent': absent}, indent=2))
            # Assets and helpers first; entry modules last to reduce transient reload errors.
            ordered = sorted(files, key=lambda name: (Path(name).name == 'main.js', name))
            for name in ordered:
                target = home / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(staging / name, target)
            for name, expected in files.items():
                if hashlib.sha256((home/name).read_bytes()).hexdigest() != expected:
                    raise SystemExit(f'Restored file verification failed: {name}. Backup: {backup}')
            print(f'Restored and verified {len(files)} files. Previous files: {backup}')
            print('Existing terminals, sessions, unrelated mods and shared state were preserved.')


if __name__ == '__main__':
    main()
