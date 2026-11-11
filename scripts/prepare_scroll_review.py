"""Create disposable native review overlays with safe long-line fixtures."""
from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parents[1];H=Path('/Users/jiezhou/.config/herdr-app')
text='''# 书卷阅读与自动换行\n\n这是一行很长的中文说明，用来检查窄侧栏打开文件后是否可以按照窗口宽度自动折行，不需要向右滚动就能继续阅读。拖动侧栏宽度后，同一行应该重新排版，保持完整文本和原始行号。\n\nconst description = "A long code line should stay readable inside this panel, preserve selection and copying, and reflow when its width changes without changing the original file.";\n\nhttps://example.com/this/is/a/very/long/path/for/testing/responsive/preview/with/no/spaces/and/remaining/visible/to/the/end\n\nconst longToken = "abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmnopqrstuvwxyz0123456789";\n\n末尾标记：完整显示。'''
for kind in ('files','changes'):
 name='ink-scroll-review-'+kind;folder=H/'mods'/name
 assert not folder.exists(),name
 shutil.copytree(R/'mods'/('ink-'+kind),folder)
 s=(folder/'main.js').read_text();s=s.replace('const key = () => JSON.stringify(location());','const key = () => "scroll-fixture";')
 a=s.index('  init(_props, cx) {');b=s.index('\n  watch(',a)
 if kind=='files':
  init='''  init(_props, cx) {
    this.context={key:"scroll-fixture"};this.root="书卷换行验证";this.file="长行示例.md";
    this.code=EditorState.new({readonly:true,soft_wrap:true,language:"js",font_size:12,
      font_family:settings().font_family,value:TEXT});
  }
'''
  init=init.replace('TEXT',json.dumps(text,ensure_ascii=False))
 else:
  init='''  init(_props,cx) {
    this.context="scroll-fixture";this.root="书卷换行验证";this.message="";
    this.handle=cx.focus_handle();this.input=InputState.new({placeholder:"Commit message"});
    this.files=[{path:"长行示例.md",status:"M",add:4,del:1}];this.open="长行示例.md";
    this.setLines(LINES);
  }
'''
  init=init.replace('LINES',json.dumps(['@@ -1,1 +1,4 @@','-原来的短行',*['+'+line for line in text.splitlines()]],ensure_ascii=False))
 s=s[:a]+init+s[b:];(folder/'main.js').write_text(s)
 (folder/'mod.json').write_text(json.dumps({'place':'none','overlay':{'width':360,'height':760}}))
 print('Created disposable fixture',name)
