import {useCurrentFrame,interpolate} from 'remotion';
import {Shell,Customer,Note,Path,ink,yellow,pop,clamp} from './Shared';
export const NewLead=()=>{const f=useCurrentFrame();return <Shell step={1} title="客户进来，马上看见" english="NEW LEAD">
 <div style={{position:'absolute',left:90,top:340,display:'flex',flexDirection:'column',gap:20}}>{['Facebook','Instagram','TikTok'].map((s,i)=><div key={s} style={{background:ink,color:'#fff7db',padding:'16px 28px',borderRadius:16,fontSize:30,fontWeight:800,width:230,translate:`${-100*(1-pop(f,8+i*6))}px 0px`}}>{s}</div>)}</div>
 <Path d="M370 385C490 385 480 500 590 500M370 485H590M370 585C490 585 480 500 590 500" at={25}/>
 <div style={{position:'absolute',left:570,top:323,width:870,height:385,border:`3px solid ${ink}`,borderRadius:30,background:'#e5ddcb',scale:pop(f,20)}}><div style={{background:yellow,borderBottom:`3px solid ${ink}`,padding:'17px 30px',borderRadius:'27px 27px 0 0',fontSize:30,fontWeight:850,display:'flex',justifyContent:'space-between'}}><span>NEW LEAD</span><span>新客户</span></div><Customer x={interpolate(f,[38,66],[160,90],clamp)} y={124} scale={pop(f,35)}/></div>
 <div style={{position:'absolute',left:1500,top:350,fontSize:115,lineHeight:1,fontWeight:900,color:yellow,WebkitTextStroke:`3px ${ink}`,textShadow:`7px 8px 0 ${ink}`,scale:pop(f,160)}}>DAY 1</div><div style={{position:'absolute',left:1520,top:500,fontSize:32,fontWeight:800,opacity:interpolate(f,[169,176],[0,1],clamp)}}>进来的第一天</div>
 <Note text="自动记录所在阶段" at={85} x={670} y={728}/>
 </Shell>};
