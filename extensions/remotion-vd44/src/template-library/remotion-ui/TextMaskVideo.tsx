/**
 * Adapted from RemotionUI, MIT (see upstream/LICENSE).
 * Pinned source and hashes: source-manifest.json.
 * Website aliases were replaced by a small, explicit frame-timing contract.
 */
import {useId} from 'react';
import type {CSSProperties, FC} from 'react';
import {Easing, Img, OffthreadVideo, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

export type TextMaskMedia = 'video' | 'image' | 'gradient';
export type TextMaskVideoProps = {
  text: string;
  /** Use an authorised local asset, normally resolved with staticFile(). */
  src?: string;
  media?: TextMaskMedia;
  gradient?: string;
  width?: number;
  height?: number;
  drift?: number;
  zoom?: number;
  reveal?: 'left' | 'right' | 'up' | 'down' | 'none';
  fontSize?: number;
  fontFamily?: string;
  fontWeight?: number | string;
  letterSpacing?: number;
  lineHeight?: number;
  startFrom?: number;
  mediaFilter?: string;
  /** Local Sequence frame counts; these do not change the source playback rate. */
  enterInFrames?: number;
  delayInFrames?: number;
  exit?: boolean;
  exitInFrames?: number;
  exitAtInFrames?: number;
  style?: CSSProperties;
  className?: string;
};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const revealInset = {
  left: (hidden: number) => `inset(0 ${hidden}% 0 0)`,
  right: (hidden: number) => `inset(0 0 0 ${hidden}%)`,
  up: (hidden: number) => `inset(0 0 ${hidden}% 0)`,
  down: (hidden: number) => `inset(${hidden}% 0 0 0)`,
};

export const TextMaskVideo: FC<TextMaskVideoProps> = ({
  text,
  src,
  media,
  gradient = 'linear-gradient(115deg, #47B4D0 0%, #F2F8FA 45%, #18A7CA 100%)',
  width: widthProp,
  height: heightProp,
  drift = 26,
  zoom = 0.12,
  reveal = 'left',
  fontSize: fontSizeProp,
  fontFamily,
  fontWeight = 800,
  letterSpacing = 0,
  lineHeight = 0.98,
  startFrom,
  mediaFilter,
  enterInFrames = 24,
  delayInFrames = 0,
  exit = false,
  exitInFrames = 14,
  exitAtInFrames,
  style,
  className,
}) => {
  const frame = useCurrentFrame();
  const {width: videoWidth, fps, durationInFrames} = useVideoConfig();
  const clipId = `mask-${useId().replace(/[^a-zA-Z0-9]/g, '')}`;
  const kind = media ?? (src ? 'video' : 'gradient');
  const fontSize = fontSizeProp ?? Math.round(150 * (videoWidth / 1080));
  const lines = text.split(/\r?\n/);
  const width = widthProp ?? Math.round(fontSize * 6.2);
  const height = heightProp ?? Math.round(fontSize * lineHeight * lines.length * 1.25);
  const numeric = {fontSize, width, height, drift, zoom, lineHeight, letterSpacing, enterInFrames, delayInFrames, exitInFrames};
  for (const [name, value] of Object.entries(numeric)) {
    if (!Number.isFinite(value)) throw new Error(`TextMaskVideo: ${name} must be finite.`);
  }
  if (!text.trim() || fontSize <= 0 || width <= 0 || height <= 0 || lineHeight <= 0) {
    throw new Error('TextMaskVideo requires non-empty text and positive layout dimensions.');
  }
  if (kind !== 'gradient' && !src) throw new Error(`TextMaskVideo requires src for media=${kind}.`);
  if (enterInFrames < 1 || delayInFrames < 0 || exitInFrames < 1 || zoom < 0) {
    throw new Error('TextMaskVideo requires positive entrance/exit lengths and non-negative delay/zoom.');
  }
  if (startFrom !== undefined && (!Number.isInteger(startFrom) || startFrom < 0)) {
    throw new Error('TextMaskVideo: startFrom must be a non-negative source frame.');
  }

  const enterFrames = Math.round(enterInFrames);
  const delay = Math.round(delayInFrames);
  const exitFrames = Math.round(exitInFrames);
  const wantsExit = exit || exitAtInFrames !== undefined;
  const exitStart = exitAtInFrames ?? durationInFrames - exitFrames;
  if (wantsExit && (!Number.isInteger(exitStart) || exitStart < delay + enterFrames || exitStart + exitFrames > durationInFrames)) {
    throw new Error('TextMaskVideo: entrance and exit must fit inside the surrounding Sequence without overlap.');
  }

  const enter = interpolate(frame, [delay, delay + enterFrames], [0, 1], {...clamp, easing: Easing.bezier(0.33, 1, 0.68, 1)});
  const enterOpacity = interpolate(frame, [delay, delay + Math.max(1, Math.round(enterFrames * 0.55))], [0, 1], clamp);
  const exitProgress = !wantsExit ? 0 : exitFrames === 1 ? (frame >= exitStart ? 1 : 0) : interpolate(frame, [exitStart, exitStart + exitFrames - 1], [0, 1], {...clamp, easing: Easing.in(Easing.cubic)});
  const revealed = reveal === 'none' ? 1 : enter * (1 - exitProgress);
  const hidden = Math.max(0, Math.min(100, (1 - revealed) * 100));
  const pan = Math.sin((frame / fps) * 0.62) * drift;
  const scale = 1 + zoom * (0.5 + 0.5 * Math.sin((frame / fps) * 0.44 + 1.1));
  const blockHeight = (lines.length - 1) * fontSize * lineHeight;
  const firstY = height / 2 - blockHeight / 2;

  return (
    <div className={className} style={{position: 'relative', width, height, opacity: enterOpacity * (1 - exitProgress), ...style}}>
      <svg width={0} height={0} style={{position: 'absolute'}} aria-hidden>
        <defs>
          <clipPath id={clipId} clipPathUnits="userSpaceOnUse">
            {lines.map((line, index) => (
              <text key={`${line}-${index}`} x={width / 2} y={firstY + index * fontSize * lineHeight} textAnchor="middle" dominantBaseline="central" fontSize={fontSize} fontWeight={fontWeight} letterSpacing={letterSpacing} {...(fontFamily ? {fontFamily} : {})}>
                {line}
              </text>
            ))}
          </clipPath>
        </defs>
      </svg>
      <div style={{position: 'absolute', inset: 0, clipPath: `url(#${clipId})`, WebkitClipPath: `url(#${clipId})`}}>
        <div style={{position: 'absolute', inset: 0, ...(reveal === 'none' ? null : {clipPath: revealInset[reveal](hidden), WebkitClipPath: revealInset[reveal](hidden)})}}>
          <div style={{position: 'absolute', inset: '-8%', transform: `translateX(${(-pan).toFixed(2)}px) scale(${scale.toFixed(4)})`, transformOrigin: 'center center', ...(mediaFilter ? {filter: mediaFilter} : null)}}>
            {kind === 'video' && src ? (
              <OffthreadVideo src={src} startFrom={startFrom} muted pauseWhenBuffering style={{width: '100%', height: '100%', objectFit: 'cover'}} />
            ) : kind === 'image' && src ? (
              <Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
            ) : (
              <div style={{width: '100%', height: '100%', background: gradient}} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
