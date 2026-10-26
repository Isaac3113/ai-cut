/**
 * Adapted from RemotionUI, MIT (see upstream/LICENSE).
 * Pinned source and hashes: source-manifest.json.
 * This primitive arranges layers; it does not create a person's alpha mask.
 */
import type {CSSProperties, FC, ReactNode} from 'react';
import {Children} from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';

export type OrbitMotionProps = {
  children: ReactNode;
  radiusX?: number;
  radiusY?: number;
  periodInFrames?: number;
  phase?: number;
  tilt?: number;
  direction?: 'cw' | 'ccw';
  /** Centre coordinates in percent of the surrounding composition. */
  centerX?: number;
  centerY?: number;
  depth?: number;
  depthFade?: number;
  upright?: boolean;
  showPath?: boolean;
  pathColor?: string;
  /** Supply a transparent, source-synchronised person layer for real footage. */
  center?: ReactNode;
  style?: CSSProperties;
  className?: string;
};

export const OrbitMotion: FC<OrbitMotionProps> = ({
  children,
  radiusX = 210,
  radiusY = 78,
  periodInFrames = 120,
  phase = 0,
  tilt = -12,
  direction = 'cw',
  centerX = 50,
  centerY = 50,
  depth = 0.28,
  depthFade = 0.4,
  upright = true,
  showPath = false,
  pathColor = 'rgba(255,255,255,0.14)',
  center,
  style,
  className,
}) => {
  const frame = useCurrentFrame();
  const numeric = {radiusX, radiusY, periodInFrames, phase, tilt, centerX, centerY, depth, depthFade};
  for (const [name, value] of Object.entries(numeric)) {
    if (!Number.isFinite(value)) throw new Error(`OrbitMotion: ${name} must be finite.`);
  }
  if (radiusX < 0 || radiusY < 0 || periodInFrames < 2) {
    throw new Error('OrbitMotion requires non-negative radii and a period of at least two frames.');
  }
  if (depth < 0 || depth >= 1 || depthFade < 0 || depthFade > 1) {
    throw new Error('OrbitMotion requires 0 <= depth < 1 and 0 <= depthFade <= 1.');
  }

  const items = Children.toArray(children);
  const period = Math.round(periodInFrames);
  const turn = (frame / period) * (direction === 'cw' ? 1 : -1);

  return (
    <AbsoluteFill className={className} style={style}>
      <div style={{position: 'absolute', left: `${centerX}%`, top: `${centerY}%`, width: 0, height: 0, transform: `rotate(${tilt}deg)`}}>
        {showPath ? (
          <div style={{position: 'absolute', left: -radiusX, top: -radiusY, width: radiusX * 2, height: radiusY * 2, borderRadius: '50%', border: `1px solid ${pathColor}`}} />
        ) : null}
        {center ? (
          <div style={{position: 'absolute', transform: `translate(-50%, -50%) rotate(${-tilt}deg)`, zIndex: 10}}>
            {center}
          </div>
        ) : null}
        {items.map((item, index) => {
          const angle = (turn + index / Math.max(1, items.length)) * Math.PI * 2 + (phase * Math.PI) / 180;
          const near = Math.sin(angle);
          const scale = 1 + depth * near;
          const fade = 1 - depthFade * (1 - (near + 1) / 2);
          return (
            <div
              key={index}
              style={{
                position: 'absolute',
                left: Math.cos(angle) * radiusX,
                top: Math.sin(angle) * radiusY,
                transform: `translate(-50%, -50%) scale(${scale.toFixed(4)})${upright ? ` rotate(${-tilt}deg)` : ''}`,
                opacity: fade,
                zIndex: near >= 0 ? 20 : 1,
                willChange: 'transform',
              }}
            >
              {item}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
