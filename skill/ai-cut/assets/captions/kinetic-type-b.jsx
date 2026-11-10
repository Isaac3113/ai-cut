
// Motion mechanisms adapted from RenderComp WaveText and TextMaskReveal.
// SPDX-FileCopyrightText: 2026 Trimora Inc.
// SPDX-License-Identifier: MIT
// ChatCut caption_v1 adaptation: actual runtime text/timing, no canned dialogue.
const Component = ({item}) => {
 const localFrame=useCurrentFrame();
 const cfg=useVideoConfig();
 const fps=cfg.fps;
 const cap=useSpecialEffects().caption_v1;
 const p=item.props;
 if(!cap || cap.status!=='ready' || !cap.content.text)return <div style={{position:'absolute',inset:0}}/>;
 const abs=cap.active.frame;
 const time=localFrame/fps;
 const index=cap.sequence?cap.sequence.index:0;
 const mode=p.treatment==='mixed'?(index<7?'wave':index<14?'mask':'assemble'):p.treatment;
 const clamp=x=>Math.max(0,Math.min(1,x));
 const ease=x=>1-Math.pow(1-clamp(x),3);
 const words=[];
 cap.content.words.forEach(w=>{
  const prev=words[words.length-1];
  if(prev && w.wordGroupId && prev.wordGroupId===w.wordGroupId){
   prev.text+=w.text;prev.end=w.timelineEndFrame;prev.emphasis=prev.emphasis||w.emphasis;
  }else words.push({text:w.text,start:w.timelineStartFrame,end:w.timelineEndFrame,emphasis:w.emphasis===true,id:w.id,wordGroupId:w.wordGroupId});
 });
 if(!words.length)words.push({text:cap.content.text,start:cap.timing.startFrame,end:cap.timing.endFrame,emphasis:false,id:cap.cue.id});
 const width=item.width;
 const height=item.height;
 const font=p.fontFamily;
 const measure=(txt,size)=>measureText({text:txt,fontFamily:font,fontSize:size,fontWeight:900}).width;
 const makeRows=size=>{
  const rows=[[]];let used=0;
  words.forEach(w=>{
   const ww=measure(w.text,size)+size*.018;
   if(rows[rows.length-1].length && used+ww>width-58){rows.push([]);used=0;}
   rows[rows.length-1].push({...w,width:ww});used+=ww;
  });
  return rows;
 };
 let size=p.fontSize;
 let rows=makeRows(size);
 while((rows.length>2||rows.length*size*1.28>height-30)&&size>56){size-=2;rows=makeRows(size);}
 const rowHeight=size*1.28;
 const rootStyle={position:'absolute',inset:0,display:'flex',flexDirection:'column',justifyContent:'center',gap:size*.06,fontFamily:font,fontWeight:900,color:p.textColor,pointerEvents:'none',overflow:'visible'};
 const shadow='2px 2px 0 #16383D,-2px -2px 0 #16383D,2px -2px 0 #16383D,-2px 2px 0 #16383D,0px 5px 0 #16383D';
 let ordinal=0;
 const output=rows.map((row,ri)=>{
  const rowWidth=row.reduce((s,w)=>s+w.width,0);
  const rowStyle={height:rowHeight,display:'flex',alignItems:'center',justifyContent:mode==='mask'?'flex-start':'center',paddingLeft:mode==='mask'?22+ri*22:0,whiteSpace:'pre',overflow:'visible'};
  return <div key={ri} style={rowStyle}>{row.map(w=>{
   const english=/^[A-Za-z0-9]+$/.test(w.text.trim());
   const letters=english?[w.text]:Array.from(w.text);
   const tokenBox={display:'inline-flex',alignItems:'center',whiteSpace:'pre',height:rowHeight,marginRight:size*.018};
   return <span key={w.id} style={tokenBox}>{letters.map((ch,ci)=>{
    const n=ordinal++;
    const stagger=english?0:Math.min(fps*.026,Math.max(0,w.end-w.start)/Math.max(1,letters.length))*ci;
    const begin=w.start+stagger;
    const age=(abs-begin)/fps;
    const enter=ease(age/.16);
    const live=age>=0;
    const wave=Math.sin(time*3.4+n*.61)*p.motionAmount*.42;
    const drift=Math.sin(time*2.3+n*.43)*p.motionAmount*.16;
    const settle=live?spring({frame:Math.max(0,(age)*fps),fps,config:{damping:15,stiffness:220,mass:.65}}):0;
    const x=mode==='mask'?(1-enter)*-size*.5+drift:mode==='assemble'?(1-settle)*(n%2?-size*.55:size*.55)+drift:drift;
    const y=mode==='wave'?(1-enter)*size*.5+wave:mode==='assemble'?(1-settle)*size*.6+wave*.55:wave*.35;
    const rot=mode==='assemble'?(1-settle)*(n%2?-14:14)+Math.sin(time*2.1+n)*.6:Math.sin(time*1.8+n*.45)*.55;
    const scale=mode==='assemble'?.65+.35*settle:1+Math.sin(time*2.6+n*.42)*.008;
    const marked=w.emphasis || /^[A-Za-z]/.test(ch);
    const letterStyle={position:'relative',display:'inline-block',fontSize:size,color:marked?p.accent:p.textColor,textShadow:shadow,opacity:live?1:0,transform:'translate('+x+'px,'+y+'px) rotate('+rot+'deg) scale('+scale+')',transformOrigin:'50% 80%',clipPath:mode==='mask'?'inset(-12% '+((1-enter)*100)+'% -20% -12%)':undefined,lineHeight:1.08};
    const trailStyle={position:'absolute',left:0,top:0,opacity:Math.max(0,1-enter)*.35,transform:'translate('+((1-enter)*-12)+'px,'+((1-enter)*5)+'px)',color:p.accent};
    return <span key={ci} style={letterStyle}>{ch}{mode==='assemble'&&<span aria-hidden="true" style={trailStyle}>{ch}</span>}</span>;
   })}</span>;
  })}</div>;
 });
 return <div style={rootStyle}>{output}</div>;
};
