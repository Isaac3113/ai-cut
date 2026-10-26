import type {FC} from 'react';
import {AbsoluteFill, staticFile, useVideoConfig} from 'remotion';
import {OrbitMotion} from './OrbitMotion';
import {TextMaskVideo} from './TextMaskVideo';
import type {TextMaskMedia} from './TextMaskVideo';

export type OrbitMotionDemoProps = {
  labels?: string[];
  title?: string;
  note?: string;
  periodInFrames?: number;
};

export const orbitMotionDemoDefaults = {
  labels: ['IDEA', 'CREATE', 'REUSE'],
  title: 'Words in front. Words behind.',
  note: 'VECTOR DEMO / PERSON ALPHA NOT PROVIDED',
  periodInFrames: 180,
};

export type TextMaskVideoDemoProps = {
  text?: string;
  title?: string;
  note?: string;
  media?: TextMaskMedia;
  /** A public-relative asset, or an already resolved authorised media URL. */
  src?: string;
  gradient?: string;
  fontFamily?: string;
};

export const textMaskVideoDemoDefaults = {
  text: 'CREATE\nMORE',
  title: '11 / MEDIA THROUGH TYPE',
  note: 'SYNTHETIC GRADIENT / VIDEO INPUT NOT EXERCISED',
  media: 'gradient' as TextMaskMedia,
  gradient: 'linear-gradient(115deg, #18A7CA 0%, #F2F8FA 42%, #47B4D0 62%, #7CD9CA 100%)',
  fontFamily: 'Arial, sans-serif',
};

/** Original vector placeholder: not an identity, portrait or segmentation result. */
const Illustration: FC<{scale: number}> = ({scale}) => (
  <svg width={180 * scale} height={270 * scale} viewBox="0 0 180 270" aria-label="Geometric demonstration figure">
    <circle cx="90" cy="67" r="45" fill="#F2F8FA" />
    <path d="M15 267V176C15 134 165 134 165 176V267Z" fill="#47B4D0" />
    <path d="M58 65H74M106 65H122M70 88Q90 103 110 88" fill="none" stroke="#153340" strokeWidth="6" strokeLinecap="round" />
  </svg>
);

/** Suggested registration: 1080x1080, 30 fps, 180 frames; no private assets. */
export const OrbitMotionDemo: FC<OrbitMotionDemoProps> = ({
  labels = orbitMotionDemoDefaults.labels,
  title = orbitMotionDemoDefaults.title,
  note = orbitMotionDemoDefaults.note,
  periodInFrames = orbitMotionDemoDefaults.periodInFrames,
}) => {
  const {width, height} = useVideoConfig();
  const unit = Math.min(width, height) / 1080;
  if (!Array.isArray(labels) || labels.length === 0 || labels.some((label) => typeof label !== 'string' || !label.trim())) {
    throw new Error('OrbitMotionDemo requires labels to be a non-empty array of non-empty strings.');
  }
  return (
    <AbsoluteFill style={{background: '#102B36', color: '#F2F8FA', fontFamily: 'Arial, sans-serif'}}>
      <div style={{position: 'absolute', left: width * 0.08, top: height * 0.08, fontSize: 22 * unit, letterSpacing: 4}}>16 / ORBIT MOTION</div>
      <div style={{position: 'absolute', left: width * 0.08, top: height * 0.14, fontSize: 52 * unit, fontWeight: 800}}>{title}</div>
      <OrbitMotion radiusX={290 * unit} radiusY={84 * unit} periodInFrames={periodInFrames} tilt={-9} depth={0.16} centerY={52} showPath pathColor="#47B4D055" center={<Illustration scale={unit} />}>
        {labels.map((label, index) => (
          <div key={`${index}-${label}`} style={{padding: `${16 * unit}px ${22 * unit}px`, borderRadius: 14 * unit, background: index === 1 ? '#F2F8FA' : '#47B4D0', color: '#102B36', fontWeight: 900, fontSize: 30 * unit, whiteSpace: 'nowrap', boxShadow: '0 8px 25px #0003'}}>{label}</div>
        ))}
      </OrbitMotion>
      <div style={{position: 'absolute', left: width * 0.08, bottom: height * 0.12, fontSize: 22 * unit, color: '#98BCCB'}}>{note}</div>
    </AbsoluteFill>
  );
};

/** Suggested registration: 1080x1080, 30 fps, 120 frames; synthetic gradient. */
export const TextMaskVideoDemo: FC<TextMaskVideoDemoProps> = ({
  text = textMaskVideoDemoDefaults.text,
  title = textMaskVideoDemoDefaults.title,
  note = textMaskVideoDemoDefaults.note,
  media = textMaskVideoDemoDefaults.media,
  src,
  gradient = textMaskVideoDemoDefaults.gradient,
  fontFamily = textMaskVideoDemoDefaults.fontFamily,
}) => {
  const {width, height} = useVideoConfig();
  const unit = Math.min(width, height) / 1080;
  if (!['gradient', 'video', 'image'].includes(media)) throw new Error('TextMaskVideoDemo: media must be gradient, video or image.');
  if (src !== undefined && typeof src !== 'string') throw new Error('TextMaskVideoDemo: src must be a string.');
  const mediaSource = src?.trim();
  if (media !== 'gradient' && !mediaSource) throw new Error(`TextMaskVideoDemo requires src for media=${media}.`);
  if (mediaSource && /^[A-Za-z]:[\\/]/.test(mediaSource)) throw new Error('TextMaskVideoDemo: use a public-relative asset or resolved media URL, not a Windows filesystem path.');
  const resolvedSource = !mediaSource ? undefined : /^(?:https?:|data:|blob:|\/)/.test(mediaSource) ? mediaSource : staticFile(mediaSource);
  const displayNote = media !== 'gradient' && note === textMaskVideoDemoDefaults.note ? `${media.toUpperCase()} SOURCE / MASKED TYPE DEMO` : note;
  return (
    <AbsoluteFill style={{background: '#102B36', color: '#F2F8FA', fontFamily}}>
      <div style={{position: 'absolute', left: width * 0.08, top: height * 0.08, fontSize: 22 * unit, letterSpacing: 4}}>{title}</div>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <TextMaskVideo text={text} width={840 * unit} height={430 * unit} fontSize={190 * unit} fontFamily={fontFamily} fontWeight={900} media={media} src={resolvedSource} gradient={gradient} drift={110 * unit} zoom={0.35} enterInFrames={24} exit exitInFrames={14} />
      </AbsoluteFill>
      <div style={{position: 'absolute', left: width * 0.08, bottom: height * 0.12, fontSize: 22 * unit, color: '#98BCCB'}}>{displayNote}</div>
    </AbsoluteFill>
  );
};
