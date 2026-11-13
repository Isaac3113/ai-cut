import React from 'react';
import {AbsoluteFill, Composition, Easing, Img, interpolate, OffthreadVideo, registerRoot, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Item = {title:string; detail:string; media?:string; mediaType?:'image'|'video'; sourceStart?:number};
type Scene = {kind:'hook'|'prompt'|'shift'|'flow'|'gallery'|'folder'|'closing'; title:string; emphasis:string; detail:string; duration:number; items:Item[]};
type Caption = {start:number;end:number;text:string};
export type Inputs = {duration:number;aspect:'9:16'|'16:9';variant:'paper-editorial'|'dark-workbench'|'material-wall';accent:string;secondary:string;paper:string;ink:string;label:string;presenter?:string;presenterType?:'image'|'video';presenterLabel?:string;presenterStart?:number;font?:string;seed:number;scenes:Scene[];captions:Caption[]};
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const tween=(f:number,a:number,b:number,x=0,y=1)=>interpolate(f,[a,b],[x,y],{...clamp,easing:Easing.bezier(.16,1,.3,1)});
const pop=(f:number,delay=0)=>spring({frame:Math.max(0,f-delay),fps:30,config:{stiffness:125,damping:20,mass:.9}});
const fit=(text:string,base:number,capacity:number)=>Math.min(base,base*capacity/Math.max(capacity,Array.from(text).reduce((n,c)=>n+(/[a-z0-9 ]/i.test(c)?.55:1),0)));
const textStyle:React.CSSProperties={fontWeight:850,letterSpacing:'-.045em',lineHeight:1.16};
const Frame:React.FC<{p:Inputs;title:string;style?:React.CSSProperties;children:React.ReactNode}>=({p,title,style,children})=><div style={{position:'absolute',background:p.paper,border:`2px solid ${p.ink}`,boxShadow:`0 24px 45px ${p.ink}20`,overflow:'hidden',...style}}><div style={{height:44,borderBottom:`1px solid ${p.ink}28`,display:'flex',alignItems:'center',gap:9,padding:'0 18px',fontSize:16,letterSpacing:1.5,fontWeight:700}}>{[0,1,2].map(n=><i key={n} style={{width:7,height:7,borderRadius:9,background:n===0?p.accent:`${p.ink}40`}}/>)}<span style={{marginLeft:8}}>{title}</span></div><div style={{position:'absolute',top:44,left:0,right:0,bottom:0,overflow:'hidden'}}>{children}</div></div>;

const Media:React.FC<{item:Item;localFrame:number;p:Inputs;style?:React.CSSProperties}>=({item,localFrame,p,style})=>{
 const currentFrame=useCurrentFrame();
 if(!item.media)return <div style={{width:'100%',height:'100%',background:`linear-gradient(135deg,${p.accent}14,${p.secondary}18)`,padding:36,display:'flex',flexDirection:'column',justifyContent:'center',gap:17,...style}}><span style={{fontSize:20,opacity:.6}}>内容窗口 / 示意</span><span style={{fontSize:fit(item.title,66,10),...textStyle}}>{item.title}</span><span style={{fontSize:26,lineHeight:1.55,opacity:.7}}>{item.detail}</span><div style={{width:'55%',height:5,background:p.accent,marginTop:20}}/></div>;
 const mediaStyle:React.CSSProperties={width:'100%',height:'100%',objectFit:'cover',...style};
 return item.mediaType==='video'?<Sequence from={currentFrame-localFrame} layout='none'><OffthreadVideo src={staticFile(item.media)} startFrom={Math.round((item.sourceStart??0)*30)} muted style={mediaStyle}/></Sequence>:<Img src={staticFile(item.media)} style={mediaStyle}/>;
};

const SceneView:React.FC<{s:Scene;f:number;p:Inputs;index:number}>=({s,f,p,index})=>{
 const wide=p.aspect==='16:9', w=wide?1920:1080,h=wide?1080:1920;
 const sf=s.duration*30;
 const wall=p.variant==='material-wall', dark=p.variant==='dark-workbench';
 const headlineX=wide?105:78,headlineY=wide?155:190;
 const accent=p.accent;
 const textWidth=wide?1080:(p.presenter&&!['hook','closing'].includes(s.kind)?660:910);
 const title=<div style={{position:'absolute',left:headlineX,top:headlineY,maxWidth:textWidth,transform:`translateY(${tween(f,0,25,55,0)}px)`,opacity:tween(f,0,16),...textStyle}}><div style={{fontSize:fit(s.title,wide?96:106,textWidth/(wide?96:106))}}>{s.title}</div><div style={{marginTop:wide?8:18,fontSize:fit(s.emphasis,wide?126:142,textWidth/(wide?126:142)),color:accent}}>{s.emphasis}</div><div style={{fontWeight:550,letterSpacing:0,lineHeight:1.55,fontSize:wide?27:30,marginTop:24,maxWidth:wide?900:850}}>{s.detail}</div></div>;
 const baseY=wide?470:740;
 const presenterReserved=wide?1300:770;
 const camera=1+tween(f,0,sf,.012,0);
 return <AbsoluteFill style={{background:p.paper,color:p.ink,overflow:'hidden'}}>
  <AbsoluteFill style={{backgroundImage:`radial-gradient(${p.ink}30 .7px,transparent .7px)`,backgroundSize:dark?'28px 28px':'10px 10px',opacity:dark?.25:.18}}/>
  <AbsoluteFill style={{transform:`scale(${camera}) translate(${Math.sin((p.seed+index)*1.71)*tween(f,0,sf,-5,5)}px,${tween(f,0,sf,7,-7)}px)`}}>
  {s.kind!=='flow'&&s.kind!=='gallery'&&title}
  {s.kind==='hook'&&<>{s.items.map((a,i)=>{const q=pop(f,40+i*15);const x=wide?105+i*300:80+i*305;return <div key={i} style={{position:'absolute',left:x,top:wide?460:625,width:wide?270:280,height:94,padding:21,border:`1px solid ${p.ink}45`,background:p.paper,boxShadow:`0 9px 22px ${p.ink}15`,transform:`translateY(${(1-q)*90}px) rotate(${(i-1)*2}deg)`,opacity:q,fontSize:30,fontWeight:800}}><span style={{color:accent,fontSize:20,marginRight:16}}>0{i+1}</span>{a.title}</div>})}</>}
  {s.kind==='prompt'&&<>
   <Frame p={p} title='ONE REQUEST → ONE RESULT / 示意' style={{left:wide?105:90,top:wide?440:650,width:wide?1100:900,height:wide?450:700,transform:`rotate(${tween(f,0,sf,-2.5,-.6)}deg)`}}>
    <Media item={s.items[0]??{title:'输入要求',detail:''}} localFrame={f} p={p} style={{opacity:.7}}/>
    <div style={{position:'absolute',left:32,right:32,top:32,background:p.paper,padding:30,borderRadius:16,boxShadow:`0 20px 35px ${p.ink}20`,fontSize:fit(s.items[0]?.detail??'',wide?43:47,22),fontWeight:700,lineHeight:1.5,opacity:tween(f,10,30),transform:`translateY(${tween(f,10,40,40,0)}px)`}}>{(s.items[0]?.detail??s.detail).slice(0,Math.floor(tween(f,25,Math.min(sf*.4,90),0,(s.items[0]?.detail??s.detail).length)))}<span style={{color:accent}}>│</span></div>
   </Frame>
   <div style={{position:'absolute',left:wide?790:440,top:wide?675:1210,width:wide?460:510,height:wide?240:320,background:p.paper,border:`1px solid ${p.ink}35`,boxShadow:`0 20px 45px ${p.ink}20`,padding:35,opacity:tween(f,sf*.42,sf*.53),transform:`translateY(${tween(f,sf*.42,sf*.65,140,0)}px) rotate(4deg)`}}><span style={{fontSize:18,color:accent,fontWeight:800}}>OUTPUT / 01</span><div style={{...textStyle,fontSize:fit(s.items[1]?.title??'输出内容',48,10),marginTop:20}}>{s.items[1]?.title??'输出内容'}</div>{[0,1,2].map(i=><div key={i} style={{height:5,width:`${tween(f,sf*.55+i*6,sf*.75+i*6,0,95-i*15)}%`,background:`${p.ink}45`,marginTop:18}}/>)}</div>
  </>}
  {s.kind==='shift'&&<><div style={{position:'absolute',left:wide?90:80,top:wide?520:760,width:wide?1020:910,height:120,background:accent,clipPath:'polygon(0 20%,75% 20%,75% 0,100% 50%,75% 100%,75% 80%,0 80%)',opacity:tween(f,16,28),transform:`translateX(${tween(f,16,60,-w,0)}px) rotate(-10deg)`}}/><div style={{position:'absolute',left:wide?200:110,top:wide?730:1170,width:wide?900:860,height:wide?250:310,padding:40,background:p.ink,color:p.paper,boxShadow:`0 24px 50px ${p.ink}20`,opacity:tween(f,50,70),transform:`translateY(${tween(f,50,90,130,0)}px) rotate(-3deg)`}}><div style={{...textStyle,fontSize:fit(s.items[0]?.title??'开始执行',wide?78:100,8),color:p.secondary}}>{s.items[0]?.title??'开始执行'}</div><div style={{fontSize:30,marginTop:25}}>{s.items[0]?.detail??s.detail}</div></div></>}
  {s.kind==='flow'&&<>
   <div style={{position:'absolute',left:headlineX,top:headlineY,width:textWidth,...textStyle,fontSize:fit(s.title,wide?78:95,textWidth/(wide?78:95))}}>{s.title}<div style={{color:accent,fontSize:fit(s.emphasis,wide?110:130,textWidth/(wide?110:130)),marginTop:15}}>{s.emphasis}</div></div>
   <div style={{position:'absolute',left:wide?120:120,top:wide?470:690,width:wide?1070:840,height:wide?410:800}}>
    <svg style={{position:'absolute',inset:0,width:'100%',height:'100%',overflow:'visible'}} viewBox={wide?'0 0 1070 410':'0 0 840 800'}>{s.items.slice(1).map((_,i)=>{const n=s.items.length;const a=wide?{x:90+i*930/(n-1),y:200}:{x:420,y:90+i*650/(n-1)};const b=wide?{x:90+(i+1)*930/(n-1),y:200}:{x:420,y:90+(i+1)*650/(n-1)};return <path key={i} d={`M${a.x} ${a.y} L${b.x} ${b.y}`} fill='none' stroke={accent} strokeWidth='4' pathLength={1} strokeDasharray={1} strokeDashoffset={1-tween(f,35+i*22,65+i*22)}/>})}</svg>
    {s.items.map((a,i)=>{const q=pop(f,15+i*22);return <div key={i} style={{position:'absolute',left:wide?i*930/Math.max(1,s.items.length-1):0,top:wide?95:i*650/Math.max(1,s.items.length-1),width:wide?220:840,height:wide?210:140,background:dark?p.ink:p.paper,color:dark?p.paper:p.ink,border:`2px solid ${i===0?accent:p.ink+'45'}`,borderRadius:18,padding:wide?25:25,boxShadow:`7px 9px 0 ${p.ink}15`,transform:`translateY(${(1-q)*55}px) scale(${.94+.06*q})`,opacity:q}}><span style={{position:'absolute',left:25,top:25,fontSize:wide?18:20,color:accent,fontWeight:800}}>0{i+1}</span><div style={{fontSize:fit(a.title,38,wide?7:14),fontWeight:850,marginTop:wide?38:0,paddingLeft:wide?0:65}}>{a.title}</div><div style={{fontSize:wide?20:22,opacity:.7,marginTop:12,marginLeft:wide?0:65,lineHeight:1.3}}>{a.detail}</div></div>})}
   </div>
  </>}
  {s.kind==='gallery'&&<>
   <div style={{position:'absolute',left:headlineX,top:headlineY,width:textWidth,...textStyle,fontSize:fit(s.title,wide?80:104,textWidth/(wide?80:104))}}>{s.title}<div style={{color:accent,marginTop:14,fontSize:fit(s.emphasis,wide?112:133,textWidth/(wide?112:133))}}>{s.emphasis}</div></div>
   {s.items.map((a,i)=>{const total=s.items.length;const seq=tween(f,0,sf*.65,0,total-1);const focus=i-seq;const overview=tween(f,sf*.7,sf*.88);const scale=(wide?.9:.95)*(1-overview)+((wide?1:.43))*overview;const x0=wide?115+i*370:160+focus*850;const x=wide?x0:x0*(1-overview)+(78+i*300)*overview;const y=wide?500:730;return <div key={i} style={{position:'absolute',left:x,top:y,width:wide?330:780,height:wide?350:690,transformOrigin:'0 0',transform:`scale(${scale}) rotate(${(wall?(i%2?2:-2):0)*(1-overview)}deg)`,opacity:pop(f,i*8)}}><Frame p={p} title={`0${i+1} / MATERIAL WINDOW`} style={{left:0,top:0,width:wide?330:780,height:wide?270:520}}><Media p={p} item={a} localFrame={f} style={{transform:`scale(${tween(f,0,sf,1.02,1.10)})`}}/></Frame><div style={{position:'absolute',top:wide?286:545,left:0,fontSize:fit(a.title,wide?33:66,wide?10:10),fontWeight:850}}>{a.title}</div><div style={{position:'absolute',top:wide?330:635,left:0,fontSize:wide?19:27,opacity:.7}}>{a.detail}</div></div>})}
   <div style={{position:'absolute',left:headlineX,top:wide?920:1500,width:wide?1050:900,fontSize:wide?29:31,fontWeight:650,opacity:tween(f,sf*.72,sf*.88)}}>{s.detail}</div>
  </>}
  {s.kind==='folder'&&<>
   {s.items.map((a,i)=>{const gather=tween(f,25,85);return gather<.98?<div key={i} style={{position:'absolute',left:wide?180+i*230:125+i*220,top:(wide?500:750)+i*45+gather*150,width:wide?320:380,height:250,background:p.paper,border:`1px solid ${p.ink}45`,padding:30,opacity:1-gather,transform:`rotate(${(i-1)*11*(1-gather)}deg) scale(${1-gather*.4})`}}><div style={{fontSize:34,fontWeight:800}}>{a.title}</div><div style={{fontSize:22,marginTop:30}}>{a.detail}</div></div>:null})}
   <div style={{position:'absolute',left:wide?180:145,top:wide?650:1030,width:wide?900:800,height:wide?250:390,background:accent,borderRadius:16,boxShadow:`0 25px 45px ${p.ink}20`,transform:`perspective(1400px) rotateX(${tween(f,0,90,-8,0)}deg) scale(${tween(f,sf*.7,sf*.95,1,.86)})`}}><div style={{position:'absolute',left:0,top:-45,width:270,height:60,borderRadius:'18px 18px 0 0',background:accent}}/><div style={{padding:40,...textStyle,fontSize:fit(s.items[0]?.title??s.emphasis,wide?90:110,6),color:p.ink}}>{s.items[0]?.title??s.emphasis}</div><span style={{position:'absolute',bottom:30,right:40,fontSize:25,fontWeight:700}}>保存方法 → 以后复用</span></div>
  </>}
  {s.kind==='closing'&&<div style={{position:'absolute',left:wide?110:95,top:wide?480:730,width:wide?1070:890,height:wide?400:880,borderRadius:24,overflow:'hidden',boxShadow:`0 20px 55px ${p.ink}20`,border:`3px solid ${p.ink}20`,transform:`translateY(${tween(f,5,35,65,0)}px)`,opacity:tween(f,0,20)}}><Media item={s.items[0]??{title:s.emphasis,detail:s.detail}} p={p} localFrame={f}/></div>}
  </AbsoluteFill>
  <div style={{position:'absolute',left:35,right:35,top:28,height:48,display:'flex',justifyContent:'space-between',borderBottom:`1px solid ${p.ink}2a`,fontSize:wide?19:18,fontWeight:700,letterSpacing:2}}><span><i style={{display:'inline-block',height:15,width:15,borderRadius:4,background:accent,marginRight:12}}/>{p.label}</span><span>{String(index+1).padStart(2,'0')} / WORKSPACE</span></div>
 </AbsoluteFill>;
};

export const Film:React.FC<Inputs>=(p)=>{
 const f=useCurrentFrame(),{fps,width,height}=useVideoConfig();
 let cursor=0;const scenes=p.scenes.map((scene,i)=>{const from=cursor;cursor+=Math.round(scene.duration*fps);return {...scene,from,to:cursor,index:i};});
 const s=scenes.find(scene=>f>=scene.from&&f<scene.to)??scenes[scenes.length-1];
 const wide=width>height,large=s.kind==='hook'||s.kind==='closing';
 const inset=large&& !wide?{left:72,top:760,width:936,height:880}:{left:wide?1330:785,top:wide?150:100,width:wide?460:235,height:wide?720:320};
 const caption=p.captions.find(c=>f/fps>=c.start&&f/fps<c.end);
 return <AbsoluteFill style={{fontFamily:'EditorialNoto,"Microsoft YaHei",sans-serif',color:p.ink,background:p.paper}}>
  {p.font&&<style>{`@font-face{font-family:EditorialNoto;src:url('${staticFile(p.font)}');font-weight:100 900;font-display:block}`}</style>}
  <SceneView s={s} f={f-s.from} p={p} index={s.index}/>
  {p.presenter&&<div style={{position:'absolute',...inset,borderRadius:24,overflow:'hidden',border:'3px solid white',boxShadow:`0 20px 50px ${p.ink}20`,transform:`translateY(${tween(f-s.from,0,25,20,0)}px)`}}>{p.presenterType==='video'?<OffthreadVideo src={staticFile(p.presenter)} startFrom={Math.round((p.presenterStart??0)*fps)} muted style={{width:'100%',height:'100%',objectFit:'cover',objectPosition:'50% 60%'}}/>:<Img src={staticFile(p.presenter)} style={{width:'100%',height:'100%',objectFit:'cover'}}/>}<div style={{position:'absolute',bottom:10,left:12,right:12,fontSize:wide?18:15,color:'white',textShadow:'0 1px 4px #000',fontWeight:700}}>{p.presenterLabel??''}</div></div>}
  {caption&&<div style={{position:'absolute',left:wide?100:60,right:wide?100:60,bottom:wide?44:80,textAlign:'center',fontSize:fit(caption.text,wide?49:53,wide?35:17),fontWeight:850,lineHeight:1.4,color:'white',WebkitTextStroke:'4px #171717',paintOrder:'stroke fill',filter:'drop-shadow(0 3px 2px #00000020)'}}>{caption.text}</div>}
 </AbsoluteFill>;
};

const demo:Inputs={duration:4,aspect:'9:16',variant:'paper-editorial',accent:'#FF5B22',secondary:'#DFFF52',paper:'#F6F4EF',ink:'#161616',label:'EDITORIAL CANVAS',seed:1,scenes:[{kind:'hook',title:'把复杂知识',emphasis:'讲成看得懂的画面',detail:'这是可换内容的图形示意。',duration:4,items:[{title:'观察',detail:''},{title:'整理',detail:''},{title:'解释',detail:''}]}],captions:[]};
const Root:React.FC=()=> <Composition id='EditorialCanvas' component={Film} durationInFrames={120} fps={30} width={1080} height={1920} defaultProps={demo} calculateMetadata={({props})=>({durationInFrames:Math.round(props.scenes.reduce((n,s)=>n+s.duration,0)*30),width:props.aspect==='16:9'?1920:1080,height:props.aspect==='16:9'?1080:1920})}/>;
registerRoot(Root);
