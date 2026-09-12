import {useCurrentFrame} from 'remotion';
import {Shell,Customer,Note,Icon,Path,ink,yellow,pop} from './Shared';
export const Register=()=>{const f=useCurrentFrame();return <Shell step={4} title="回复并报名，再进下一步" english="REGISTER">
 <div style={{position:'absolute',left:110,top:340,fontSize:30,fontWeight:800}}>条件满足后，状态才变化</div><div style={{position:'absolute',left:110,top:410,width:480,padding:30,background:'#fffefa',border:`3px solid ${ink}`,borderRadius:'28px 28px 28px 0',scale:pop(f,12),boxShadow:'8px 8px 0 #d8cfbd'}}><div style={{fontSize:22,color:'#877f70',marginBottom:12}}>客户回复 · 示例</div><div style={{fontSize:49,fontWeight:850}}>我想报名</div></div>
 <Path d="M650 510h310l-25-22m25 22-25 22" at={59} length={400}/>
 <div style={{position:'absolute',left:1020,top:325,width:705,height:420,border:`3px solid ${ink}`,borderRadius:28,background:yellow,scale:pop(f,91),boxShadow:`12px 12px 0 ${ink}`}}><div style={{display:'flex',alignItems:'center',gap:24,padding:'25px 35px',fontSize:46,fontWeight:900}}><Icon kind="check" size={70}/><span>REGISTER</span></div><Customer x={47} y={170}/></div><Note text="回复 + 报名" at={36} x={260} y={690}/>
 </Shell>};
