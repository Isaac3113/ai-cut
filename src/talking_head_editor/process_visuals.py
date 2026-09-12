"""Large, frame-deterministic instructional objects. Never a product screenshot."""
from __future__ import annotations
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from .util import require, executable, atomic_json, file_hash
from .visuals import font

INK='#172F3D'; MUTED='#647B85'; BG='#F0F3F0'; TEAL='#087D79'; GOLD='#C17A14'; CORAL='#B65745'

def ease(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)

def frame(spec,t,width=1920,height=1080):
    require(width*9==height*16,'process_ratio','This authored process canvas is 16:9; author portrait separately')
    s=width/1920; im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
    def text(x,y,value,size=40,color=INK):
        d.text((x,y),value,font=font(size),fill=color,anchor='lt')
    def box(x,y,w,h,fill='white',edge=None,r=24):
        d.rounded_rectangle((x,y,x+w,y+h),r,fill=fill,outline=edge,width=2)
    def person(x,y,color=TEAL):
        d.ellipse((x,y,x+42,y+42),fill=color)
        d.rounded_rectangle((x-16,y+50,x+58,y+87),18,fill=color)
    def bubble(x,y,w=98,h=64,color=TEAL):
        d.rounded_rectangle((x,y,x+w,y+h),16,outline=color,width=5)
        d.line((x+25,y+h,x+16,y+h+15,x+44,y+h),fill=color,width=5)
        for a in (26,49,72):d.ellipse((x+a-3,y+29,x+a+3,y+35),fill=color)
    def check(x,y,color=TEAL):
        d.line((x,y+20,x+18,y+38,x+57,y-7),fill=color,width=9)
    def clock(x,y,color=GOLD):
        d.ellipse((x-40,y-40,x+40,y+40),outline=color,width=5)
        d.line((x,y-24,x,y,x+21,y+12),fill=color,width=5)
    def card(x,y,status,color,detail='咨询客户',w=550):
        box(x+4,y+9,w,220,fill='#DCE4E1')
        box(x,y,w,220)
        d.rounded_rectangle((x+28,y+32,x+135,y+156),18,fill='#E6F2EE')
        person(x+60,y+48,color)
        text(x+164,y+38,detail,42)
        text(x+164,y+116,status,36,color)
        d.line((x+164,y+180,x+w-35,y+180),fill='#E7EBE8',width=3)
    def arrow(x,y,length=125,color='#AFBFBD'):
        d.line((x,y,x+length,y),fill=color,width=5)
        d.line((x+length-18,y-18,x+length,y,x+length-18,y+18),fill=color,width=5)
    def column(x,w,title,number,color,active=True):
        box(x,285,w,505,fill='#E3EBE6')
        box(x+25,313,64,54,fill=color if active else '#CBD7D1',r=12)
        text(x+39,318,number,32,'white')
        text(x+112,315,title,41,color if active else MUTED)
    kind=spec['kind']; events=spec['events']
    text(115,83,'客户流程  /  '+spec.get('eyebrow','状态与动作'),30,MUTED)
    text(113,151,spec['title'],60)
    text(1630,94,'流程示意',28,MUTED)
    if kind=='states':
        titles=['未回复','已购买','没兴趣']; colors=[GOLD,TEAL,CORAL]
        for i,(title,col) in enumerate(zip(titles,colors)):
            x=115+i*574
            box(x,285,540,505,fill='#E4EBE5')
            text(x+37,324,title,48,col)
            active=ease((t-events[i])/.42)
            if active>0:
                y=440+24*(1-active)
                card(x+25,y,title,col,w=490)
                if i==0: clock(x+465,365,col)
                elif i==1:check(x+440,348,col)
                else:
                    d.line((x+446,348,x+483,385),fill=col,width=7)
                    d.line((x+483,348,x+446,385),fill=col,width=7)
        text(115,824,'不同客户的并列状态',31,MUTED)
    else:
        left,right=115,1060
        titles={'entry':('新客户','跟进中'),'no_reply':('跟进中','未回复'),'registration':('未回复','报名')}
        a,b=titles[kind]; move=events[-1]
        progress=ease((t-move)/.65)
        column(left,745,a,'01' if kind=='entry' else '•',TEAL)
        column(right,745,b,'02' if kind=='entry' else '•',GOLD if kind=='no_reply' else TEAL,progress>0)
        arrow(891,548,125,TEAL if progress>0 else '#AFBFBD')
        x=left+95+(right-left)*progress
        label=a if progress<.5 else b
        card(x,449,label,TEAL if kind!='no_reply' else GOLD)
        if kind=='entry':
            if t>=events[1]:
                box(left+40,712,252,57,fill='#CBE2D8',r=12);text(left+60,718,'第 1 天',34,TEAL)
            text(right+38,716,'条件：尚未购买',34,GOLD)
        elif kind=='no_reply':
            clock(890,397,GOLD)
            text(left+37,717,'条件：没有回复',34,GOLD)
            if progress>.9:
                bubble(right+600,696,90,57,GOLD)
        elif kind=='registration':
            if t>=events[1]:
                bubble(810,399,98,60,TEAL)
                text(939,395,'收到回复',30,TEAL)
            if progress>.9: check(right+650,719,TEAL)
            text(right+38,717,'条件：回复并报名',34,TEAL)
    d.line((115,894,1805,894),fill='#CDD9D1',width=2)
    # Subtitles occupy the lower 140 pixels in the unified render, not here.
    return im.resize((width,height),Image.Resampling.LANCZOS) if s!=1 else im

def validate_spec(spec):
    require(spec.get('kind') in ('entry','states','no_reply','registration'),'process_kind','Unknown process kind')
    require(spec.get('title') and spec.get('purpose'),'process_purpose','Title and spoken purpose required')
    events=spec.get('events',[]); duration=spec.get('duration',0)
    count={'entry':3,'states':3,'no_reply':2,'registration':3}[spec['kind']]
    require(len(events)==count and events[0]==0 and all(a<b for a,b in zip(events,events[1:])) and events[-1]<duration,
            'process_events','Events must ascend from zero and fit actual output seconds')

def render_scene(spec,target):
    validate_spec(spec);target=Path(target)
    require(not target.exists(),'process_exists','Use a new asset version')
    target.parent.mkdir(parents=True,exist_ok=True)
    cmd=[executable('ffmpeg'),'-v','error','-nostdin','-n','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0',
         '-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(target)]
    with target.with_suffix('.log').open('wb') as log:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if __import__('os').name=='nt' else 0)
        try:
            for n in range(math.ceil(spec['duration']*30)):proc.stdin.write(frame(spec,n/30).tobytes())
        finally: proc.stdin.close()
        require(proc.wait()==0,'process_render','Inspect procedural render log')
    atomic_json(target.with_suffix('.source.json'),{'spec':spec,'sha256':file_hash(target),'basis':'authored illustration, not product or customer evidence'})
    return target
