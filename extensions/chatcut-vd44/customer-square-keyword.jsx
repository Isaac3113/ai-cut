const Component=({item})=>{
 const localFrame=useCurrentFrame();const {durationInFrames}=useVideoConfig();const f=localFrame*74/(durationInFrames-1);const props=item.props;
 const s=spring({frame:f,fps:30,config:{damping:16,stiffness:220,mass:.55}});
 const exit=interpolate(f,[67,74],[1,0],{extrapolateLeft:"clamp",extrapolateRight:"clamp"});
 const rootStyle={position:"absolute",inset:0,backgroundColor:"transparent",fontFamily:props.fontFamily,color:props.accentColor,opacity:exit,overflow:"visible"};
 const rowStyle={display:"flex",justifyContent:"center",alignItems:"center",gap:12,height:"100%",fontSize:92,fontWeight:900,letterSpacing:2,lineHeight:1.1,WebkitTextStroke:"2px #25231f",paintOrder:"stroke fill",textShadow:"3px 4px 0 #25231f",transform:"scale("+s+") rotate(-2deg)"};
 const tagScale=spring({frame:f-9,fps:30,config:{damping:16,stiffness:180,mass:.65}});
 const tagStyle={display:"inline-block",color:props.secondaryColor,transform:"scale("+tagScale+")"};
 return <div style={rootStyle}><div style={rowStyle}><span>{props.text}</span><span style={tagStyle}>{props.tail}</span></div></div>;
};