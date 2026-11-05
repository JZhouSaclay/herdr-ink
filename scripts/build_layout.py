"""Build a personal layout from the locally shipped Herdr 0.1.13 modules.
Only writes inside this project. Never installs or selects a layout.
"""
from pathlib import Path
import json, shutil
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Users/jiezhou/.config/herdr-app')
ART='mods/ink-chrome/art/'

def replace(text, old, new):
    if old not in text: raise RuntimeError('Shipped source changed; missing anchor: '+old[:100])
    return text.replace(old,new)

def save(name,text):
    # Use the user's actual brush scan and photographic bamboo in the final build.
    text=text.replace('stroke-v2.png','stroke-v3.png').replace('bamboo-v2.png','bamboo-v3.png')
    text=text.replace('svg("mods/ink-chrome/art/ink-ring-v2.svg")','image("mods/ink-chrome/art/ink-ring-v3.png")')
    if name in ('ink-spaces','ink-agents'):
        text=text.replace('image("mods/ink-chrome/art/stroke-v3.png")', 'image(i % 2 ? "mods/ink-chrome/art/stroke-alt-v3.png" : "mods/ink-chrome/art/stroke-v3.png")')
    if name == 'ink-spaces':
        text=replace(text,'.opacity(on ? 0.38 : this.hoveredSpace === w.id ? 0.24 : 0.12)', '.opacity(0.10))\n      .child(image("mods/ink-chrome/art/row-frame-v4.png").absolute().inset(0).size_full().opacity(on ? 0.66 : this.hoveredSpace === w.id ? 0.28 : 0)')
    if name == 'ink-agents':
        text=replace(text,'.opacity(a.focused ? 0.38 : this.hovered === a.address ? 0.24 : 0.12)', '.opacity(0.10))\n        .child(image("mods/ink-chrome/art/row-frame-v4.png").absolute().inset(0).size_full().opacity(a.focused ? 0.66 : this.hovered === a.address ? 0.28 : 0)')
    if name == 'ink-tabs':
        text=replace(text,'.h(38).px(18).gap(9)', '.h(34).px(12).gap(6)')
        text=replace(text,'.max_w(170)', '.max_w(128).tooltip(name)')
        text=replace(text,'.size(22)', '.size(18)')
        text=text.replace('bamboo-v3.png','bamboo-v4.png')
    if name in ('ink-spaces','ink-agents'):
        namespace = 'space' if name == 'ink-spaces' else 'agent'
        text='import { CraneMotion } from "./crane.js";\n'+text
        text=replace(text,'  init(_props, cx) {', '  init(_props, cx) {\n    this.craneMotion = new CraneMotion("'+namespace+'");')
        selected = 'spaces().find(s => s.active)?.id' if name == 'ink-spaces' else 'agents().find(a => a.focused)?.address'
        text=replace(text,'    const collapsed = narrow();', '    const collapsed = narrow();\n    this.craneMotion.observe(collapsed ? null : ('+selected+' ?? null));')
        last=text.rfind('\n}')
        text=text[:last]+'\n  close() { this.craneMotion.cancel(); }\n'+text[last:]
    if name == 'ink-spaces':
        text=replace(text,'.id(`space-${w.id}`)\n      .px(8)', '.id(`space-${w.id}`)\n      .pl(8).pr(44)')
        text=replace(text,'.opacity(on ? 0.66 : this.hoveredSpace === w.id ? 0.28 : 0))', '.opacity(on ? 0.66 : this.hoveredSpace === w.id ? 0.28 : 0))\n      .child(this.craneMotion.render(w.id))')
    if name == 'ink-agents':
        text=replace(text,'.id(`ag-${a.address}`)\n        .relative()\n        .px(10)', '.id(`ag-${a.address}`)\n        .relative()\n        .pl(10).pr(46)')
        text=replace(text,'.opacity(a.focused ? 0.66 : this.hovered === a.address ? 0.28 : 0))', '.opacity(a.focused ? 0.66 : this.hovered === a.address ? 0.28 : 0))\n        .child(this.craneMotion.render(a.address))')
    folder=ROOT/'mods'/name;folder.mkdir(parents=True,exist_ok=True)
    (folder/'main.js').write_text(text)
    if name in ('ink-spaces','ink-agents'):
        shutil.copy2(ROOT/'scripts/crane-motion.js',folder/'crane.js')
    (folder/'mod.json').write_text(json.dumps({'place':'none','title':name,'cloned_from':{'name':name.removeprefix('ink-') if name != 'ink-chrome' else 'workspace-chrome','version':'0.1.13'}},indent=2)+'\n')

# Keep the shipped navigation, reordering, remote machines, git and sub-agent behavior.
s=(SOURCE/'mods/spaces/main.js').read_text()
s=replace(s,'{ View, div, svg }','{ View, div, svg, image }')
s=replace(s,'(tree ? 28 : 30)','(tree ? 32 : 44)')
s=replace(s,'.when(on, (el) => el.bg(t.selected))','.when(on, (el) => el.child(image("'+ART+'wash-v1.png").absolute().inset(0).size_full()))')
s=replace(s,'.rounded(8)','.rounded(0)')
s=replace(s,'h_flex()\n          .gap(9)','h_flex()\n          .relative()\n          .gap(9)')
s=replace(s,'.when(!tree, el => el.child(h_flex().size(18).flex_none().rounded(5).bg(fill).items_center().justify_center().text_size(10.5).font_bold().text_color("#ffffff").child([...w.name][0]?.toUpperCase() ?? "?")))','.when(!tree, el => el.child(div().w(20).flex_none().text_size(11).text_color(t.dim).child(String(i + 1).padStart(2,"0"))))')
s=replace(s,'.child("Spaces")','.child("工作区")')
s=replace(s,'.h(31).pl(16)','.h(42).pl(16)')
# Drop unused avatar color bookkeeping, which would write global shared state just for decoration.
start=s.index('    const palette = [',s.index('  render()'))
end=s.index('    return v_flex()',start)
s=s[:start]+s[end:]
s=replace(s,'    const colors = shared("space.colors") ?? {};\n    const color = colors[w.id] ?? "ansi6";\n    const fill = color.startsWith("#") ? color : (MARK[color] ?? t[color]);\n','')
# V2: every row carries one pressed stroke, with explicit hover/selection ink levels.
s=replace(s,'  init(_props, cx) {','  init(_props, cx) {\n    this.hoveredSpace = null;')
s=replace(s,'.when(on, (el) => el.child(image("'+ART+'wash-v1.png").absolute().inset(0).size_full()))', '.child(image("'+ART+'stroke-v2.png").absolute().inset(0).size_full().opacity(on ? 0.38 : this.hoveredSpace === w.id ? 0.24 : 0.12))')
s=replace(s,'.when(!on, (el) => el.hover((s) => s.bg(t.hover)))', '.on_hover((over, cx) => { this.hoveredSpace = over ? w.id : this.hoveredSpace === w.id ? null : this.hoveredSpace; cx.notify(); })')
save('ink-spaces',s)

s=(SOURCE/'mods/agents/main.js').read_text()
s=replace(s,'const pic = icon(a.program, 16, t.foreground);','const pic = null;')
s=replace(s,'.id(`ag-${a.address}`)\n        .px(8)','.id(`ag-${a.address}`)\n        .relative()\n        .px(10)')
s=replace(s,'.h(30)\n        .flex_none()\n        .rounded(8)','.h(44)\n        .flex_none()\n        .rounded(0)')
s=replace(s,'.when(a.focused, (el) => el.bg(t.selected))','.when(a.focused, (el) => el.child(image("'+ART+'agent-wash-v1.png").absolute().inset(0).size_full()))')
s=replace(s,'.child(h_flex().flex_1().min_w(0).gap(5).items_center()','.child(h_flex().relative().flex_1().min_w(0).gap(5).items_center()')
s=replace(s,'"Needs you"','"待确认"')
s=replace(s,'"Done"','"已完成"')
s=replace(s,'"Working"','"进行中"')
s=replace(s,'"Idle"','"空闲"')
s=replace(s,'.child("Agents")','.child("Agents · 协作")')
s=replace(s,'.child("!")','.child("待")')
s=replace(s,'.rounded(4).bg(t.blocked + "26")','.rounded(1).bg(t.blocked + "16").border(1).border_color(t.blocked + "77")')
s=replace(s,'.rounded(5).bg(t.blocked + "26")','.rounded(1).bg(t.blocked + "16")')
s=replace(s,'No agent status yet. Agents show up here when they report their status. Older versions and agents inside tmux may not.','尚无 Agent 状态。Agent 上报状态后会出现在这里。')
s=replace(s,'openOverlay({ mod: "agents",','openOverlay({ mod: "ink-agents",')
# V2: remove redundant status headings and words; keep priority sorting and tooltips.
s=replace(s,'.when(a.focused, (el) => el.child(image("'+ART+'agent-wash-v1.png").absolute().inset(0).size_full()))', '.child(image("'+ART+'stroke-v2.png").absolute().inset(0).size_full().opacity(a.focused ? 0.38 : this.hovered === a.address ? 0.24 : 0.12))')
s=replace(s,'.cursor_pointer()\n        .hover((s) => s.bg(t.hover))\n        .on_hover', '.cursor_pointer()\n        .on_hover')
start=s.index('  status(t, a, compact = false) {')
end=s.index('  render(cx) {',start)
s=s[:start]+'''  status(t, a, compact = false) {
    if (a.status === "working") return svg("mods/ink-chrome/art/ink-ring-v2.svg").size(15).flex_none().text_color(t.working).spin(1600).tooltip("进行中");
    if (a.status === "blocked") return div().size(17).flex_none().rounded(1).border(1).border_color(t.blocked + "88").bg(t.blocked + "12").text_color(t.blocked).text_size(11).flex().items_center().justify_center().tooltip("待确认").child("待");
    if (a.status === "done") return svg("mods/ink-chrome/art/check-v2.svg").size(15).flex_none().text_color(t.done).tooltip("已完成");
    return div().size(7).mx(4).flex_none().rounded(4).border(1).border_color(t.dim).tooltip("空闲");
  }

'''+s[end:]
s=replace(s,'const rows = collapsed\n      ? list.flatMap(withKids)', 'const rows = collapsed || byPriority\n      ? list.flatMap(withKids)')
s=replace(s,'.px(collapsed ? 0 : 8).overflow_y_scrollbar()', '.px(collapsed ? 0 : 8).pt(8).gap(6).overflow_y_scrollbar()')
save('ink-agents',s)

s=(SOURCE/'mods/tabs/main.js').read_text()
s=replace(s,'  init() {\n    this.pressed = null;','  init() {\n    this.hovered = null;\n    this.pressed = null;')
s=replace(s,'h_flex().id(`tab-${c.id}`).h(29).px(10).gap(7).rounded(7)', 'h_flex().id(`tab-${c.id}`).relative().h(42).px(14).gap(9).rounded(0)')
s=replace(s,'.border(1).border_color(c.active ? t.border : t.chrome).bg(c.active ? t.raised : t.chrome).text_color(c.active ? t.foreground : t.muted)', '.text_color(c.active ? t.foreground : t.muted)\n        .when(c.active, el => el.child(image("'+ART+'ticket-v1.png").absolute().inset(0).size_full()))\n        .on_hover((on,cx) => { this.hovered = on ? c.id : this.hovered === c.id ? null : this.hovered; cx.notify(); })')
s=replace(s,'.when(Boolean(program?.icon), el => el.child(program.tint ? svg(program.icon).size(14).text_color(t.muted) : image(program.icon).size(14)))', '.child(div().relative().text_size(10).text_color(t.dim).child(String(i + 1).padStart(2, "0")))')
s=replace(s,'.child(div().max_w(170).truncate()', '.child(div().relative().max_w(170).truncate()')
s=replace(s,'.when(c.active, el => el.child(div().id(`close-${c.id}`)', '.when(c.active, el => el.child(image("'+ART+'underline-v1.png").absolute().left(8).right(8).bottom(0).h(4).w_full()))\n        .child(div().relative().id(`close-${c.id}`).size(22).flex_none().flex().items_center().justify_center().tooltip("关闭标签").opacity(c.active || this.hovered === c.id ? 1 : 0)')
s=replace(s,'.child(svg("mods/pane/close.svg").size(12))));','.child(svg("mods/pane/close.svg").size(12)));')
s=replace(s,'run("tab.close", { id: c.id });','run(c.active || this.hovered === c.id ? "tab.close" : "tab.select", { id: c.id });')
s=replace(s,'.h(26).px(8).gap(5).flex_none().items_center().rounded(6)', '.h(32).px(10).gap(6).flex_none().items_center().rounded(1)')
s=replace(s,'.size(26).flex_none()', '.size(30).flex_none().tooltip(id === "tab-new" ? "新建标签" : id)')
s=replace(s,'panelButton("files", "Files",','panelButton("files", "文件",')
s=replace(s,'panelButton("changes", "Changes",','panelButton("changes", "变更",')
s=replace(s,'.px(10).pl(lightsPadding).gap(3)', '.px(16).pl(lightsPadding).gap(6)')
# V2: a single horizontal bamboo slip for every tab, independent of active state.
s=replace(s,'.h(42).px(14).gap(9)', '.h(38).px(18).gap(9)')
s=replace(s,'.when(c.active, el => el.child(image("'+ART+'ticket-v1.png").absolute().inset(0).size_full()))', '.child(image("'+ART+'bamboo-v2.png").absolute().inset(0).size_full().opacity(c.active ? 1 : this.hovered === c.id ? 0.85 : 0.52))')
s=replace(s,'.when(c.active, el => el.child(image("'+ART+'underline-v1.png").absolute().left(8).right(8).bottom(0).h(4).w_full()))', '.when(c.active, el => el.child(image("'+ART+'stroke-v2.png").absolute().left(18).right(18).bottom(1).h(4).opacity(0.7)))')
s=replace(s,'svg("mods/workspace-chrome/spinner.svg")', 'svg("mods/ink-chrome/art/ink-ring-v2.svg")')
s=replace(s,'.spin(900)', '.spin(1600)')
s=replace(s,'.when(c.status === "blocked" || c.status === "done", el => el.child(div().size(6).rounded(3).bg(t[c.status])))', '.when(c.status === "blocked", el => el.child(div().size(15).flex_none().border(1).border_color(t.blocked + "88").text_size(10).text_color(t.blocked).flex().items_center().justify_center().tooltip("待确认").child("待")))\n        .when(c.status === "done", el => el.child(svg("mods/ink-chrome/art/check-v2.svg").size(13).flex_none().text_color(t.done).tooltip("已完成")))')
save('ink-tabs',s)

s=(SOURCE/'mods/pane/main.js').read_text()
s=replace(s,'const pic = icon(p.program, 14, t.dim);','const pic = null;')
s=replace(s,'.bg(t.background)','.bg(t.background + "b8")')
s=replace(s,'.child("Needs you")','.child("待确认")')
s=replace(s,'.rounded(5).bg(t.blocked + "26")','.rounded(1).bg(t.blocked + "16")')
s=replace(s,'svg("mods/workspace-chrome/spinner.svg")', 'svg("mods/ink-chrome/art/ink-ring-v2.svg")')
s=replace(s,'.spin(900)', '.spin(1600)')
s=replace(s,'.when(st === "blocked", el => el.child(div().flex_none().px(6).h(18).flex().items_center().rounded(1).bg(t.blocked + "16").text_size(10.5).font_semibold().text_color(t.blocked).child("待确认")))', '.when(st === "blocked", el => el.child(div().size(17).flex_none().flex().items_center().justify_center().rounded(1).border(1).border_color(t.blocked + "88").text_size(11).text_color(t.blocked).tooltip("待确认").child("待")))')
s=replace(s,'.when(st === "done", el => el.child(div().size(7).flex_none().rounded(4).bg(t.done)))', '.when(st === "done", el => el.child(svg("mods/ink-chrome/art/check-v2.svg").size(14).flex_none().text_color(t.done).tooltip("已完成")))')
save('ink-pane',s)

s=(SOURCE/'mods/workspace-chrome/main.js').read_text()
s=replace(s,'.child(image("frame/welcome/herdr.png").size(20).rounded(5)).child(div().font_semibold().text_color(t.foreground).child("Herdr"))','.child(div().font_family("Songti SC").text_size(17).text_color(t.foreground).child("水墨书斋"))')
s=replace(s,'"Settings"','"设置"')
s=replace(s,'"Add machine"','"添加机器"')
s=replace(s,'.rounded(8)','.rounded(0)')
save('ink-chrome',s)

layout=json.loads((SOURCE/'layouts/main.json').read_text())
mods={'spaces':'ink-spaces','agents':'ink-agents','tabs':'ink-tabs','pane':'ink-pane','workspace-chrome':'ink-chrome'}
def walk(node):
    yield node
    for c in node.get('children',[]):yield from walk(c)
for n in walk(layout):
    content=n.get('content',{})
    if content.get('mod') in mods:content['mod']=mods[content['mod']]
    if n['id']=='sidebar':n['size']={'px':264};n['min']=76
    if n['id']=='brand':n['size']={'px':56}
    if n['id']=='tabs':n['size']={'px':60}
    if n['id']=='work-body':
        n['background']={'image':ART+'landscape-v2.png','fit':'cover'}
        n['padding']=[8,12]
    if n['id']=='main':
        p=content['pane'];p['radius']=0;p['background']='#fcfcf900';p['border']['color']='#cecfc580';p['focus']['color']='#879086';p['header']['content']['mod']='ink-pane';p['header']['height']=30
layout.update({'theme':'ink-study','ui_font':'Geist','font':'JetBrains Mono','font_size':14,'terminal_opacity':0.24,'terminal_padding':[18,18],'preview':'layouts/ink-study.png','cloned_from':{'name':'main','version':'0.1.13'}})
(ROOT/'layouts/ink-study.json').write_text(json.dumps(layout,indent=2,ensure_ascii=False)+'\n')
colors={'background':'#FCFCF9','foreground':'#303632','canvas':'#FCFCF9','chrome':'#F8FAF8','surface':'#FCFCF9','raised':'#FFFFFF','popover':'#FFFFFF','border':'#E2E7E3','accent':'#496B65','muted':'#58645D','dim':'#606B64','selected':'#E0E9E3','hover':'#EBF0EC','input':'#D2DDD5','working':'#496B65','blocked':'#A64B3C','done':'#526746','idle':'#606B64','unknown':'#606B64','solid':'#496B65'}
ansi=['#303632','#A04437','#4E633F','#80642C','#3F6278','#755975','#3E6C68','#62695F','#6B7168','#A04437','#4E633F','#80642C','#3F6278','#755975','#3E6C68','#303632']
theme={'background':colors['background'],'foreground':colors['foreground'],'selection':'#D7DFD1','cursor':'#526B70','ansi':ansi,'colors':colors}
(ROOT/'themes/ink-study.json').write_text(json.dumps(theme,indent=2)+'\n')
print('Built layout and five mods in',ROOT)
