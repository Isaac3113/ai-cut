import React from 'react';
import {AbsoluteFill, Composition, Folder, staticFile} from 'remotion';
import {RemotionRoot as RenderCompRoot} from '../vendor/rendercomp/Root';
import {BarChartAnim, defaultBarChartAnimProps, type BarChartAnimProps} from '../vendor/rendercomp/components/bar-chart-anim/BarChartAnim';
import {LowerThirdGlassCard, defaultLowerThirdGlassCardProps, type LowerThirdGlassCardProps} from '../vendor/rendercomp/components/lower-third-glass-card/LowerThirdGlassCard';
import {SocialReel, defaultSocialReelProps, type SocialReelProps} from '../vendor/rendercomp/components/social-reel/SocialReel';
import {OrbitMotionDemo, TextMaskVideoDemo} from './remotion-ui';
import {orbitMotionDemoDefaults, textMaskVideoDemoDefaults, type OrbitMotionDemoProps, type TextMaskVideoDemoProps} from './remotion-ui/Demos';

const LocalFont: React.FC<{children: React.ReactNode}> = ({children}) => (
  <AbsoluteFill>
    <style>{`@font-face {font-family: TemplateNoto; src: url('${staticFile('NotoSansSC.ttf')}') format('truetype'); font-weight: 100 900;} * {font-family: TemplateNoto, sans-serif !important;}`}</style>
    {children}
  </AbsoluteFill>
);

const ChineseBar: React.FC<BarChartAnimProps> = (props) => <LocalFont><BarChartAnim {...props}/></LocalFont>;
const ChineseGlass: React.FC<LowerThirdGlassCardProps> = (props) => <LocalFont><LowerThirdGlassCard {...props}/></LocalFont>;
const ChinesePlayer: React.FC<SocialReelProps> = (props) => <LocalFont><SocialReel {...props}/></LocalFont>;
const LocalOrbit: React.FC<OrbitMotionDemoProps> = (props) => <LocalFont><OrbitMotionDemo {...props}/></LocalFont>;
const LocalTextMask: React.FC<TextMaskVideoDemoProps> = (props) => <LocalFont><TextMaskVideoDemo {...props}/></LocalFont>;

export const TemplateLibraryRoot: React.FC = () => (
  <>
    <Folder name="RenderComp-50"><RenderCompRoot/></Folder>
    <Folder name="RemotionUI-Adapted">
      <Composition id="library-orbit" component={LocalOrbit} durationInFrames={180} fps={30} width={1080} height={1080} defaultProps={orbitMotionDemoDefaults}/>
      <Composition id="library-text-mask" component={LocalTextMask} durationInFrames={120} fps={30} width={1080} height={1080} defaultProps={textMaskVideoDemoDefaults}/>
    </Folder>
    <Folder name="Chinese-Examples">
      <Composition id="library-bar-zh" component={ChineseBar} durationInFrames={150} fps={30} width={1920} height={1080}
        defaultProps={{...defaultBarChartAnimProps, title: '长条成长｜模板演示', subtitle: '以下为动画测试数值，不代表业务结果', bars: [{label: '项目一', value: 40}, {label: '项目二', value: 80}], accentColor: '#06b6d4'}}/>
      <Composition id="library-glass-zh" component={ChineseGlass} durationInFrames={120} fps={30} width={1920} height={1080}
        defaultProps={{...defaultLowerThirdGlassCardProps, nameText: '玻璃卡片', titleText: '文字、颜色可以替换'}}/>
      <Composition id="library-player-zh" component={ChinesePlayer} durationInFrames={150} fps={30} width={1920} height={1080}
        defaultProps={{...defaultSocialReelProps, brandName: '界面示意', handle: '@demo', headline: '手机画面', headlineAccent: '模板演示', secondCopy: '后续替换\n自己的素材', infoLines: ['此处为图形示意', '尚未接入真人视频'], ctaText: '参数可以替换', caption: '模板预览', likeCount: '示意'}}/>
    </Folder>
  </>
);
