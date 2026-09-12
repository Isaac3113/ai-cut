"""Object-led CRM illustrations; all UI is explicitly illustrative, not a product capture."""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from talking_head_editor.util import require, executable, atomic_json, file_hash, probe
from talking_head_editor.visuals import font

KINDS={'states':3,'entry':2,'no_reply':2,'registration':3}
def validate(spec):
    require(isinstance(spec,dict),'scene_spec','Scene must be an object')
    require(isinstance(spec.get('kind'),str) and spec['kind'] in KINDS,'scene_kind','Choose states, entry, no_reply or registration')
    duration=spec.get('duration')
    require(isinstance(duration,(int,float)) and not isinstance(duration,bool) and math.isfinite(duration) and .5<=duration<=30,'scene_duration','Scene must last 0.5..30 seconds')
    events=spec.get('events',[])
    require(isinstance(events,list) and len(events)==KINDS[spec['kind']] and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in events)
            and events[0]==0 and all(a<b for a,b in zip(events,events[1:])) and events[-1]<duration,'scene_events','Use ordered source-relative event times starting at zero')
    require(isinstance(spec.get('purpose'),str) and spec['purpose'].strip(),'scene_purpose','Record what the picture explains')
    return spec

def frame(spec,t,width=1920,height=1080):
    validate(spec)
    require((width,height)==(1920,1080) or (width,height)==(1280,720),'scene_geometry','Current illustrative desktop layout needs 16:9')
    scale=width/1280
    image=Image.new('RGB',(width,height),'#E9EDEF'); d=ImageDraw.Draw(image)
    def box(b,fill,r=0,outline=None,line=1):
        b=tuple(round(x*scale) for x in b)
        if r: d.rounded_rectangle(b,radius=round(r*scale),fill=fill,outline=outline,width=max(1,round(line*scale)))
        else: d.rectangle(b,fill=fill,outline=outline,width=max(1,round(line*scale)))
    def text(x,y,s,size=18,color='#25354A'):
        d.text((round(x*scale),round(y*scale)),s,font=font(size*scale),fill=color,anchor='lt')
    def line(points,color='#8190A0',w=2):
        d.line([(round(x*scale),round(y*scale)) for x,y in points],fill=color,width=max(1,round(w*scale)),joint='curve')
    def circle(x,y,r,color):
        d.ellipse(((x-r)*scale,(y-r)*scale,(x+r)*scale,(y+r)*scale),fill=color)
    def check(x,y,color='#248C68',s=1): line([(x-9*s,y),(x-2*s,y+7*s),(x+12*s,y-10*s)],color,3*s)
    def avatar(x,y,r=22,color='#DDE7EF'):
        circle(x,y,r,color); circle(x,y-r*.20,r*.28,'#758D9E')
        d.pieslice(((x-r*.58)*scale,(y-r*.05)*scale,(x+r*.58)*scale,(y+r*1.04)*scale),180,360,fill='#758D9E')
    def clock(x,y,r=15,color='#B08243'):
        d.ellipse(((x-r)*scale,(y-r)*scale,(x+r)*scale,(y+r)*scale),outline=color,width=round(2*scale))
        line([(x,y-r*.6),(x,y),(x+r*.4,y+r*.2)],color,2)
    def message(x,y,w=34,h=25,color='#50768F'):
        box((x,y,x+w,y+h),None,5,color,2)
        line([(x+7,y+h),(x+7,y+h+5),(x+15,y+h)],color,2)
        line([(x+7,y+8),(x+w-7,y+8)],color,2)
        line([(x+7,y+15),(x+w-14,y+15)],color,2)
    def bag(x,y,size=54):
        box((x-size*.65,y-size*.3,x+size*.65,y+size*.7),'#F7FAF8',6,'#41866C',2)
        d.arc(((x-size*.3)*scale,(y-size*.7)*scale,(x+size*.3)*scale,(y+size*.05)*scale),180,360,fill='#41866C',width=round(3*scale))
        check(x,y+size*.2,s=1.25)
    def calendar(x,y,size=55):
        box((x-size*.7,y-size*.55,x+size*.7,y+size*.7),'white',8,'#4F7693',2)
        box((x-size*.7,y-size*.55,x+size*.7,y-size*.2),'#DCE8F0',8)
        for dx in (-.36,.36): line([(x+dx*size,y-size*.7),(x+dx*size,y-size*.4)],'#4F7693',4)
        check(x,y+size*.23,'#347359',1.5)
    def cursor(x,y):
        pts=[(x,y),(x+2,y+24),(x+9,y+18),(x+16,y+30),(x+21,y+27),(x+14,y+15),(x+24,y+14)]
        d.polygon([(round(a*scale),round(b*scale)) for a,b in pts],fill='white',outline='#283849',width=round(1*scale))
    # A desktop window, neutral natural typography, restrained blue accents.
    box((48,58,1238,598),'#D9DEE2',20)
    box((42,50,1230,588),'#FFFFFF',16)
    box((42,50,1230,99),'#F7F8F9',16)
    for i,c in enumerate(('#C2CBD2','#CED6DC','#D7DEE3')): circle(64+i*17,74,4,c)
    text(124,64,'客户工作台',16,'#617384')
    text(1101,65,'流程示意',15,'#6C7A88')
    line([(42,99),(1230,99)],'#E6EAED',1)
    box((43,100,213,587),'#F7F9FA')
    for i,label in enumerate(['概览','客户','跟进','日程']):
        yy=134+i*60
        if i==1: box((55,yy-12,199,yy+28),'#E4EDF4',8)
        if i==0: box((73,yy-1,87,yy+12),None,3,'#708494',2)
        elif i==1: avatar(80,yy+6,12)
        elif i==2: message(71,yy-2,18,14,'#708494')
        else: box((71,yy-2,89,yy+14),None,3,'#708494',2); line([(71,yy+3),(89,yy+3)],'#708494',2)
        text(108,yy-2,label,16,'#364D63' if i==1 else '#788897')
    text(65,543,'客户流程 · 操作示意',11,'#93A0AC')
    kind=spec['kind']; events=spec['events']; active=max(i for i,at in enumerate(events) if t>=at)
    age=t-events[active]; ease=min(1,max(0,age/.65)); ease=ease*ease*(3-2*ease)
    if kind=='states':
        text(244,126,'查看客户当前状态',25)
        text(246,166,'点开不同客户，看到对应的沟通与购买状态',15,'#7D8B98')
        labels=['等待回复','已经购买','暂时无兴趣']
        for i,label in enumerate(labels):
            y=229+i*97
            box((247,y-10,654,y+72),'#EDF3F7' if i==active else '#FFFFFF',10,'#CCDCE8' if i==active else '#E7ECEF',1)
            avatar(283,y+27,22)
            text(322,y+3,['咨询客户','成交客户','暂未需要的客户'][i],19)
            text(322,y+36,label,15,'#647C8F')
            if i==0: clock(618,y+27,12)
            elif i==1: check(618,y+27)
            else: circle(618,y+27,12,'#E4E8EB'); line([(612,y+27),(624,y+27)],'#8695A1',2)
        box((691,219,1186,532),'#F9FBFC',12,'#E3EAF0',1)
        if active==0:
            box((837,245,1043,503),'#344552',19); box((845,254,1035,491),'#FFFFFF',13)
            box((904,258,976,266),'#344552',5)
            avatar(939,303,20)
            box((867,341,1009,373),'#E5EFF4',7); message(879,350,28,14)
            box((899,388,1009,418),'#F0F2F4',7)
            for dx in [-10,0,10]: circle(951+dx,402,2,'#A0AAB3')
            clock(940,455,13)
            text(715,548,'消息已发出，等待客户回应',15,'#647C8F')
        elif active==1:
            bag(849,363,58)
            box((956,274,1113,466),'white',3,'#D7E0E6',1)
            text(978,298,'购买记录',18)
            for yy,ww in [(344,105),(370,83),(395,96)]: box((978,yy,978+ww,yy+5),'#D9E1E6',2)
            check(1035,442)
            text(715,548,'客户状态已更新为已购买',15,'#647C8F')
        else:
            message(844,290,196,101,'#8B9AA6')
            circle(1061,431,34,'#ECF0F2'); line([(1047,431),(1075,431)],'#7B8C9A',4)
            text(863,329,'暂时无兴趣',21,'#5B6F7E')
            text(715,548,'记录客户意向，方便后续判断',15,'#647C8F')
        cursor(601,267+active*97)
    else:
        if kind=='entry':
            title='新客户进入，开始跟进'; condition='条件：客户尚未购买，继续跟进'
            labels=['新客户','跟进中']; positions=[0,1]
        elif kind=='no_reply':
            title='没有回复时，更新客户状态'; condition='条件：客户还没有回复'
            labels=['跟进中','未回复']; positions=[0,1]
        else:
            title='客户回复并报名后，更新状态'; condition='条件：回复，并且报名'
            labels=['未回复','客户回应','报名分享会']; positions=[0,1,2]
        text(244,126,title,25); text(247,168,condition,15,'#718493')
        n=len(labels); gap=22; cw=(944-gap*(n-1))/n; lefts=[246+i*(cw+gap) for i in range(n)]
        for i,label in enumerate(labels):
            x=lefts[i]
            box((x,222,x+cw,543),'#F5F7F9',10)
            circle(x+21,246,4,['#7B9AB1','#B59C6F','#739E8A'][i])
            text(x+36,234,label,18)
            line([(x+12,270),(x+cw-12,270)],'#E1E7EC',1)
        prev=positions[max(0,active-1)]; now=positions[active]
        x=lefts[prev]+(lefts[now]-lefts[prev])*ease+14
        cardwidth=cw-28
        box((x+3,304,x+cardwidth+3,442),'#DEE5EA',10)
        box((x,300,x+cardwidth,438),'#FFFFFF',10,'#C8D9E4',1)
        avatar(x+38,340,20)
        text(x+70,321,'咨询客户',18)
        text(x+70,352,('第 1 天' if kind=='entry' and active==0 else labels[now]),14,'#728592')
        line([(x+18,382),(x+cardwidth-18,382)],'#E9EDF0',1)
        message(x+21,395,23,18)
        text(x+57,396,'查看沟通记录',13,'#8897A3')
        # Object cues show a message, elapsed waiting, or a registration event.
        if kind=='entry' and active==1:
            message(lefts[now]+cw-96,469,44,30,'#5D809A')
            for dot in range(3): circle(lefts[now]+cw-42+dot*8,484,2,'#A5B8C6')
        elif kind=='no_reply':
            clock(lefts[now]+cw-52,486,22)
        elif kind=='registration' and active==1:
            message(lefts[now]+cw/2-26,472,53,31,'#4B8D70'); check(lefts[now]+cw/2+41,488,s=.7)
        elif kind=='registration' and active==2:
            calendar(lefts[now]+cw/2,488,36)
        cursor(x+cardwidth-22,413)
        if active and age<.75:
            # A small selection pulse accompanies the drag; no decorative flashing.
            rr=8+age*13
            d.ellipse(((x+cardwidth-22-rr)*scale,(413-rr)*scale,(x+cardwidth-22+rr)*scale,(413+rr)*scale),outline='#A9C3D5',width=round(scale))
    return image

def render_scene(spec,target):
    validate(spec); target=Path(target)
    require(not target.exists(),'scene_exists','Choose a new output path')
    target.parent.mkdir(parents=True,exist_ok=True)
    fps=30; frames=math.ceil(spec['duration']*fps-1e-7)
    cmd=[executable('ffmpeg'),'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
    log=target.with_suffix('.log')
    with log.open('wb') as err:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err,stdout=subprocess.DEVNULL)
        try:
            for i in range(frames): process.stdin.write(frame(spec,i/fps).tobytes())
            process.stdin.close(); code=process.wait(timeout=120)
        except BaseException:
            process.kill(); process.wait(); raise
    require(code==0,'scene_render','Inspect '+str(log))
    info=probe(target)
    require(abs(float(info['format']['duration'])-frames/fps)<.1,'scene_duration','Encoded scene length mismatch')
    receipt={'spec':spec,'frames':frames,'fps':fps,'sha256':file_hash(target),'origin':'Locally drawn illustrative UI, not a real product/customer screenshot','width':1920,'height':1080}
    atomic_json(target.with_suffix('.json'),receipt)
    return receipt

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--spec',type=Path,required=True); parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(); print(json.dumps(render_scene(json.loads(args.spec.read_text(encoding='utf-8-sig')),args.out),ensure_ascii=False))
if __name__=='__main__': main()
