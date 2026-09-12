import React,{useEffect,useState} from 'react';
import {TransitionSeries} from '@remotion/transitions';
import {continueRender,delayRender,staticFile} from 'remotion';
import {NewLead} from './scenes/NewLead';
import {FollowUp} from './scenes/FollowUp';
import {NoReply} from './scenes/NoReply';
import {Register} from './scenes/Register';
export const FontReady:React.FC<{children:React.ReactNode}>=({children})=>{const [handle]=useState(()=>delayRender('Load local licensed Chinese font'));useEffect(()=>{const font=new FontFace('Noto Sans SC',`url(${staticFile('NotoSansSC.ttf')})`,{weight:'100 900'});font.load().then(x=>{document.fonts.add(x);continueRender(handle)}).catch(e=>{throw e});},[handle]);return <>{children}</>};
export const Journey=()=><FontReady><TransitionSeries>
 <TransitionSeries.Sequence durationInFrames={241} name="New Lead"><NewLead/></TransitionSeries.Sequence>
 <TransitionSeries.Sequence durationInFrames={211} name="Follow up"><FollowUp/></TransitionSeries.Sequence>
 <TransitionSeries.Sequence durationInFrames={255} name="No reply"><NoReply/></TransitionSeries.Sequence>
 <TransitionSeries.Sequence durationInFrames={131} name="Register"><Register/></TransitionSeries.Sequence>
</TransitionSeries></FontReady>;
