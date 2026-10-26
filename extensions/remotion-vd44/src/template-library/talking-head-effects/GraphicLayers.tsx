import React from 'react';

export type GraphicLayerProps = {
  kind: number;
  frame: number;
  duration: number;
  width: number;
  height: number;
  title: string;
  accent?: string;
};

const INK = '#153340';
const WHITE = '#F2F8FA';
const BASE_WIDTH = 1080;
const BASE_HEIGHT = 1920;
const FONT = '"Noto Sans SC", "Microsoft YaHei", sans-serif';
const SUPPORTED = new Set([1, 2, 7, 8, 10, 11, 12, 13, 14, 18, 19]);
const clamp = (value: number) => Math.min(1, Math.max(0, value));
const smooth = (value: number) => {
  const x = clamp(value);
  return x * x * (3 - 2 * x);
};
const out = (value: number) => 1 - (1 - clamp(value)) ** 3;
const short = (value: string, max: number) => Array.from(value).slice(0, max).join('');

const Letter: React.FC<React.SVGProps<SVGTextElement>> = ({children, ...props}) => (
  <text fill={WHITE} fontFamily={FONT} fontWeight={700} {...props}>{children}</text>
);

const Panel: React.FC<{x: number; y: number; width: number; height: number; accent: string}> = ({accent, ...props}) => (
  <>
    <rect {...props} rx={36} fill={INK} fillOpacity={0.93} stroke={WHITE} strokeOpacity={0.28} strokeWidth={2}/>
    <rect x={props.x + 24} y={props.y + 22} width={8} height={34} rx={4} fill={accent}/>
  </>
);

/** Original vector stickers, with no downloaded brand marks or media. */
const Sticker: React.FC<{index: number; color: string}> = ({index, color}) => {
  const line = {fill: 'none', stroke: color, strokeWidth: 7, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  if (index === 0) return <path d="M0 -37L10 -10L37 0L10 10L0 37L-10 10L-37 0L-10 -10Z" {...line}/>;
  if (index === 1) return <><rect x={-35} y={-27} width={70} height={54} rx={9} {...line}/><path d="M-10 -14L17 0L-10 14Z" fill={color}/></>;
  if (index === 2) return <path d="M-23 -35L29 5L3 10L-8 35L-23 -35Z" {...line}/>;
  if (index === 3) return <><rect x={-35} y={-29} width={70} height={52} rx={14} {...line}/><path d="M-14 24L-22 38L4 24M-18 -4H18M-18 9H8" {...line}/></>;
  return <><path d="M-31 -14V-31H-14M14 -31H31V-14M31 14V31H14M-14 31H-31V14" {...line}/><circle r={11} {...line}/></>;
};

/**
 * Transparent, local-frame-driven graphics for a reference-effects review.
 * Does not cut footage, isolate a person, produce audio, or own a timeline.
 * Layout uses a 1080x1920 design canvas; y >= 1570 is reserved for captions.
 */
export const GraphicLayer: React.FC<GraphicLayerProps> = ({kind, frame, duration, width, height, title, accent = '#47B4D0'}) => {
  if (!SUPPORTED.has(kind)) return null;
  if (![frame, duration, width, height].every(Number.isFinite) || duration <= 0 || width <= 0 || height <= 0) {
    throw new Error('GraphicLayer requires a finite frame and positive duration/width/height.');
  }
  if (frame < 0 || frame >= duration) return null;

  const progress = clamp(frame / Math.max(1, duration - 1));
  const enter = out(progress / 0.18);
  const opacity = smooth(progress / 0.1) * (1 - smooth((progress - 0.88) / 0.12));
  const scale = Math.min(width / BASE_WIDTH, height / BASE_HEIGHT);
  const originX = (width - BASE_WIDTH * scale) / 2;
  const originY = (height - BASE_HEIGHT * scale) / 2;
  const key = `${kind}-${width}-${height}-${Array.from(title).reduce((sum, char) => (sum * 31 + char.codePointAt(0)!) >>> 0, 0)}`;
  const svgId = `talk-graphic-${key}`;
  const label = short(title.trim() || '剪辑特效', 12);
  const content: React.CSSProperties = {
    position: 'absolute', left: originX, top: originY, width: BASE_WIDTH, height: BASE_HEIGHT,
    transform: `scale(${scale})`, transformOrigin: 'top left', opacity,
  };
  let graphic: React.ReactNode = null;

  if (kind === 1) {
    const bars = [0.45, 0.72, 0.94];
    graphic = (
      <g transform={`translate(0 ${28 * (1 - enter)})`}>
        <Panel x={70} y={90} width={940} height={340} accent={accent}/>
        <Letter x={122} y={150} fontSize={38}>{label}</Letter>
        <Letter x={966} y={148} textAnchor="end" fontSize={23} fill={accent}>动画示意</Letter>
        {bars.map((length, i) => {
          const grow = out((progress - 0.08 - i * 0.08) / 0.4);
          const y = 194 + i * 69;
          return <g key={i}>
            <Letter x={118} y={y + 31} fontSize={27}>示例 {String.fromCharCode(65 + i)}</Letter>
            <rect x={252} y={y} width={674} height={43} rx={12} fill={WHITE} fillOpacity={0.09}/>
            <rect x={252} y={y} width={674 * length * grow} height={43} rx={12} fill={i === 2 ? WHITE : accent}/>
            <circle cx={252 + 674 * length * grow} cy={y + 21.5} r={6} fill={INK}/>
          </g>;
        })}
      </g>
    );
  } else if (kind === 7) {
    const cursorX = 766 + 110 * out(progress / 0.75);
    graphic = <g transform={`translate(0 ${30 * (1 - enter)})`}>
      <rect x={64} y={88} width={952} height={1416} rx={42} fill="none" stroke={WHITE} strokeWidth={5}/>
      <path d="M106 88H974Q1016 88 1016 130V188H64V130Q64 88 106 88Z" fill={INK} fillOpacity={0.96}/>
      {[0, 1, 2].map((i) => <circle key={i} cx={104 + i * 32} cy={137} r={9} fill={i === 0 ? accent : WHITE} fillOpacity={i === 0 ? 1 : 0.5}/>)}
      <rect x={250} y={113} width={602} height={47} rx={16} fill={WHITE} fillOpacity={0.1}/>
      <Letter x={280} y={145} fontSize={23}>界面示意 / {label}</Letter>
      <rect x={105} y={1402} width={870} height={55} rx={18} fill={INK} fillOpacity={0.92}/>
      <path d="M132 1417L152 1430L132 1443Z" fill={WHITE}/>
      <rect x={179} y={1425} width={645} height={8} rx={4} fill={WHITE} fillOpacity={0.18}/>
      <rect x={179} y={1425} width={645 * progress} height={8} rx={4} fill={accent}/>
      <path d={`M${cursorX} 1360L${cursorX + 28} 1405L${cursorX + 7} 1400L${cursorX - 4} 1419Z`} fill={WHITE} stroke={INK} strokeWidth={3}/>
      <circle cx={876} cy={1429} r={13 + 10 * smooth((progress - 0.68) / 0.2)} fill="none" stroke={accent} strokeWidth={3} opacity={smooth((progress - 0.68) / 0.2)}/>
    </g>;
  } else if (kind === 8) {
    graphic = <g transform={`translate(0 ${-35 * (1 - enter)})`}>
      <Letter x={70} y={110} fontSize={26} letterSpacing={8} fill={accent}>THE MOTION EDIT</Letter>
      <Letter x={70} y={270} fontSize={158} fontWeight={950} letterSpacing={-8}>EFFECTS</Letter>
      <path d="M76 305H1004" stroke={accent} strokeWidth={8}/>
      <Letter x={78} y={360} fontSize={29} letterSpacing={10}>原声口播 · 动态包装</Letter>
      <Letter x={80} y={1150} fontSize={50} fontWeight={900}>{short(label, 6)}</Letter>
      <Letter x={82} y={1210} fontSize={28} fill={accent}>让重点被看见</Letter>
      <path d="M82 1245H310M82 1271H244" stroke={WHITE} strokeOpacity={0.7} strokeWidth={3}/>
      <g transform={`translate(${915 - 45 * (1 - enter)} 1110)`}>
        <rect width={12} height={185} fill={accent}/>
        <Letter x={-20} y={184} transform="rotate(-90 -20 184)" fontSize={25} letterSpacing={7}>CREATE / REUSE</Letter>
      </g>
    </g>;
  } else if (kind === 10) {
    const items = ['玻璃字', '手机画面', '贴纸轮播'];
    const checked = items.filter((_, i) => progress >= 0.2 + i * 0.2).length;
    graphic = <g transform={`translate(0 ${45 * (1 - enter)})`}>
      <Panel x={70} y={1080} width={940} height={402} accent={accent}/>
      <Letter x={122} y={1143} fontSize={35}>效果清单</Letter>
      <Letter x={952} y={1143} fontSize={29} textAnchor="end" fill={accent}>{checked} / 3</Letter>
      <rect x={119} y={1166} width={832} height={8} rx={4} fill={WHITE} fillOpacity={0.15}/>
      <rect x={119} y={1166} width={832 * out(progress / 0.75)} height={8} rx={4} fill={accent}/>
      {items.map((item, i) => {
        const local = smooth((progress - 0.15 - i * 0.2) / 0.12);
        const y = 1230 + i * 90;
        return <g key={item}>
          <circle cx={148} cy={y} r={23} fill={local > 0 ? accent : 'none'} stroke={local > 0 ? accent : WHITE} strokeOpacity={local > 0 ? 1 : 0.4} strokeWidth={3}/>
          <path d={`M137 ${y}L145 ${y + 8}L160 ${y - 9}`} fill="none" stroke={INK} strokeWidth={5} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - local}/>
          <Letter x={194} y={y + 12} fontSize={34} fill={local > 0 ? WHITE : '#94ADB7'}>{item}</Letter>
          <path d={`M495 ${y + 1}H916`} stroke={WHITE} strokeOpacity={0.12} strokeWidth={2}/>
        </g>;
      })}
    </g>;
  } else if (kind === 11) {
    graphic = <g transform={`translate(0 ${38 * (1 - enter)})`}>
      <Letter x={540} y={202} textAnchor="middle" fontSize={28} letterSpacing={7} fill={accent}>VIDEO THROUGH TYPE</Letter>
      {['剪辑', '特效'].map((word, i) => <Letter key={word} x={540} y={715 + i * 300} textAnchor="middle" fontSize={272} fontWeight={950} fill="none" stroke={i === 0 ? WHITE : accent} strokeWidth={5} paintOrder="stroke" letterSpacing={15}>{word}</Letter>)}
      <path d="M190 1118H890" stroke={WHITE} strokeOpacity={0.65} strokeWidth={3}/>
    </g>;
  } else if (kind === 12) {
    const draw = out(progress / 0.68);
    const paths = [
      'M120 555Q220 510 160 685Q130 760 232 731',
      'M880 495L894 531L932 535L902 558L910 598L877 576L844 598L854 558L823 535L862 531Z',
      'M845 766Q964 800 886 914Q861 949 808 922M808 922L822 883M808 922L850 931',
      'M152 1139Q227 1087 250 1153Q252 1230 168 1219Q98 1202 152 1139',
      'M223 1392Q480 1361 853 1387M262 1411Q564 1387 802 1410',
    ];
    graphic = <g fill="none" stroke={accent} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round">
      {paths.map((d, i) => <path key={d} d={d} pathLength={1} strokeDasharray="1" strokeDashoffset={1 - out((draw - i * 0.06) / 0.76)}/>)}
      <Letter x={540} y={1339} textAnchor="middle" fontSize={45} fill={WHITE} stroke="none">{label}</Letter>
    </g>;
  } else if (kind === 13) {
    graphic = <>
      {/* The caller places its synchronised person-alpha layer above this wall. */}
      <g>
        {Array.from({length: 7}, (_, row) => <g key={row} transform={`translate(${(row % 2 ? -70 : -15) + (row % 2 ? 35 : -35) * progress} ${150 + row * 200})`}>
          {[0, 1, 2, 3].map((column) => <Letter key={column} x={column * 340} y={0} fontSize={135} fontWeight={950} fill={row % 2 ? 'none' : accent} stroke={row % 2 ? WHITE : 'none'} strokeWidth={3} letterSpacing={7}>{column % 2 ? '剪辑' : '特效'}</Letter>)}
        </g>)}
      </g>
      <rect x={75} y={1400} width={930} height={96} rx={22} fill={INK} fillOpacity={0.92}/>
      <Letter x={540} y={1463} textAnchor="middle" fontSize={43}>{label}</Letter>
    </>;
  } else if (kind === 14) {
    const turn = -5 + 6 * out(progress / 0.65);
    graphic = <g transform={`rotate(${turn} 540 790)`}>
      <rect x={195} y={95} width={690} height={1405} rx={96} fill="none" stroke={INK} strokeWidth={25}/>
      <rect x={195} y={95} width={690} height={1405} rx={96} fill="none" stroke={WHITE} strokeOpacity={0.9} strokeWidth={4}/>
      <rect x={430} y={119} width={220} height={38} rx={19} fill={INK}/>
      <circle cx={608} cy={138} r={6} fill={accent}/>
      <path d="M900 367V470M180 340V405M180 449V513" stroke={INK} strokeWidth={12} strokeLinecap="round"/>
      <rect x={245} y={1294} width={590} height={135} rx={26} fill={INK} fillOpacity={0.93}/>
      <Letter x={280} y={1346} fontSize={30}>{short(label, 7)}</Letter>
      <Letter x={280} y={1388} fontSize={21} fill={accent}>画面示意</Letter>
      <path d="M768 1327L789 1340L768 1353Z" fill={WHITE}/>
      <rect x={280} y={1405} width={500 * progress} height={5} rx={2.5} fill={accent}/>
      <path d="M445 1463H635" stroke={WHITE} strokeWidth={8} strokeLinecap="round"/>
    </g>;
  } else if (kind === 18) {
    const feed = out((progress - 0.06) / 0.66);
    const paperY = 1060;
    const paperHeight = 417;
    const teeth = Array.from({length: 25}, (_, i) => `${780 - i * 20},${1465 + (i % 2 ? 12 : 0)}`).join(' ');
    graphic = <>
      <defs><clipPath id={`${svgId}-paper`}><rect x={290} y={paperY} width={500} height={paperHeight * feed}/></clipPath></defs>
      <g transform={`translate(0 ${25 * (1 - enter)})`}>
        <rect x={250} y={1001} width={580} height={83} rx={24} fill={INK} stroke={WHITE} strokeOpacity={0.45} strokeWidth={2}/>
        <rect x={286} y={1051} width={508} height={18} rx={8} fill="#07171E"/>
        <circle cx={785} cy={1032} r={7} fill={accent}/>
        <Letter x={540} y={1042} textAnchor="middle" fontSize={24} fill={accent}>{feed < 0.99 ? '正在列印' : '列印完成'}</Letter>
        <g clipPath={`url(#${svgId}-paper)`}>
          <polygon points={`300,1060 780,1060 ${teeth}`} fill={WHITE}/>
          <Letter x={540} y={1119} textAnchor="middle" fontSize={34} fill={INK}>{short(label, 6)}</Letter>
          <path d="M330 1142H750M330 1402H750" stroke={INK} strokeOpacity={0.45} strokeWidth={2} strokeDasharray="7 8"/>
          {['镂空字', '手机画面', '贴纸轮播'].map((item, i) => <g key={item} opacity={smooth((feed - 0.14 - i * 0.16) / 0.1)}>
            <Letter x={334} y={1200 + i * 65} fontSize={25} fill={INK}>{String(i + 1).padStart(2, '0')}</Letter>
            <Letter x={398} y={1200 + i * 65} fontSize={30} fill={INK}>{item}</Letter>
            <path d={`M706 ${1185 + i * 65}L716 ${1195 + i * 65}L734 ${1175 + i * 65}`} fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round"/>
          </g>)}
          <Letter x={540} y={1440} textAnchor="middle" fontSize={20} fill={INK} letterSpacing={4}>EFFECTS / REUSE</Letter>
        </g>
      </g>
    </>;
  } else if (kind === 19) {
    const angle = progress * Math.PI * 1.7;
    const stickers = Array.from({length: 5}, (_, i) => {
      const theta = angle + i * Math.PI * 2 / 5;
      return {i, x: 540 + Math.sin(theta) * 345, y: 1268 + Math.cos(theta) * 116, depth: Math.cos(theta)};
    }).sort((a, b) => a.depth - b.depth);
    graphic = <g transform={`translate(0 ${40 * (1 - enter)})`}>
      <ellipse cx={540} cy={1268} rx={345} ry={116} fill="none" stroke={accent} strokeOpacity={0.5} strokeWidth={3} strokeDasharray="6 14"/>
      {stickers.map(({i, x, y, depth}) => <g key={i} transform={`translate(${x} ${y}) rotate(${Math.sin(angle + i) * 9}) scale(${0.83 + (depth + 1) * 0.12})`}>
        <rect x={-61} y={-61} width={122} height={122} rx={29} fill={i % 2 ? WHITE : accent} stroke={WHITE} strokeWidth={7}/>
        <Sticker index={i} color={INK}/>
      </g>)}
      <rect x={338} y={1450} width={404} height={62} rx={24} fill={INK} fillOpacity={0.9}/>
      <Letter x={540} y={1494} textAnchor="middle" fontSize={32}>{label}</Letter>
    </g>;
  }

  return <div aria-hidden style={{position: 'absolute', inset: 0, width, height, overflow: 'hidden', pointerEvents: 'none'}}>
    <div style={content}>
      {kind === 2 ? <div style={{
        position: 'absolute', left: 150, top: 1195 + 55 * (1 - enter), width: 780, height: 174,
        borderRadius: 90, display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'linear-gradient(130deg, rgba(242,248,250,.36), rgba(71,180,208,.12) 48%, rgba(21,51,64,.32))',
        border: '3px solid rgba(242,248,250,.8)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
        boxShadow: '0 16px 48px rgba(4,20,29,.2), inset 0 2px 4px rgba(255,255,255,.75)',
        color: WHITE, fontFamily: FONT, fontSize: Math.min(72, 610 / Math.max(4, Array.from(label).length)),
        fontWeight: 900, letterSpacing: 7, textShadow: '0 3px 10px rgba(0,0,0,.5)',
      }}>{label}<span style={{position: 'absolute', bottom: 22, width: 80 + 100 * progress, height: 4, borderRadius: 2, background: accent}}/></div> : null}
      <svg width={BASE_WIDTH} height={BASE_HEIGHT} viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>{graphic}</svg>
    </div>
  </div>;
};
