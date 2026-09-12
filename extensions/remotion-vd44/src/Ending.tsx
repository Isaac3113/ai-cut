import {AbsoluteFill,Img,staticFile,useCurrentFrame,interpolate} from 'remotion';
import {FontReady} from './Journey';
import {pop,clamp} from './scenes/Shared';
export const Ending=()=>{const f=useCurrentFrame();return <FontReady><AbsoluteFill style={{background:'#20201e',fontFamily:'Noto Sans SC',color:'#fff3cb',overflow:'hidden'}}>
 <div style={{position:'absolute',left:0,top:0,width:690,height:1080,background:'#ffd545',translate:`${interpolate(f,[0,12],[-690,0],clamp)}px 0px`}}/>
 <div style={{position:'absolute',left:200,top:260,width:510,height:510,borderRadius:'50%',border:'10px solid #fff3cb',overflow:'hidden',scale:pop(f,6),boxShadow:'15px 18px 0 #20201e'}}><Img src={staticFile('presenter.jpg')} style={{width:'100%',height:'100%',objectFit:'cover',objectPosition:'53% 40%'}}/></div>
 <div style={{position:'absolute',left:825,top:263,fontSize:27,fontWeight:700,letterSpacing:7,opacity:interpolate(f,[10,20],[0,1],clamp)}}>你的品牌 · 系统教学</div>
 <div style={{position:'absolute',left:810,top:365,fontSize:153,fontWeight:900,letterSpacing:7,color:'#ffd545',lineHeight:1.15,scale:pop(f,13),transformOrigin:'left center'}}>我们课程见</div>
 <div style={{position:'absolute',left:825,top:609,fontSize:47,fontWeight:700,translate:`0px ${32*(1-pop(f,24))}px`,opacity:Math.min(1,pop(f,24))}}>把客户流程，变成看得见的系统。</div>
 <div style={{position:'absolute',left:825,top:737,width:interpolate(f,[30,52],[0,570],clamp),height:8,background:'#ffd545'}}/>
 </AbsoluteFill></FontReady>};
