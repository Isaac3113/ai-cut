import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame} from 'remotion';
export const ink='#20201e', yellow='#ffd545', red='#e65245';
export const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
export const pop=(f:number,d=0)=>spring({frame:f-d,fps:30,config:{damping:17,stiffness:175,mass:.65}});
export const Icon:React.FC<{kind:'user'|'message'|'clock'|'check';size?:number}>=({kind,size=64})=><svg width={size} height={size} viewBox="0 0 64 64" fill="none" stroke={ink} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
 {kind==='user'&&<><circle cx="32" cy="22" r="11"/><path d="M12 57c0-23 40-23 40 0"/></>}
 {kind==='message'&&<><path d="M9 10h46v34H29L15 55V44H9Z"/><path d="M19 22h26M19 32h17"/></>}
 {kind==='clock'&&<><circle cx="32" cy="34" r="23"/><path d="M32 19v16l11 7M24 3h16M32 3v8"/></>}
 {kind==='check'&&<><circle cx="32" cy="32" r="26"/><path d="m17 32 10 10 21-22"/></>}
</svg>;
export const Shell:React.FC<{step:number;title:string;english:string;children:React.ReactNode;tone?:string}>=({step,title,english,children,tone=yellow})=>{const f=useCurrentFrame();return <AbsoluteFill style={{background:'#f5f0e6',fontFamily:'Noto Sans SC',color:ink,overflow:'hidden'}}>
 <div style={{position:'absolute',inset:0,backgroundImage:'radial-gradient(#d7d0bf 1.5px, transparent 1.5px)',backgroundSize:'28px 28px',opacity:.45}}/>
 <div style={{position:'absolute',top:68,left:92,fontSize:23,fontWeight:700,letterSpacing:6}}>CUSTOMER JOURNEY</div>
 <div style={{position:'absolute',top:105,left:86,display:'flex',alignItems:'center',gap:25,translate:`0px ${32*(1-pop(f))}px`,opacity:Math.min(1,pop(f))}}><div style={{fontSize:108,fontWeight:900,lineHeight:1.2,color:tone,WebkitTextStroke:`3px ${ink}`,textShadow:'5px 6px 0 #20201e'}}>0{step}</div><div><div style={{fontSize:75,fontWeight:900,lineHeight:1.25}}>{title}</div><div style={{fontSize:28,fontWeight:650,letterSpacing:3,marginTop:8}}>{english}</div></div></div>
 <div style={{position:'absolute',top:94,right:95,fontSize:23,padding:'9px 15px',border:'2px solid #d4ccbb',borderRadius:6}}>流程示意</div>{children}
 <div style={{position:'absolute',left:100,top:835,display:'flex',gap:10}}>{[1,2,3,4].map(n=><div key={n} style={{width:n===step?130:54,height:7,borderRadius:8,background:n===step?tone:'#d5cdbf'}}/>)}</div>
 <div style={{position:'absolute',left:0,right:0,bottom:0,height:175,background:ink}}/>
 </AbsoluteFill>};
export const Customer:React.FC<{x:number;y:number;scale?:number;accent?:string}>=({x,y,scale=1,accent=yellow})=><div style={{position:'absolute',left:x,top:y,width:460,background:'#fffefa',border:`3px solid ${ink}`,borderRadius:22,padding:30,boxShadow:`9px 10px 0 ${ink}`,scale,display:'flex',alignItems:'center',gap:26}}><div style={{width:84,height:84,borderRadius:'50%',background:accent,display:'grid',placeItems:'center'}}><Icon kind="user" size={54}/></div><div><div style={{fontSize:37,fontWeight:850}}>演示客户</div><div style={{fontSize:24,color:'#797566',marginTop:7}}>客户动态 · 示例</div></div></div>;
export const Note:React.FC<{text:string;at:number;x:number;y:number;accent?:string}>=({text,at,x,y,accent=yellow})=>{const f=useCurrentFrame();return <div style={{position:'absolute',left:x,top:y,fontSize:48,fontWeight:900,background:accent,padding:'13px 30px',rotate:'-3deg',border:`3px solid ${ink}`,boxShadow:`6px 7px 0 ${ink}`,scale:pop(f,at)}}>{text}</div>};
export const Path:React.FC<{d:string;at:number;length?:number}>=({d,at,length=1000})=>{const f=useCurrentFrame();return <svg width="1920" height="900" style={{position:'absolute',inset:0}}><path d={d} fill="none" stroke={ink} strokeWidth={6} strokeLinecap="round" strokeDasharray={length} strokeDashoffset={interpolate(f,[at,at+24],[length,0],clamp)}/></svg>};
