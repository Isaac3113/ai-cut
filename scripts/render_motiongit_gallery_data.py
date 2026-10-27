"""Chinese demo inputs; labels/variants come from the official public guide.

All numbers, transactions, comments and UI shown below are illustrative examples.
These are original content parameters, not MotionGit protected implementation.
"""
GROUPS = {
 'base': ('基础讲解', 'title keyword number list compare steps quote bars media stamp chapter fusion'.split()),
 'brand': ('品牌与行动', 'logo intro outro cta subscribe countdown price reveal'.split()),
 'concept': ('概念教学', 'iconcards qa myth prosCons definition tip checklist vs'.split()),
 'data': ('数据与进度', 'donut linechart counter progress timeline table ranking'.split()),
 'diagram': ('关系与系统结构', 'flow cycle funnel venn mindmap matrix hub'.split()),
 'showcase': ('真实素材展示', 'gallery beforeafter kenburns polaroid device collage spotlight'.split()),
 'typo': ('文字动态', 'kinetic highlight scramble rotator marquee bigtype'.split()),
 'ui': ('界面与交互演示', 'chat comment notify search browser social cursor'.split()),
 'overlay': ('叠加标注与装饰', 'lowerthird callout sticker emoji progressbar tag confetti frame'.split()),
}

P = 'presenter.jpg'
S = 'screen.jpg'
D = 'detail.jpg'
LOGO = 'logo.png'

# One representative is rendered. All three official variants remain in the catalogue.
VARIANTS = {'keyword':'focus','stamp':'badge','intro':'minimal','outro':'next',
 'subscribe':'triple','countdown':'ring','prosCons':'columns','vs':'cards',
 'ranking':'list','beforeafter':'split','device':'monitor','polaroid':'pin',
 'highlight':'underline','bigtype':'outline','notify':'toast','frame':'viewfinder'}

PROPS = {
 'title': {'line1':'AI 视频细节','line2':'保留剧情再修复','kicker':'控件演示 · 示例文案'},
 'keyword': {'word':'先看证据','sub':['定位问题','再做判断']},
 'number': {'label':'示例片段数','value':3,'unit':'段','note':['仅演示数字动画']},
 'list': {'title':'检查清单示例','items':['保留原始素材','定位具体问题','检查修改结果']},
 'compare': {'left':{'big':'整体','label':'示例方案甲','lines':['重新生成']},'right':{'big':'局部','label':'示例方案乙','lines':['保留剧情']},'verdict':'按需求选择','winner':'none'},
 'steps': {'title':'教学步骤示例','steps':['发现问题','定位画面','局部修复']},
 'quote': {'text':'先保留原始素材，再检查每一次修改。','who':'示例提示语'},
 'bars': {'title':'示例数据','items':[{'label':'方案甲','value':40},{'label':'方案乙','value':65},{'label':'方案丙','value':85}],'unit':'分','max':100},
 'media': {'src':S,'title':'本人实拍屏幕 · 演示','callouts':[{'text':'观察画面','x':0.5,'y':0.45}]},
 'stamp': {'text':'演示完成','sub':'仅演示确认章动画','tone':'ok'},
 'chapter': {'no':'01','name':'先看原片','sub':'章节切换示例'},
 'fusion': {'a':'真实素材','b':'清楚讲解','result':'容易理解','line':'概念组合示例'},
 'logo': {'name':'AGI TOP','src':LOGO,'tagline':'本人品牌 · 动效演示'},
 'intro': {'title':'AI 视频修细节','subtitle':'模板开场演示','episode':'示例 01'},
 'outro': {'thanks':'观看示例','name':'AGI TOP','avatar':P,'follow':'下一段','sub':'仅演示模板结尾','items':[{'text':'定位问题','src':S},{'text':'检查细节','src':D}]},
 'cta': {'text':'查看示例','sub':'按钮动画演示','kicker':'示例操作','dir':'down','icon':'arrow'},
 'subscribe': {'items':[{'icon':'like','label':'示例','count':3},{'icon':'bell','label':'提醒','count':1}],'avatar':P,'name':'示例账号','done':'已演示','kicker':'互动动画示例'},
 'countdown': {'from':3,'label':'示例倒计时','end':'开始'},
 'price': {'price':'99','was':'129','name':'示例套餐','kicker':'虚构价格 · 仅演示','tag':'示例','unit':'RM','feats':['示例功能一','示例功能二']},
 'reveal': {'text':'找到重点','sub':'揭示动画示例','kicker':'控件演示','icon':'idea'},
 'iconcards': {'title':'工作分工示例','kicker':'控件演示','items':[{'icon':'video','title':'素材','text':'保留原始视频'},{'icon':'search','title':'检查','text':'定位具体问题'},{'icon':'check','title':'确认','text':'核对修改结果'}]},
 'qa': {'question':'怎样保留原有剧情？','answer':'先定位具体问题，再评估局部修改。','kicker':'问答示例'},
 'myth': {'myth':'有瑕疵就全部重做','fact':'先判断是否只需局部修改','mythLabel':'示例误区','factLabel':'判断思路','kicker':'概念对照示例'},
 'prosCons': {'pros':['保留上下文','便于对照'],'cons':['需要检查'],'title':'局部修改示例','verdict':'按实际问题判断','lean':'even','proLabel':'优点示例','conLabel':'限制示例','kicker':'方案分析'},
 'definition': {'term':'局部修复','definition':'只修改具体问题所在的区域或片段。','example':'示例：保留剧情，处理细节。','pos':'概念','kicker':'词条示例'},
 'tip': {'text':'做修改前，先保存原始素材。','title':'操作提示示例','kind':'tip','kicker':'控件演示'},
 'checklist': {'items':['参数已准备','预览已查看','演示已导出'],'title':'动画清单示例','done':'示例','kicker':'非实际项目验收状态'},
 'vs': {'a':{'name':'示例甲','src':P,'tag':'方案对比'},'b':{'name':'示例乙','src':S,'tag':'方案对比'},'stats':[{'label':'示例值','a':4,'b':6,'unit':'分'}],'winner':'none','kicker':'虚构数据 · 仅演示'},
 'donut': {'items':[{'label':'示例甲','value':40},{'label':'示例乙','value':35},{'label':'示例丙','value':25}],'title':'示例占比','center':'示例','unit':'%'},
 'linechart': {'points':[{'label':'一','value':20},{'label':'二','value':35},{'label':'三','value':30},{'label':'四','value':50}],'series':['示例序列'],'title':'示例趋势','unit':'分','note':'非业务数据'},
 'counter': {'items':[{'label':'示例甲','value':12,'unit':'项'},{'label':'示例乙','value':24,'unit':'项'}],'title':'示例计数'},
 'progress': {'items':[{'label':'示例任务甲','percent':40},{'label':'示例任务乙','percent':75}],'title':'示例进度'},
 'timeline': {'items':[{'date':'步骤一','text':'导入素材'},{'date':'步骤二','text':'检查问题'},{'date':'步骤三','text':'对照结果'}],'current':2,'title':'示例时间线'},
 'table': {'cols':['方案甲','方案乙'],'rows':[{'label':'示例项目一','cells':['支持','支持']},{'label':'示例项目二','cells':['可选','支持']}],'title':'示例比较表'},
 'ranking': {'items':[{'label':'示例甲','value':80},{'label':'示例乙','value':65},{'label':'示例丙','value':50}],'title':'示例排序','unit':'分'},
 'flow': {'nodes':[{'text':'输入素材','icon':'video'},{'text':'检查细节','icon':'search'},{'text':'对照结果','icon':'eye'}],'title':'流程示例'},
 'cycle': {'nodes':[{'text':'观察','icon':'eye'},{'text':'修改','icon':'tool'},{'text':'验证','icon':'check'}],'title':'循环示例'},
 'funnel': {'layers':[{'label':'初步素材','value':'100项'},{'label':'候选素材','value':'40项'},{'label':'选定素材','value':'10项'}],'title':'示例漏斗'},
 'venn': {'sets':['内容','画面','声音'],'center':'表达','title':'关系示例'},
 'mindmap': {'center':'视频检查','icon':'video','branches':[{'text':'内容','icon':'book','children':['原意']},{'text':'画面','icon':'image','children':['细节']},{'text':'声音','icon':'mic','children':['清楚']}]},
 'matrix': {'quads':['先处理','待验证','可保留','后处理'],'xLabel':'影响程度','yLabel':'处理难度','title':'示例判断矩阵','pick':1,'points':[{'label':'示例项','x':0.7,'y':0.6}]},
 'hub': {'center':{'text':'素材中心','icon':'folder'},'items':[{'text':'原片','icon':'video'},{'text':'声音','icon':'mic'},{'text':'字幕','icon':'file'}]},
 'gallery': {'items':[{'src':P,'caption':'本人口播'},{'src':S,'caption':'本人拍屏'},{'src':D,'caption':'本人实操'}],'title':'真实素材展示示例'},
 'beforeafter': {'before':S,'after':D,'beforeLabel':'画面一','afterLabel':'画面二','title':'两画面对照 · 非修复结果'},
 'kenburns': {'items':[{'src':P,'caption':'本人素材 · 镜头移动演示'}],'kicker':'动效演示'},
 'polaroid': {'items':[{'src':P,'caption':'本人口播'},{'src':S,'caption':'本人拍屏'}]},
 'device': {'src':S,'title':'屏幕容器示例','sub':'本人实拍素材'},
 'collage': {'items':[{'src':P},{'src':S},{'src':D}],'title':'本人素材拼贴示例'},
 'spotlight': {'src':S,'title':'重点区域演示','points':[{'x':0.5,'y':0.45,'label':'示例重点'}]},
 'kinetic': {'lines':['保留剧情','找到问题','修好细节'],'kicker':'文字节奏示例'},
 'highlight': {'text':'先保留*原始素材*再检查修改','kicker':'关键词强调示例'},
 'scramble': {'word':'定位问题','sub':'文字解码动画演示','kicker':'控件演示'},
 'rotator': {'lead':'先检查','words':['内容','画面','声音'],'tail':'再决定怎样修改','kicker':'轮换词示例'},
 'marquee': {'items':['内容清楚','画面完整','声音自然'],'big':'示例','kicker':'文字循环'},
 'bigtype': {'word':'细节','src':P,'sub':'大字标题演示','kicker':'本人素材'},
 'chat': {'messages':[{'who':'left','text':'这段画面需要检查吗？','name':'示例甲','avatar':P},{'who':'right','text':'先看原片，再定位问题。','name':'示例乙','avatar':P}],'title':'虚构对话示例'},
 'comment': {'items':[{'user':'示例甲','text':'这是评论动画示例。','likes':3,'time':'示例','avatar':P},{'user':'示例乙','text':'不代表真实客户反馈。','likes':2,'time':'示例','avatar':P}],'title':'虚构评论示例','src':P},
 'notify': {'items':[{'app':'示例应用','title':'演示通知','text':'这不是实际系统通知。','time':'现在','icon':'bell'}],'time':'10:00','date':'演示日期'},
 'search': {'query':'怎样检查视频细节','placeholder':'示例搜索','items':[{'text':'示例结果一','desc':'先定位具体问题','icon':'search'},{'text':'示例结果二','desc':'保留原始素材对照','icon':'video'}]},
 'browser': {'url':'example.com/demo','title':'模拟浏览器示例','src':S,'callouts':[{'text':'示例标注','x':0.4,'y':0.4,'w':0.2,'h':0.15}]},
 'social': {'user':'示例账号','text':'界面动画示例，非真实发布。','time':'示例','src':P,'avatar':P,'likes':3,'comments':2,'shares':1,'followers':12},
 'cursor': {'items':[{'label':'导入示例','icon':'folder'},{'label':'检查示例','icon':'search'},{'label':'导出示例','icon':'video'}],'title':'模拟点击示例','src':S,'pick':2},
 'lowerthird': {'name':'本人素材','title':'姓名条动画示例','avatar':P,'side':'left'},
 'callout': {'text':'示例重点','x':0.55,'y':0.44,'w':0.24,'h':0.16},
 'sticker': {'text':'重点','icon':'idea','rot':-5,'x':0.7,'y':0.25},
 'emoji': {'icon':'smile','text':'✨','n':6,'x':0.5,'y':0.3},
 'progressbar': {'chapters':['原片','检查','结果'],'current':2,'title':'步骤示例'},
 'tag': {'items':['本人素材','模板演示'],'pos':'tl'},
 'confetti': {},
 'frame': {'label':'演示取景框'},
}

AVOID = {
 'base':['不替代原始证据；重点字不能改变原话的限定条件。'],
 'brand':['只在需要品牌开场或行动引导时使用；示例价格与互动数不能当成事实。'],
 'concept':['简化概念不能省略关键前提；完成章和勾选不能冒充实际验收。'],
 'data':['正式视频必须绑定真实数据及单位；本演示数字全部为示例。'],
 'diagram':['关系图须反映实际流程；不能把假设关系写成已实现功能。'],
 'showcase':['必须使用有权使用的真实素材；对照动画不能冒充真实修复结果。'],
 'typo':['保持可读停留时间；不宜持续堆叠或覆盖字幕。'],
 'ui':['模拟界面必须标明示例；不能冒充真实操作、通知或用户反馈。'],
 'overlay':['避开脸部、字幕与关键证据；装饰不应抢走讲解重点。'],
}

INPUT_HINT = {
 'base':['短标题或重点词','清楚的解释关系','真实数值或标明示例的数据'],
 'brand':['品牌名称或有权使用的 Logo','明确的行动引导或章节信息'],
 'concept':['定义、问题、对比或清单文案','关键限定条件'],
 'data':['有来源的数值、标签和单位'],
 'diagram':['真实节点、顺序、层级或关系'],
 'showcase':['本人视频帧、照片、产品图或真实截图','需要强调的区域'],
 'typo':['适合阅读的短词和短句'],
 'ui':['明确标示的模拟文案或真实界面截图'],
 'overlay':['叠加底图或视频','短标签及标注位置'],
}
