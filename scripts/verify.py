"""Meaningful native smoke checks, including populated and empty branches.
Checks never use real terminal data or dispatch commands to the user's window.
"""
from pathlib import Path
import subprocess, tempfile, os, shutil, re, json
ROOT=Path(__file__).resolve().parents[1]

def luminance(c):
    a=[int(c[i:i+2],16)/255 for i in (1,3,5)]
    a=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a]
    return sum(v*w for v,w in zip(a,[.2126,.7152,.0722]))
def contrast(a,b):
    lo,hi=sorted([luminance(a),luminance(b)])
    return (hi+.05)/(lo+.05)

layout=json.loads((ROOT/'layouts/ink-study.json').read_text())
ids=set()
def walk(n):
    assert n['id'] not in ids,n['id']
    ids.add(n['id'])
    for child in n.get('children',[]):walk(child)
walk(layout)
assert layout['terminal_opacity']==.24
# The art lives on the shared container, never on each individual pane.
work=next(n for n in layout['children'] if n['id']=='work')
body=next(n for n in work['children'] if n['id']=='work-body')
assert body['background']['image'].endswith('landscape-v11.png')
assert body['children'][0]['content']['pane']['background'].endswith('00')
colors=json.loads((ROOT/'themes/ink-study.json').read_text())['colors']
for role in ['foreground','muted','dim','working','blocked','done']:
    c=contrast(colors[role],colors['chrome'])
    assert c>=4.5,(role,c)

report=[]
for mod in sorted((ROOT/'mods').iterdir()):
    subprocess.run(['node','--check',str(mod/'main.js')],check=True,capture_output=True,text=True)
    env=dict(os.environ,HERDR_APP_HOME=str(ROOT))
    result=subprocess.run(['herdr-app','check',str(mod)],env=env,check=True,capture_output=True,text=True)
    report.append('PASS source / '+mod.name)
fixture=(ROOT/'.review-home/mods/ink-tabs/fixture.js').read_text()
for name,kind in [('ink-tabs','populated'),('ink-tabs','empty'),('ink-spaces','populated'),('ink-spaces','narrow'),('ink-agents','populated'),('ink-agents','subagents'),('ink-agents','empty'),('ink-agents','narrow'),('ink-agents','sort'),('ink-pane','populated'),('ink-pane','hover'),('ink-chrome','footer'),('ink-chrome','narrow')]:
    with tempfile.TemporaryDirectory(prefix='ink-study-check-') as tmp:
        home=Path(tmp);folder=home/'mods'/name
        shutil.copytree(ROOT/'mods'/name,folder)
        f=fixture
        extra={'layout','props'}
        data={'spaces','agents','panes','terminals','focused','machines','exec','hc','watchFolder','run','setAgentOrder'}|extra
        if kind=='empty':
            f=re.sub(r'export const spaces = \(\) => \[.*?\n\];','export const spaces=()=>[];',f,flags=re.S)
            f=re.sub(r'export const agents = \(\) => \[.*?\n\];','export const agents=()=>[];',f,flags=re.S)
        if kind=='subagents':
            f=f.replace('export const terminals=()=>[];', 'export const terminals=()=>[{address:"demo-child",parent:"demo-a",state:"live",status:"blocked",name:"检查任务",program:{name:"Codex",agent:true}}];')
        f+='\nexport const layout=()=>({id:"root",type:"row",children:[{id:"sidebar",size:{px:'+('76' if kind=='narrow' else '264')+'}}]});\n'
        props={'pane':'pane-a'}
        if kind=='sort':props.update(sortMenu=True,overlay='fixture')
        if kind=='footer':props.update(footer=True)
        f+='export const props=()=>('+json.dumps(props)+');\n'
        (folder/'fixture.js').write_text(f)
        def rewrite(m):
            names=[n.strip() for n in m.group(1).split(',')]
            fake=[n for n in names if n in data]; real=[n for n in names if n not in data]
            return ('import { '+', '.join(real)+' } from "herdr";\n' if real else '')+('import { '+', '.join(fake)+' } from "./fixture.js";' if fake else '')
        s=re.sub(r'import \{([^}]+)\} from "herdr";',rewrite,(folder/'main.js').read_text())
        if kind=='hover':s=s.replace('this.hovered = false','this.hovered = true')
        (folder/'main.js').write_text(s)
        env=dict(os.environ,HERDR_APP_HOME=tmp)
        subprocess.run(['herdr-app','check',str(folder)],env=env,check=True,capture_output=True,text=True)
        report.append('PASS fixture / '+name+' / '+kind)
report.append('PASS layout / unique IDs, shared art container, transparent pane frames')
report.append('PASS contrast / all six UI text roles >= 4.5:1 on sidebar paper')
events=subprocess.run(['node',str(ROOT/'scripts/check_interactions.mjs')],check=True,capture_output=True,text=True)
report.extend(events.stdout.strip().splitlines())
(ROOT/'verification.txt').write_text('\n'.join(report)+'\n')
print('\n'.join(report))
