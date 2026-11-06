"""Round-trip both complete UI versions in a temporary home, including backups."""
from pathlib import Path
import argparse,tempfile,subprocess,json,zipfile,hashlib
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,default=R/'ink-study.zip');args=parser.parse_args()
with zipfile.ZipFile(args.archive) as archive:
 metadata='checkpoint-cursor.json' if 'checkpoint-cursor.json' in archive.namelist() else 'checkpoint-v18.json'
 manifest=json.loads(archive.read(metadata))
versions=(["ink-study-v18-cursor"] if "ink-study-v18-cursor" in manifest['versions'] else [])+['ink-study-v18','ink-study-v17']
results={}
with tempfile.TemporaryDirectory(prefix='ink-ui-restore-proof-') as tmp:
 t=Path(tmp);home=t/'herdr';ext=t/'pretty-tui';home.mkdir();ext.mkdir()
 (home/'unrelated.txt').write_text('preserve this');(ext/'unrelated.txt').write_text('preserve this too')
 (home/'layouts').mkdir();(home/'layouts/ink-study.json').write_text('old placeholder')
 for version in versions:
  subprocess.run(['python3',str(R/'scripts/restore_ui_checkpoint.py'),'--archive',str(args.archive),'--version',version,'--home',str(home),'--extension-dir',str(ext),'--apply'],check=True,capture_output=True,text=True)
  for group,root in [('runtime',home),('extension',ext)]:
   for name,entry in manifest['versions'][version][group].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==entry['sha256']
  assert (home/'unrelated.txt').read_text()=='preserve this' and (ext/'unrelated.txt').read_text()=='preserve this too'
  results[version]={'runtime':len(manifest['versions'][version]['runtime']),'extension':len(manifest['versions'][version]['extension']),'checksums_match':True,'unrelated_files_preserved':True}
  print('PASS temporary round-trip:',version)
 backups=sorted((home/'backups').glob('*.zip'),key=lambda p:p.stat().st_mtime_ns);assert len(backups)==len(versions)
 with zipfile.ZipFile(backups[0]) as saved:assert saved.read('herdr/layouts/ink-study.json')==b'old placeholder'
 with zipfile.ZipFile(backups[1]) as saved:assert hashlib.sha256(saved.read('pretty-tui/index.ts')).hexdigest()==manifest['versions'][versions[0]]['extension']['index.ts']['sha256']
print('PASS previous-version backups and unrelated-file preservation')
(R/('restore-proof-cursor.json' if 'ink-study-v18-cursor' in versions else 'restore-proof-v18.json')).write_text(json.dumps({'versions':results,'backup_verified':True},indent=2)+'\n')
