"""Create a restrained owned-video ending from an inspected source-frame crop."""
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from talking_head_editor.visuals import font
from talking_head_editor.util import executable, require, atomic_json, file_hash


def frame(portrait,t,width=1920,height=1080,duration=4.1):
    image=Image.new('RGB',(width,height),'#0F292D');d=ImageDraw.Draw(image)
    sx=width/1920;sy=height/1080
    # Layout is authored for landscape; other ratios are composed separately.
    require(width/height>1.7 and width/height<1.8,'ending_geometry','Use the authored 16:9 ending')
    ease=min(1,max(0,t/.6));ease=1-(1-ease)**3
    center=(round(518*sx),round((473+20*(1-ease))*sy));radius=round((202+12*ease)*sx)
    d.ellipse((center[0]-radius-17,center[1]-radius-17,center[0]+radius+17,center[1]+radius+17),outline='#3C6075',width=max(1,round(2*sx)))
    im=portrait.resize((radius*2,radius*2),Image.Resampling.LANCZOS)
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).ellipse((0,0,im.width-1,im.height-1),fill=255)
    image.paste(im,(center[0]-radius,center[1]-radius),mask)
    d=ImageDraw.Draw(image)
    def text(x,y,value,size,color='#F2F5F6'):
        d.text((round(x*sx),round(y*sy)),value,font=font(size*sx),fill=color,anchor='lt')
    text(865,276,'客户流程 · 系统分享',26,'#91ACBA')
    text(855,358,'让每一步',94)
    text(855,482,'清清楚楚',94,'#F0BE69')
    if t>.25:
        end=855+340*min(1,(t-.25)/.65)
        d.line((855*sx,624*sy,end*sx,624*sy),fill='#64B8AF',width=max(1,round(3*sx)))
    text(860,669,'我们课程见',42,'#C0D1D8')
    text(174,924,'Music: Digital Lemonade — Kevin MacLeod (incompetech.com)',21,'#99ACB8')
    text(174,960,'CC BY 4.0 · creativecommons.org/licenses/by/4.0/ · Edited & mixed',21,'#99ACB8')
    if t>duration-.5:
        alpha=(t-(duration-.5))/.5
        image=Image.blend(image,Image.new('RGB',image.size,'#0F292D'),min(1,alpha*.9))
    return image


def render_ending_asset(frame_path,crop,target,duration=4.1):
    target=Path(target);require(not target.exists(),'ending_exists','Choose a new ending file')
    with Image.open(frame_path) as im:
        require(0<=crop[0]<crop[2]<=im.width and 0<=crop[1]<crop[3]<=im.height,'portrait_crop','Crop outside source')
        portrait=im.convert('RGB').crop(crop)
    log=target.with_suffix('.log')
    cmd=[executable('ffmpeg'),'-v','error','-nostdin','-n','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0',
         '-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(target)]
    with log.open('wb') as err:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err)
        try:
            for n in range(math.ceil(duration*30)):
                process.stdin.write(frame(portrait,n/30,duration=duration).tobytes())
        finally:process.stdin.close()
        require(process.wait()==0,'ending_render',f'Inspect {log}')
    atomic_json(target.with_suffix('.source.json'),{'source_frame':str(frame_path),'source_sha256':file_hash(frame_path),'crop':crop,'duration':duration,'note':'Actual user frame; no generated face, identity, or voice'})
    return target
