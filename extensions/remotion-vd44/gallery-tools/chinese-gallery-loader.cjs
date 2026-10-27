/** Gallery-only build adaptation. Vendor files on disk remain byte-identical. */
module.exports = function (source) {
  const file = this.resourcePath.replaceAll('\\', '/');
  let code = source;
  const replace = (from, to) => {
    if (!code.includes(from)) throw new Error(`Gallery localization source changed: ${file}: ${from.slice(0, 60)}`);
    code = code.replace(from, to);
  };
  if (file.endsWith('/pixel-kit/fx.tsx')) {
    replace('  const { cells } = layoutText(text);', `  // Chinese fallback uses NotoSansSC; numeric pixels retain the upstream font.
  if (/[\\u3400-\\u9fff]/.test(text)) return <text x={x} y={y + 7 * cell} fill={color} opacity={opacity} fontFamily="TemplateNoto" fontSize={7 * cell} fontWeight={700} textAnchor={align === 'center' ? 'middle' : align === 'right' ? 'end' : 'start'}>{text}</text>;
  const { cells } = layoutText(text);`);
  }
  if (file.endsWith('/PouroverDripFillGauge.tsx')) {
    replace('text="VOLUME"', 'text="容量"'); replace('text="FULL"', 'text="满格"');
  }
  if (file.endsWith('/PixelCandlestickOhlc.tsx')) {
    replace('text="OHLC"', 'text="开高低收"');
    replace('isUp ? "UP" : "DOWN"', 'isUp ? "上涨" : "下跌"');
  }
  if (file.endsWith('/SocialReel.tsx')) {
    replace('"Share"', '"分享"'); replace('      Follow', '      关注');
  }
  if (file.endsWith('/CommunityChat.tsx')) {
    replace('label="A"', 'label="甲"'); replace('label="B"', 'label="乙"'); replace('label="C"', 'label="丙"');
    replace('Text Channels', '文字频道'); replace('# general', '# 综合讨论'); replace('# random', '# 随意交流');
    replace('Message #{channelName}', '发送到 #{channelName}');
    // The upstream portrait defaults use desktop-size labels; enlarge only the gallery copy.
    const sizes={11:20,12:20,13:22,14:24,15:26,16:28,17:30,18:30};
    code=code.replace(/fontSize: (11|12|13|14|15|16|17|18)\b/g, (_,size)=>`fontSize: ${sizes[size]}`);
  }
  if (file.endsWith('/CharacterJumping.tsx')) {
    // Upstream subtracts jumpOffset again in every SVG position: don't double the jump.
    replace('const bodyBottom = feetY - jumpOffset;', 'const bodyBottom = feetY;');
    replace('const maxJumpH = scale * 0.28;', 'const maxJumpH = scale * 0.22;');
    replace('bottom: height - groundY,', 'bottom: 0,');
  }
  if (file.endsWith('/PixelTypewriterQuote.tsx')) {
    replace('  const { cells } = layoutText(ch);', `  if (/[\\u3400-\\u9fff]/.test(ch)) return [<text key={keyPrefix} x={originX} y={originY + 7 * cell} fill={color} opacity={opacity} fontFamily="TemplateNoto" fontSize={7 * cell} fontWeight={700} textLength={5 * cell} lengthAdjust="spacingAndGlyphs">{ch}</text>];
  const { cells } = layoutText(ch);`);
  }
  if (file.endsWith('/FourToneMonoTitler.tsx')) {
    replace('layoutText(title)', "layoutText(/[\\u3400-\\u9fff]/.test(title) ? '' : title)");
    replace('layoutText(subtitle)', "layoutText(/[\\u3400-\\u9fff]/.test(subtitle) ? '' : subtitle)");
    replace('  // Scanning write-head', `  // Keep the original panel wipe and shimmer timing, with a readable Chinese font.
  panel.push(<defs key="zh-clip"><clipPath id="gallery-title-clip"><rect x={0} y={0} width={Math.max(0, edge)} height={IH}/></clipPath></defs>);
  if (/[\\u3400-\\u9fff]/.test(title)) panel.push(<text key="zh-title" x={TITLE_X0} y={TITLE_Y0 + 7 * titleCell} fontFamily="TemplateNoto" fontSize={7 * titleCell} fontWeight={900} fill={Math.abs(TITLE_X0 + 56 - shimmerX) < 65 ? c3 : c2} clipPath="url(#gallery-title-clip)">{title}</text>);
  if (/[\\u3400-\\u9fff]/.test(subtitle)) panel.push(<text key="zh-subtitle" x={SUB_X0} y={SUB_Y0 + 7 * subtitleCell} fontFamily="TemplateNoto" fontSize={7 * subtitleCell} fontWeight={700} fill={c2} clipPath="url(#gallery-title-clip)">{subtitle}</text>);
  // Scanning write-head`);
  }
  if (file.endsWith('/remotion-ui/Demos.tsx')) replace('16 / ORBIT MOTION', '环绕文字 · 动画示意');
  return code;
};
