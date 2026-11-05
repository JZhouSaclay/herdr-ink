"""Open only a synthetic local Pi transcript; never send a model request."""
from pathlib import Path
import json,subprocess,datetime,time,uuid
R=Path(__file__).resolve().parents[1];D=R/'.pi-ink-review';D.mkdir(exist_ok=True)
old=json.loads(subprocess.check_output(['herdr-app','status'],text=True));(D/'before.json').write_text(json.dumps(old))
(D/'settings.json').write_text(json.dumps({'theme':'light','tuiMode':'fullscreen','packages':[],'defaultProvider':'fixture','defaultModel':'fixture','extensions':['/Users/jiezhou/Desktop/公司其他/pi-extension/extensions/pretty-tui/index.ts']})+'\n')
(D/'pretty-tui.json').write_text(json.dumps({'enabled':True,'mode':'clean','inkStyle':True,'transcriptMarginRatio':.12})+'\n')
(D/'models.json').write_text(json.dumps({'providers':{'fixture':{'baseUrl':'http://127.0.0.1:1/v1','api':'openai-completions','apiKey':'fixture-unused','models':[{'id':'fixture','contextWindow':8192,'maxTokens':512}]}}})+'\n')
now=datetime.datetime.now(datetime.timezone.utc).isoformat();fixture=D/'fixture.jsonl'
records=[{'type':'session','version':3,'id':str(uuid.uuid4()),'timestamp':now,'cwd':'/tmp'}, {'type':'message','id':'11111111','parentId':None,'timestamp':now,'message':{'role':'user','content':'宣纸气泡与水墨输入框\n这是一条本地固定样例，不会发送模型请求。','timestamp':int(time.time()*1000)}}]
records.append({'type':'message','id':'22222222','parentId':'11111111','timestamp':now,'message':{'role':'assistant','content':[{'type':'text','text':'本地固定样例：检查气泡底色、输入框笔触和文字对齐。\n\n```text\n│iiiiiiiiii│MMMMMMMMMM│1234567890│\n│..........│..........│..........│\n│中文对齐测│宋体与文楷│等宽列测试│\n```'}],'api':'openai-completions','provider':'fixture','model':'fixture','stopReason':'stop','timestamp':int(time.time()*1000),'usage':{'input':0,'output':0,'cacheRead':0,'cacheWrite':0,'totalTokens':0,'cost':{'input':0,'output':0,'cacheRead':0,'cacheWrite':0,'total':0}}}})
fixture.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in records))
args={'name':'墨色验收','space':old['space'],'folder':'/tmp','argv':['env','PI_CODING_AGENT_DIR='+str(D),'pi','--session',str(fixture),'--no-skills','--no-prompt-templates']}
v=json.loads(subprocess.check_output(['herdr-app','do','tab.new',json.dumps(args,ensure_ascii=False)],text=True));(D/'created.json').write_text(json.dumps(v));print(json.dumps(v))
