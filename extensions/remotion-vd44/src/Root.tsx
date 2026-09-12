import {Composition} from 'remotion';
import {Journey} from './Journey';
import {Ending} from './Ending';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="CustomerJourney" component={Journey} durationInFrames={838} fps={30} width={1920} height={1080}/>
      <Composition id="PresenterEnding" component={Ending} durationInFrames={90} fps={30} width={1920} height={1080}/>
    </>
  );
};
