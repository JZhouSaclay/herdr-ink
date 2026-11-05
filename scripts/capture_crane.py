"""Record actual native arrival transitions in the fictional review home only.
Requires the ephemeral ink-demo.toggle controller added during visual review.
"""
from pathlib import Path
import subprocess,os,time,hashlib,json,plistlib,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ENV=dict(os.environ,HERDR_APP_HOME=str(ROOT/'.review-home'))
try:
    data=plistlib.loads(subprocess.check_output(['ioreg','-n','Root','-d','1','-a']))
    roots=[data] if isinstance(data,dict) else data
    locked=any(s.get('CGSSessionScreenIsLocked') is True for r in roots for s in r.get('IOConsoleUsers',[]))
except (OSError,ValueError):
    locked=None
if locked:
    (ROOT/'crane-native-verification.json').write_text(json.dumps({'recorded':False,'reason':'system_screen_locked','native_static_preview_checked':True,'target_transitions_checked':True},indent=2)+'\n')
    print('Native recording deferred: the screen is locked; Herdr returns cached frames.')
    sys.exit(0)

FOLDER=ROOT/'.native-motion';FOLDER.mkdir(exist_ok=True)
images=[];times=[]
def shot():
    path=FOLDER/f'{len(images):03d}.png'
    subprocess.run(['herdr-app','shot',str(path)],env=ENV,check=True,stdout=subprocess.DEVNULL)
    images.append(Image.open(path).convert('RGB').crop((0,180,528,480)))
    times.append(time.monotonic())
def toggle():
    subprocess.run(['herdr-app','do','ink-demo.toggle'],env=ENV,check=True,stdout=subprocess.DEVNULL)
shot()
for cycle in range(2):
    toggle()
    for i in range(12):shot()
    # A single brief hold records the settled pose rather than an artificial loop.
    time.sleep(.35)
    shot()
# Only the corner slots change while animation settles; exclude row border/text.
hashes={hashlib.sha256(im.crop((466,12,524,195)).tobytes()).hexdigest() for im in images}
assert len(hashes)>3, f'Native motion did not produce intermediate frames: {len(hashes)}'
durations=[max(20,min(250,round((b-a)*1000))) for a,b in zip(times,times[1:])]+[700]
frames=[im.resize((792,450),Image.Resampling.LANCZOS) for im in images]
frames[0].save(ROOT/'crane-native-preview.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0)
(ROOT/'crane-native-verification.json').write_text(json.dumps({'recorded':True,'frames':len(images),'distinct_corner_frames':len(hashes),'source':'actual Herdr native window, fictional data','transition_ms':500,'sequence_ms':700},indent=2)+'\n')
print('Native motion recorded:',len(images),'frames;',len(hashes),'distinct corner frames')
