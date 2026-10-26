import React from 'react';
import {Composition,getInputProps,registerRoot} from 'remotion';
import {Showcase,type ShowcaseProps} from './Showcase';
const Root:React.FC=()=>{
  const input=getInputProps<Partial<ShowcaseProps>>();
  const props:ShowcaseProps={clips:[],totalFrames:828,sourceFile:'source-cfr30.mp4',alphaFile:'person-alpha.mov',...input};
  return <Composition id="TalkingHeadShowcase" component={Showcase} width={1080} height={1920} fps={30} durationInFrames={props.totalFrames} defaultProps={props}/>;
};
registerRoot(Root);
