# 原生重点字与声音节点

这里保存已经在ChatCut真实渲染的重点字源码与插入记录。唯一主时间轴仍为ChatCut中的VD44审阅版；继续修改前读取官方最新状态，不把这个记录覆盖成第二套剪辑清单。

native-keyword.jsx是ChatCut inline Motion Graphic受限执行环境的源码，不是独立React应用。Component只导出渲染函数；useCurrentFrame、useVideoConfig、spring和interpolate由宿主提供。输入props包括text、tail、fontFamily、accentColor、secondaryColor；必须绑定`const props=item.props`以通过宿主检查。

实际assetId为8f15e238-306c-4cf1-95a5-1cf544b74106，画布1560×260，30fps，75帧，主画面位置left180/top660。默认Noto Sans SC、黄色#FFD545与奶油#FFF3CB；否定位置少量红色。14次强调、22个轻音效、7次人物轻推近在placements.json按主时间轴帧记录。

这个原生组件可以在ChatCut调字/配色；HyperFrames与Remotion输出的复杂流程视频需要改各自源码重渲染。两种可编辑程度不能混称。
