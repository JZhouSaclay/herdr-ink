"""Package the layout from source without launching/stopping Herdr or changing homes."""
from pathlib import Path
import re,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/n for n in ('README.md','RECIPE.md','ART-NOTICE.md','preview-v7.png','verification.txt','native-review.json','ink-ring-preview.gif','crane-arrival-preview-v8.gif','crane-poses-v8.png','crane-art-verification-v8.json','ring-native-proof-v9.gif','ring-native-verification-v9.json','ink-numbers-v11.png','pi-ink-native-v11.png','ink-style-native-verification-v11.json','font-source-v12.json','font-native-review-v12.json','font-native-preview-v12.png','font-spacing-v13.json','hede-native-review-v13.json','hede-native-preview-v13.png','hede-calligraphy-preview-v13.png','ink-bubble-native-v14.png','ink-bubble-native-review-v14.json')]
files += [ROOT/n for n in ('sidebar-after-v15.png','sidebar-detail-v15.png','sidebar-native-review-v15.json','space-objects-v15.png')]
files += [ROOT/n for n in ('sidebar-after-v16.png','sidebar-detail-v16.png','sidebar-native-review-v16.json','space-objects-v16.png')]
files += [ROOT/n for n in ('selection-after-v17.png','selection-sidebar-v17.png','selection-tabs-v17.png','selection-native-review-v17.json')]
files += [ROOT/n for n in ('CHECKPOINTS.md','V18-REVIEW.md','DESIGN-V18.md','checkpoint-manifest.json','checkpoint-v18.json','native-review-v18.json','restore-proof-v18.json','footer-icons-v18.png','ink-study-v18-native.png','ink-study-v18-footer.png','ink-study-v18-corner.png')]
files += [ROOT/n for n in ('CURSOR-REVIEW.md','CURSOR-DESIGN.md','checkpoint-cursor.json','cursor-native-review.json','restore-proof-cursor.json','cursor-bar-native.png','cursor-bar-detail.png','cursor-bar-typed-detail.png','cursor-reload-proof.json','cursor-reload-fixed-detail.png','cursor-position-proof.json','cursor-position-sequence-proof.json')]
files += [p for p in (ROOT/'integrations').rglob('*') if p.is_file()]
files += [ROOT/n for n in ('tab-leaf-native-v19.png','tab-leaf-detail-v19.png','tab-leaf-verification-v19.json')]
files += [ROOT/n for n in ('tab-feather-native-v22.png','tab-feather-detail-v22.png','tab-feather-verification-v22.json')]
files += [ROOT/n for n in ('tab-gpt-feather-native-v23.png','tab-gpt-feather-detail-v23.png','tab-gpt-feather-verification-v23.json')]
files += [ROOT/'scroll-wrap-comparison-v25.png',ROOT/'scroll-native-review-v25.json']
files+=list((ROOT/'layouts').glob('*'))+list((ROOT/'themes').glob('*'))
for pattern in ('*.py','*.mjs','*.js','*.json'):files+=list((ROOT/'scripts').glob(pattern))
files+=[ROOT/'reference'/n for n in ('ink-reference.png','bamboo-table.jpg','crane-ink-reference.png','Zhi-Mang-Xing-brand.ttf','zhimangxing-OFL.txt')]
# Include all runtime artwork: the v17 restoration manifest and image generators
# also need source assets which are no longer referenced by the active layout.
assets=set(p for p in (ROOT/'mods/ink-chrome/art').iterdir() if p.is_file())
for folder in (ROOT/'mods').iterdir():
    files+=[folder/'mod.json']+list(folder.glob('*.js'))+list(folder.glob('*.svg'))+list((folder/'fonts').glob('*'))
    for source in folder.glob('*.js'):
        for name in re.findall(r'mods/ink-chrome/art/([A-Za-z0-9._-]+)',source.read_text()):
            if name.endswith('-'):assets.update((ROOT/'mods/ink-chrome/art').glob(name+'*.png'))
            else:assets.add(ROOT/'mods/ink-chrome/art'/name)
def visit(n):
    bg=n.get('background')
    if isinstance(bg,dict) and 'image' in bg:assets.add(ROOT/bg['image'])
    for child in n.get('children',[]):visit(child)
visit(json.loads((ROOT/'layouts/ink-study.json').read_text()))
files+=sorted(assets)
assert all(p.is_file() for p in files)
with zipfile.ZipFile(ROOT/'ink-study.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(files)):z.write(p,p.relative_to(ROOT))
with zipfile.ZipFile(ROOT/'ink-study.zip') as z:
    assert z.testzip() is None
    names=z.namelist()
    assert len([n for n in names if n.startswith('mods/') and n.endswith('/main.js')])==8
    assert not any(n.startswith(('.review-home','data/','backups/')) or n.endswith('.d.ts') for n in names)
    assert all(f'mods/ink-chrome/art/ink-number-v11-{i}.png' in names for i in range(1,16))
    assert 'mods/ink-chrome/art/landscape-v11.png' in names
    assert 'mods/ink-chrome/art/landscape-v18.png' in names
    assert 'checkpoint-v18.json' in names
    assert 'integrations/pretty-tui-v18/ink-footer.ts' in names
    assert 'integrations/pretty-tui-v17/index.ts' in names
    assert 'mods/ink-chrome/fonts/LXGWWenKaiMono-Regular.ttf' in names
    assert 'mods/ink-chrome/fonts/OFL.txt' in names
    assert 'mods/ink-chrome/fonts/HedeInkMono-Regular.ttf' in names
    assert 'mods/ink-chrome/art/hede-calligraphy-v13.png' in names
    assert len([n for n in names if n.startswith('mods/ink-chrome/art/object-v16-') and n.endswith('.png')]) == 15
    print(f'Packaged {len(names)} files: {ROOT/"ink-study.zip"}')
