"""Native v18 review: synthetic transcript and footer; no model request."""
from pathlib import Path
import json, subprocess, datetime, uuid, time
R=Path(__file__).resolve().parents[1];D=R/'.pi-ink-review';D.mkdir(exist_ok=True)
before=json.loads(subprocess.check_output(['herdr-app','status'],text=True))
(D/'before-v18.json').write_text(json.dumps(before))
(D/'footer-v18.ts').write_text('''import type {ExtensionAPI} from "@earendil-works/pi-coding-agent";
import {truncateToWidth} from "@earendil-works/pi-tui";
export default function(pi:ExtensionAPI){pi.on("session_start",(_e,ctx)=>{ctx.ui.setFooter(()=>({
 invalidate(){},render(width:number){return [truncateToWidth("✦ 本地验收 · 🧠 high · 48k/500k (10%) · ⚡ 42 tok/s · MCP 2/2 · 微信未连接",width)];}
}));});}
''')
(D/'settings.json').write_text(json.dumps({'theme':'light','tuiMode':'fullscreen','packages':[],'defaultProvider':'fixture','defaultModel':'fixture','extensions':['/Users/jiezhou/Desktop/公司其他/pi-extension/extensions/pretty-tui/index.ts',str(D/'footer-v18.ts')]}))
(D/'pretty-tui.json').write_text(json.dumps({'enabled':True,'mode':'clean','inkStyle':True,'transcriptMarginRatio':.12}))
(D/'models.json').write_text(json.dumps({'providers':{'fixture':{'baseUrl':'http://127.0.0.1:1/v1','api':'openai-completions','apiKey':'fixture-unused','models':[{'id':'fixture','contextWindow':8192,'maxTokens':512}]}}}))
now=datetime.datetime.now(datetime.timezone.utc).isoformat();ts=int(time.time()*1000)
fixture=D/'sessions/--tmp--/fixture-v18.jsonl';fixture.parent.mkdir(parents=True,exist_ok=True)
records=[{'type':'session','version':3,'id':str(uuid.uuid4()),'timestamp':now,'cwd':'/tmp'},
{'type':'message','id':'11111111','parentId':None,'timestamp':now,'message':{'role':'user','content':'请留出更多阅读空间，细节保持淡雅的水墨风格。','timestamp':ts}},
{'type':'message','id':'22222222','parentId':'11111111','timestamp':now,'message':{'role':'assistant','content':[{'type':'text','text':'竹影疏处，留白有声。\n\n顶部路径收进悬停栏，底部常驻信息移入侧栏，对话区域多出 58 像素。\n\n输入框下方保留原有状态文字，小图标改为书卷、风叶与墨星。左上淡竹与右下山水相映，正文和输入保持清晰。\n\n```text\n│iiiiiiiiii│MMMMMMMMMM│1234567890│\n│中文对齐测│宋体与文楷│等宽列测试│\n```\n\n以上为固定本地样例，不发送模型请求。'}],'api':'openai-completions','provider':'fixture','model':'fixture','stopReason':'stop','timestamp':ts,'usage':{'input':0,'output':0,'cacheRead':0,'cacheWrite':0,'totalTokens':0,'cost':{'input':0,'output':0,'cacheRead':0,'cacheWrite':0,'total':0}}}}]
fixture.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in records))
args={'name':'墨色细节验收','space':before['space'],'folder':'/tmp','argv':['env','PI_CODING_AGENT_DIR='+str(D),'pi','--session',str(fixture),'--no-skills','--no-prompt-templates']}
created=json.loads(subprocess.check_output(['herdr-app','do','tab.new',json.dumps(args,ensure_ascii=False)],text=True))
(D/'created-v18.json').write_text(json.dumps(created));print(json.dumps(created))
