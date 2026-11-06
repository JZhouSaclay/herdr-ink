#!/usr/bin/env python3
"""Validate or restore the complete Ink Study v18/v17 UI, including pretty-tui.
Default is a dry run. Existing session data and unrelated files are preserved.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, shutil, tempfile, zipfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--version',choices=['ink-study-v18','ink-study-v17','ink-study-v18-cursor','ink-cursor-particles-v1','ink-cursor-particles-v2','ink-cursor-particles-v3','ink-cursor-particles-v4'])
    parser.add_argument('--home',type=Path,default=Path.home()/'.config/herdr-app')
    parser.add_argument('--extension-dir',type=Path,default=Path.home()/'.pi/agent/extensions/pretty-tui')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();home=args.home.expanduser().resolve();extension=args.extension_dir.expanduser().resolve()
    with zipfile.ZipFile(args.archive) as archive,tempfile.TemporaryDirectory(prefix='ink-restore-') as tmp:
        if archive.testzip() is not None:raise SystemExit('Archive CRC check failed')
        metadata=next(name for name in ['checkpoint-cursor-particles.json','checkpoint-cursor.json','checkpoint-v18.json'] if name in archive.namelist())
        manifest=json.loads(archive.read(metadata))
        args.version=args.version or manifest.get('default_version','ink-study-v18')
        version=manifest['versions'][args.version]
        staged=[]
        for group,root,entries in [('herdr',home,version['runtime']),('pretty-tui',extension,version['extension'])]:
            for relative,entry in entries.items():
                path=Path(relative)
                if path.is_absolute() or '..' in path.parts:raise SystemExit(f'Unsafe target: {relative}')
                if group=='herdr' and not (relative.startswith('mods/ink-') or relative in ['layouts/ink-study.json','themes/ink-study.json']):
                    raise SystemExit(f'Unexpected runtime target: {relative}')
                if group=='pretty-tui' and not (path.suffix in ['.ts','.js','.json','.png','.svg','.md'] or path.name=='LICENSE'):
                    raise SystemExit(f'Unexpected extension target: {relative}')
                target=root/path
                if not target.resolve().is_relative_to(root):raise SystemExit(f'Symlink escapes destination: {target}')
                data=archive.read(entry['source'])
                if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise SystemExit(f'Hash mismatch: {relative}')
                staging=Path(tmp)/group/path;staging.parent.mkdir(parents=True,exist_ok=True);staging.write_bytes(data)
                staged.append((group,relative,staging,target,entry['sha256']))
        print(f'Validated {len(staged)} files for {args.version}')
        print(f'Herdr: {home}\nPretty TUI: {extension}')
        if not args.apply:
            print('Dry run: no destination files changed. Add --apply to restore.');return
        stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup=home/'backups'/f'before-{args.version}-restore-{stamp}.zip';backup.parent.mkdir(parents=True,exist_ok=True)
        absent=[]
        with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as saved:
            for group,name,_,target,_ in staged:
                if target.is_file():saved.write(target,f'{group}/{name}')
                elif target.exists():raise SystemExit(f'Destination is not a file: {target}')
                else:absent.append(f'{group}/{name}')
            saved.writestr('backup-info.json',json.dumps({'herdr':str(home),'pretty_tui':str(extension),'previously_absent':absent},indent=2))
        # Install art and helpers first, entries last. Keep existing symlink files intact.
        for group,name,source,target,_ in sorted(staged,key=lambda item:(Path(item[1]).name in ['main.js','index.ts'],item[1])):
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        for _,name,_,target,digest in staged:
            if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise SystemExit(f'Restored verification failed: {name}; backup: {backup}')
        print(f'Restored and verified {len(staged)} files. Previous files: {backup}')
        print('Herdr updates live. Reload each Pi session you want to update using /reload when idle.')
        print('Sessions, terminals, settings, shared state and unrelated files were preserved.')


if __name__=='__main__':main()
