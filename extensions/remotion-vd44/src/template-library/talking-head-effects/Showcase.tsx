import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {GraphicLayer} from './GraphicLayers';
import {OrbitMotion} from '../remotion-ui/OrbitMotion';

export type SourceClip = {fromFrame:number;durationInFrames:number;sourceStart:number;playbackRate:number;kind:number;title:string};
export type ShowcaseProps = {clips:SourceClip[];totalFrames:number;sourceFile:string;alphaFile:string};
const W=1080,H=1920,INK='#153340',ACCENT='#47B4D0';
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;

const Source:React.FC<{clip:SourceClip;file:string;alpha?:boolean;style?:React.CSSProperties}>=({clip,file,alpha=false,style})=>(
  <OffthreadVideo src={staticFile(file)} startFrom={Math.round(clip.sourceStart*30)} playbackRate={clip.playbackRate} muted transparent={alpha}
    style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',...style}}/>
);
const Pip:React.FC<{clip:SourceClip;file:string}>=({clip,file})=>(
  <div style={{position:'absolute',left:46,top:1330,width:270,height:270,borderRadius:'50%',overflow:'hidden',border:'5px solid #F2F8FA',boxShadow:'0 10px 30px #0004',zIndex:35}}>
    <Source clip={clip} file={file} style={{position:'absolute',width:270,height:480,top:-15,left:0}}/>
  </div>
);

const Scene:React.FC<{clip:SourceClip;sourceFile:string;alphaFile:string}>=({clip,sourceFile,alphaFile})=>{
  const frame=useCurrentFrame();const n=clip.durationInFrames;
  // The combined green-screen/checklist source clip is split visually at its source-time boundary.
  const sourceTime=clip.sourceStart+frame/30*clip.playbackRate;
  const kind=clip.kind===9&&sourceTime>=21.75?10:clip.kind;
  const title=kind===10?'打勾清单':clip.title;
  const graphicStart=kind===10?Math.round((21.75-clip.sourceStart)/clip.playbackRate*30):0;
  const p=Math.min(1,Math.max(0,frame/Math.max(1,n-1)));
  const pop=interpolate(frame,[0,Math.min(7,n-1)],[0.94,1],clamp);
  const normal=<Source clip={clip} file={sourceFile}/>;
  const person=<Source clip={clip} file={alphaFile} alpha/>;
  let picture:React.ReactNode=normal;
  let graphics=true;let pip=false;

  if(kind===3){
    const zoom=interpolate(p,[0,.45,.53,1],[1,2.8,1.35,1],clamp);
    picture=<><div style={{position:'absolute',inset:0,transform:`scale(${zoom})`,transformOrigin:'58% 36%',filter:`blur(${p>.3&&p<.6?Math.sin((p-.3)/.3*Math.PI)*9:0}px)`}}>{normal}</div>
      <div style={{position:'absolute',inset:70,border:`${Math.max(0,18*(1-p))}px solid ${ACCENT}`,borderRadius:50,transform:`scale(${1+p*4})`,opacity:1-p}}/>
    </>;
  }else if(kind===4){
    picture=<><AbsoluteFill style={{background:'#d5c4a5',backgroundImage:'radial-gradient(#15334022 1px,transparent 1px)',backgroundSize:'16px 16px'}}/>
      <div style={{position:'absolute',inset:0,transform:`translateY(50px) scale(${.88*pop})`,filter:'drop-shadow(5px 0 0 white) drop-shadow(-5px 0 0 white) drop-shadow(0 5px 0 white) drop-shadow(0 -5px 0 white) drop-shadow(0 20px 18px #0005)'}}>{person}</div>
      <div style={{position:'absolute',left:90,top:170,background:'white',padding:'12px 26px',fontSize:70,fontWeight:900,color:INK,transform:'rotate(-9deg)'}}>CUT!</div></>;
  }else if(kind===5){
    picture=<><AbsoluteFill style={{background:INK}}/>{Array.from({length:12},(_,i)=><div key={i} style={{position:'absolute',left:(i%3)*380-40,top:Math.floor(i/3)*500-80+(i%2?1:-1)*p*70,width:345,height:460,borderRadius:22,overflow:'hidden',transform:`rotate(${i%2?5:-5}deg)`,border:'6px solid white'}}><Img src={staticFile(`portrait-${String(i%8+1).padStart(2,'0')}.jpg`)} style={{width:'100%',height:'100%',objectFit:'cover'}}/></div>)}
      <div style={{position:'absolute',inset:0,filter:'drop-shadow(0 12px 24px #0006)'}}>{person}</div></>;
  }else if(kind===6||kind===7){
    const scale=kind===6?interpolate(p,[0,.8],[1,.72],clamp):.82;
    picture=<><AbsoluteFill style={{background:kind===6?'#07161d':'#DEE8E5'}}/>
      <div style={{position:'absolute',inset:0,transform:`scale(${scale}) translateY(-50px)`,borderRadius:34,overflow:'hidden',boxShadow:'0 30px 90px #0008'}}>
        {normal}<div style={{position:'absolute',top:0,left:0,right:0,height:72,background:INK,display:'flex',alignItems:'center',gap:16,paddingLeft:25}}>{['#ff7777','#ffd466','#65dfad'].map(c=><span key={c} style={{width:17,height:17,borderRadius:'50%',background:c}}/>)}<span style={{color:'white',fontSize:24,marginLeft:25}}>特效预览.mp4</span></div>
      </div></>;graphics=false;
  }else if(kind===8){
    picture=<>{normal}<GraphicLayer kind={8} frame={frame} duration={n} width={W} height={H} title={title}/><AbsoluteFill>{person}</AbsoluteFill></>;graphics=false;
  }else if(kind===9){
    picture=<><AbsoluteFill style={{background:'linear-gradient(135deg,#08212E,#174D6A 45%,#47B4D0)'}}/>
      <div style={{position:'absolute',left:560,top:130,width:300,height:300,borderRadius:'50%',background:'#F2F8FA',boxShadow:'0 0 100px #b6f2ff'}}/>
      <div style={{position:'absolute',left:-200,top:1100,width:1400,height:800,background:'repeating-linear-gradient(90deg,transparent 0 88px,#47B4D055 90px 92px),repeating-linear-gradient(0deg,transparent 0 88px,#47B4D055 90px 92px)',transform:'perspective(600px) rotateX(55deg)'}}/>
      {person}</>;
  }else if(kind===11){
    picture=<><AbsoluteFill style={{background:INK}}/><svg style={{position:'absolute',width:0,height:0}}><defs><clipPath id="talking-text-mask" clipPathUnits="userSpaceOnUse"><text x={540} y={830} textAnchor="middle" fontSize={640} fontWeight={950}>剪</text><text x={540} y={1430} textAnchor="middle" fontSize={640} fontWeight={950}>辑</text></clipPath></defs></svg>
      <AbsoluteFill style={{clipPath:'url(#talking-text-mask)'}}>{normal}</AbsoluteFill></>;pip=true;graphics=false;
  }else if(kind===12){
    picture=<>{normal}<AbsoluteFill style={{filter:'drop-shadow(3px 0 0 white) drop-shadow(-3px 0 0 white) drop-shadow(0 3px 0 white)'}}>{person}</AbsoluteFill></>;
  }else if(kind===13){
    picture=<><AbsoluteFill style={{background:'#092E3C'}}/><GraphicLayer kind={13} frame={frame} duration={n} width={W} height={H} title={title}/>{person}</>;graphics=false;
  }else if(kind===14){
    const angle=-5+6*(1-(1-p)**3);
    picture=<><AbsoluteFill style={{background:'linear-gradient(130deg,#13202F,#283C4E)'}}/>
      <div style={{position:'absolute',left:207,top:110,width:666,height:1373,borderRadius:84,overflow:'hidden',transform:`rotate(${angle}deg)`,transformOrigin:'333px 680px'}}>{normal}</div></>;
  }else if(kind===15){
    // Both media layers keep the same full-canvas geometry; only the window is clipped.
    const sourceTransform:React.CSSProperties={position:'absolute',inset:0,transform:`translateY(${120-50*p}px) scale(.82)`,transformOrigin:'50% 50%'};
    picture=<><AbsoluteFill style={{background:'#07161d'}}/>
      <svg style={{position:'absolute',width:0,height:0}}><defs><clipPath id="talking-breakout-window" clipPathUnits="userSpaceOnUse"><rect x={130} y={650} width={820} height={840} rx={30} transform="rotate(-5 540 1070)"/></clipPath></defs></svg>
      <AbsoluteFill style={{clipPath:'url(#talking-breakout-window)'}}><div style={sourceTransform}>{normal}</div></AbsoluteFill>
      <div style={{position:'absolute',left:130,top:650,width:820,height:840,boxSizing:'border-box',border:'12px solid #F2F8FA',borderRadius:30,transform:'rotate(-5deg)',transformOrigin:'50% 50%'}}/>
      <div style={{...sourceTransform,filter:'drop-shadow(0 20px 28px #0007)'}}>{person}</div></>;
  }else if(kind===16){
    picture=<>{normal}<OrbitMotion radiusX={390} radiusY={130} centerY={40} periodInFrames={Math.max(30,n*1.5)} depth={.14} center={<div style={{width:W,height:H,transform:'translateY(192px)'}}>{person}</div>}>
      {['创作','剪辑','复用'].map((t,i)=><div key={t} style={{width:190,whiteSpace:'nowrap',textAlign:'center',padding:'20px 25px',background:i===1?'#F2F8FA':ACCENT,color:INK,border:'5px solid white',borderRadius:22,fontSize:55,fontWeight:900}}>{t}</div>)}
      </OrbitMotion></>;
  }else if(kind===17){
    const zoom=interpolate(p,[0,.9],[1,1.65],clamp);
    picture=<><div style={{position:'absolute',inset:0,transform:`scale(${zoom})`,transformOrigin:'59% 36%'}}>{normal}</div>
      <div style={{position:'absolute',left:205,top:390,width:670,height:820,border:'5px solid white',opacity:.85}}/>
      <div style={{position:'absolute',left:205,top:330,color:'white',fontSize:30}}>ZOOM {zoom.toFixed(1)}×</div></>;
  }
  return <AbsoluteFill style={{background:INK,overflow:'hidden'}}>
    {picture}
    {graphics?<GraphicLayer kind={kind} frame={frame-graphicStart} duration={n-graphicStart} width={W} height={H} title={title}/>:null}
    {pip?<Pip clip={clip} file={sourceFile}/>:null}
    <div style={{position:'absolute',left:48,top:38,padding:'10px 23px',background:'#153340D9',color:'white',borderRadius:30,fontSize:30,fontWeight:700,zIndex:45}}>{kind<=19?`${String(kind).padStart(2,'0')} / 19`:'免费领取'}</div>
    <Img src={staticFile('logo.png')} style={{position:'absolute',right:38,top:35,width:165,opacity:.12,zIndex:45}}/>
    <div style={{position:'absolute',left:65,right:65,top:1610,textAlign:'center',fontSize:kind===20?62:76,lineHeight:1.3,fontWeight:900,color:'white',textShadow:'0 4px 2px #153340,2px 0 #153340,-2px 0 #153340',zIndex:50}}>
      {kind===20?(p<.36?'留言「影片」':<>我把资料<br/><span style={{color:ACCENT}}>完全免费</span>发给你</>):title}
    </div>
    {kind===20?<div style={{position:'absolute',top:1260,left:170,right:170,padding:'25px 38px',borderRadius:60,background:'#F2F8FA',color:INK,fontWeight:900,fontSize:70,boxShadow:'0 15px 50px #0003',zIndex:40}}>影片 <span style={{float:'right',color:'#18A7CA'}}>➜</span></div>:null}
  </AbsoluteFill>;
};

export const Showcase:React.FC<ShowcaseProps>=({clips,sourceFile,alphaFile})=>{
  if(clips.length===0)throw new Error('Provide clips derived from a frozen authoritative timeline.');
  return <AbsoluteFill style={{fontFamily:'Noto Sans SC,sans-serif'}}>
    <style>{`@font-face{font-family:'Noto Sans SC';src:url('${staticFile('NotoSansSC.ttf')}') format('truetype');font-weight:100 950;}`}</style>
    {clips.map((clip,i)=><Sequence key={i} from={clip.fromFrame} durationInFrames={clip.durationInFrames}>
      <Scene clip={clip} sourceFile={sourceFile} alphaFile={alphaFile}/>
    </Sequence>)}
  </AbsoluteFill>;
};
