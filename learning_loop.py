"""BioHPS V7.0: auditable, offline formative practice.

Only explicitly authored multiple-choice items are automatically checked.  This is
NOT a validated psychometric scale or a substitute for teacher assessment.
No student data leaves the running Streamlit session unless the user downloads it.
"""
from datetime import datetime, timezone

# Short, independently-authored, provisional exercises. Must be reviewed by a biology teacher.
# Fields: question, options, correct index, misconception-specific feedback for distractors.
# Separate recheck items guard against passing simply by memorising the first answer.
BANK = {
 'BIO-001': {
  'initial': ('动物细胞和植物细胞通常都具有哪项基本结构？', ['细胞膜、细胞质和细胞核', '细胞壁、叶绿体和大液泡', '叶绿体、细胞壁和细胞核'], 0),
  'recheck': ('观察到细胞没有细胞壁，但具有细胞膜和细胞核，最合理的判断是？', ['必定是植物细胞', '可能是动物细胞', '不是细胞'], 1),
  'remedy': '常见动植物细胞都有细胞膜、细胞质和细胞核；细胞壁与叶绿体并非每种细胞都有。',
  'misconception': '把植物细胞的特殊结构误认为所有细胞共有。',
 },
 'BIO-007': {
  'initial': ('为什么鲸属于哺乳动物，而不是鱼类？', ['因为生活在水中', '因为用肺呼吸、胎生并哺乳', '因为身体呈流线型'], 1),
  'recheck': ('海豚虽然终生生活在水中，仍归为哺乳动物，关键证据是哪一项？', ['有鳍状肢', '能够快速游泳', '用肺呼吸并哺乳幼崽'], 2),
  'remedy': '动物分类要看身体结构和繁殖等特征，不能仅看栖息地。鲸、海豚用肺呼吸，胎生并哺乳。',
  'misconception': '把生活环境或外形当成判别动物类群的充分依据。',
 },
 'BIO-011': {
  'initial': ('草→兔→狐这条食物链中，箭头表示什么？', ['能量和物质随被取食关系传递的方向', '动物运动的方向', '种群数量一定增加的方向'], 0),
  'recheck': ('食物链“草→蝗虫→青蛙”中的生产者是哪一个？', ['青蛙', '蝗虫', '草'], 2),
  'remedy': '食物链通常从生产者开始，箭头由被捕食者指向捕食者，反映物质和能量的转移关系。',
  'misconception': '混淆食物链箭头方向或生产者与消费者。',
 },
 'BIO-014': {
  'initial': ('要研究水分是否影响种子萌发，哪种对照最合理？', ['一组放冰箱且不浇水，另一组温暖且浇水', '两组温度和种子条件相同，仅供水不同', '两组种子数量和温度都不同'], 1),
  'recheck': ('同批种子在相同温度下比较不同供水量，其主要改变的因素是？', ['水分', '温度', '种子品种'], 0),
  'remedy': '研究一个因素时，应尽量控制其他重要条件相同；种子萌发还需要适宜温度和氧气。',
  'misconception': '一次改变多个实验因素，无法判断结果归因。',
 },
 'BIO-016': {
  'initial': ('绿色植物光合作用所需的主要原料是？', ['氧气和葡萄糖', '二氧化碳和水', '氮气和土壤'], 1),
  'recheck': ('对绿色植物来说，光合作用释放的气体通常是哪一种？', ['氧气', '二氧化碳', '氮气'], 0),
  'remedy': '光合作用利用光能，将二氧化碳和水转化为有机物，并释放氧气；条件和过程需结合具体情境理解。',
  'misconception': '混淆光合作用的原料、产物或与呼吸作用的区别。',
 },
 'BIO-021': {
  'initial': ('肺泡适合进行气体交换的一个重要原因是？', ['壁较厚且血管少', '壁薄且周围毛细血管丰富', '肺泡内没有空气'], 1),
  'recheck': ('氧气从肺泡进入血液，主要依靠什么过程？', ['扩散', '肌肉主动推送氧气', '血液倒流'], 0),
  'remedy': '肺泡壁和毛细血管壁都很薄，周围毛细血管丰富；气体沿分压差发生扩散。',
  'misconception': '未理解薄壁、丰富毛细血管及扩散对气体交换的意义。',
 },
 'BIO-027': {
  'initial': ('以下关于DNA、基因和染色体的说法，哪项较准确？', ['基因是DNA上具有遗传效应的片段', '所有DNA都位于细胞膜上', '染色体完全由蛋白质构成'], 0),
  'recheck': ('多数真核生物的染色体主要由什么构成？', ['细胞壁和液泡', 'DNA和蛋白质', '叶绿素和淀粉'], 1),
  'remedy': '基因通常指具有遗传效应的DNA片段；真核生物染色体主要由DNA和蛋白质组成。',
  'misconception': '将基因、DNA和染色体三个层级混为一谈。',
 },
 'BIO-032': {
  'initial': ('制作酸奶常利用哪类微生物的发酵作用？', ['乳酸菌', '病毒', '草履虫'], 0),
  'recheck': ('面包面团发酵常利用哪类微生物？', ['大肠杆菌', '酵母菌', '蓝细菌'], 1),
  'remedy': '不同食品工艺利用不同微生物：酸奶常利用乳酸菌，面包发酵常利用酵母菌；注意食品安全。',
  'misconception': '将所有食品发酵都归因于同一种微生物。',
 },
 'BIO-050': {
  'initial': ('细菌一般没有成形的细胞核，意味着什么？', ['细菌一定没有DNA', '遗传物质没有被核膜包围形成典型细胞核', '细菌完全没有细胞结构'], 1),
  'recheck': ('细菌通常属于哪一类生物？', ['原核生物', '真核动物', '无细胞结构病毒'], 0),
  'remedy': '细菌属于原核生物，通常有DNA，但没有由核膜围成的典型细胞核。',
  'misconception': '把“没有成形细胞核”误解为“没有遗传物质”。',
 },
 'BIO-060': {
  'initial': ('蜘蛛不是昆虫，重要原因之一是它通常有？', ['三对足', '四对足', '只有一对足'], 1),
  'recheck': ('典型成虫昆虫通常具有几对足？', ['三对', '四对', '五对'], 0),
  'remedy': '昆虫成虫通常三对足，蜘蛛属于蛛形纲，通常四对足；同属节肢动物但不是同一类群。',
  'misconception': '把所有节肢动物当成昆虫。',
 },
 'BIO-078': {
  'initial': ('某生态系统中一种捕食者突然减少，合理的预测是？', ['其他种群绝不会变化', '可能影响猎物数量及其他生物关系', '全部生物立即灭绝'], 1),
  'recheck': ('生态系统结构改变后的影响为何不能仅凭一个物种断定？', ['因为食物网中的生物之间存在联系', '因为食物链没有箭头', '因为生产者不依赖环境'], 0),
  'remedy': '食物网中存在多条相互联系的摄食关系，某个环节改变可能产生连锁效应，但具体程度需要观察数据。',
  'misconception': '把生态系统看成互不关联的孤立物种集合。',
 },
 'BIO-088': {
  'initial': ('种子一直完全浸没在水里可能难以萌发，主要原因可能是？', ['缺乏足够氧气', '一定因为没有光', '水没有质量'], 0),
  'recheck': ('同一批种子在适温、适水条件下仍需注意哪项环境条件？', ['是否有足够氧气', '是否处于真空', '是否每天更换种子品种'], 0),
  'remedy': '多数种子萌发需要适当水分、适宜温度及充足氧气；长期浸没可能造成缺氧。',
  'misconception': '以为水越多越有利于萌发，忽略氧气需要。',
 },
 'BIO-095': {
  'initial': ('同一盆植物同时增加光照和温度后气泡增多，能证明只由光照造成吗？', ['能，光照一定是唯一原因', '不能，因为同时改变两个因素', '能，只要气泡数变多'], 1),
  'recheck': ('要比较光照强度对光合表现的影响，哪种设置更恰当？', ['保持温度等条件一致，改变光照', '一边换植物一边换光照', '各组观察时间随意'], 0),
  'remedy': '判断光照影响时应尽量控制温度、材料、CO₂等主要因素一致；气泡数仅是特定条件下的间接观察指标。',
  'misconception': '多变量混杂以及把气泡数视为精确的光合速率。',
 },
 'BIO-105': {
  'initial': ('秋季一些叶片变黄的重要原因是？', ['叶绿素分解或减少，使其他色素更显著', '植物细胞全部瞬间死亡', '叶子变成了土壤'], 0),
  'recheck': ('叶片颜色变化与下列哪项更直接相关？', ['不同色素含量的变化', '根尖细胞全部消失', '光永远不影响色素'], 0),
  'remedy': '部分植物秋季叶绿素逐渐分解，黄色类胡萝卜素更明显；不同物种及环境下变色机制有所差异。',
  'misconception': '以为叶色变化是单一、瞬时或与色素无关的过程。',
 },
 'BIO-115': {
  'initial': ('正常人体心脏共有几个腔？', ['两个', '三个', '四个'], 2),
  'recheck': ('人体左心室的主要作用是？', ['将血泵入主动脉进入体循环', '接受肺静脉血', '将血直接泵入肺动脉'], 0),
  'remedy': '人体心脏有左右心房与左右心室共四个腔；不同心腔承担不同血流任务。',
  'misconception': '混淆心房、心室数量及其血流方向。',
 },
 'BIO-122': {
  'initial': ('完成一个典型反射活动通常需要什么？', ['完整反射弧', '只有骨骼', '只需要肌肉不需要神经'], 0),
  'recheck': ('反射弧中接受刺激并产生神经冲动的结构通常是？', ['效应器', '感受器', '心房'], 1),
  'remedy': '典型反射弧由感受器、传入神经、神经中枢、传出神经与效应器等部分构成。',
  'misconception': '忽视神经通路与感受器在反射中的作用。',
 },
 'BIO-127': {
  'initial': ('疫苗主要通过什么方式帮助预防某些传染病？', ['训练免疫系统产生针对性保护', '直接消灭世界上所有病原体', '保证接种者永不患病'], 0),
  'recheck': ('为什么接种疫苗后仍需要关注公共卫生措施？', ['疫苗不是对所有人所有感染都提供完全保护', '疫苗本质上是抗生素', '病原体一定已经完全消失'], 0),
  'remedy': '疫苗可帮助免疫系统建立针对特定病原体的保护，但保护效果并非绝对，也应遵循公共卫生建议。',
  'misconception': '把疫苗理解为必然、永久、百分之百的保护。',
 },
 'BIO-132': {
  'initial': ('基因和染色体之间较准确的关系是？', ['每条染色体上通常有多个基因', '每个基因都独立漂浮在细胞外', '所有染色体都是基因'], 0),
  'recheck': ('真核细胞的基因一般位于什么物质的特定区域？', ['DNA', '细胞壁', '淀粉'], 0),
  'remedy': '基因通常是具有遗传效应的DNA片段，真核生物染色体上一般含有多个基因。',
  'misconception': '混淆基因、DNA、染色体的包含关系。',
 },
 'BIO-149': {
  'initial': ('制作面包时，酵母使面团膨胀的重要原因是？', ['释放二氧化碳气体', '消耗了所有水分', '释放氮气'], 0),
  'recheck': ('观察面团发酵，能否仅通过面团膨胀就断言发酵环境完全无菌？', ['能，气体越多越无菌', '不能，膨胀不能证明无菌', '能，只要是酵母'], 1),
  'remedy': '酵母发酵可释放CO₂使面团蓬松，但气体产生与无菌状态是两回事。',
  'misconception': '混淆发酵现象和微生物污染检测。',
 },
 'BIO-153': {
  'initial': ('看到“某食物能彻底治愈所有疾病”的短视频，首先应当？', ['立即转发', '核查来源、证据和专业共识', '只看点赞数量'], 1),
  'recheck': ('判断一条生物健康信息是否可靠，哪项最有帮助？', ['只看博主粉丝数', '看是否使用复杂术语', '检查证据出处、适用范围和更新日期'], 2),
  'remedy': '科学信息需要核实来源、证据质量和适用范围，不能把网络热度当成可靠性。',
  'misconception': '依赖传播热度、权威口吻而非可核查证据。',
 },
 'BIO-031': {
  'initial': ('想调查校园草坪上的植物种类，应当优先怎样做？', ['明确范围、记录方法和取样规则', '随意挑最好看的样地', '只数一种植物就推断全校'], 0),
  'recheck': ('为什么要记录样方大小、位置和调查日期？', ['便于比较和复核调查', '为了让表格变长', '调查数据没有必要记录条件'], 0),
  'remedy': '校园生物调查应明确问题、样地或样方选择、记录方法与时间，避免随意取样造成偏差。',
  'misconception': '忽视调查设计与记录可复核性。',
 },
}

MAX_HISTORY = 30

def available(card_id):
    return card_id in BANK


def new_session(card_id, source_query='', started_at=None):
    if card_id not in BANK:
        raise ValueError('当前知识点尚无可自动核对的练习题')
    return {'card_id':card_id,'source_query':str(source_query)[:350],
            'phase':'initial','events':[], 'initial_correct':None,'recheck_correct':None,
            'started_at':started_at or datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'mastery':'尚无检测证据'}


def current_question(session):
    p=session['phase']
    if p not in ('initial','recheck'):
        return None
    question,options,right=BANK[session['card_id']][p]
    return {'question':question,'options':list(options),'right':right,'phase':p}


def submit_answer(session, option_index, when=None):
    """Return a new, independently copied session; never take an answer from LLM as ground truth."""
    cur=current_question(session)
    if cur is None:
        raise ValueError('当前不是可提交答案的阶段')
    if type(option_index) is not int or not (0 <= option_index < len(cur['options'])):
        raise ValueError('请选择有效选项')
    out={**session,'events':[dict(e) for e in session['events']]}
    correct=option_index==cur['right']
    event={'time':when or datetime.now(timezone.utc).isoformat(timespec='seconds'),
           'phase':cur['phase'],'question':cur['question'],
           'selected':cur['options'][option_index],
           'expected':cur['options'][cur['right']], 'correct':correct,
           'evidence_kind':'预编写选择题（未经过教师审核）'}
    out['events'].append(event)
    out['events']=out['events'][-MAX_HISTORY:]
    if cur['phase']=='initial':
        out['initial_correct']=correct
        out['phase']='passed' if correct else 'remediate'
        out['mastery']='初测答对（暂定）' if correct else '初测有误，需巩固复测'
    else:
        out['recheck_correct']=correct
        out['phase']='passed' if correct else 'remediate'
        out['mastery']='复测答对（暂定）' if correct else '复测仍需巩固'
    return out,event


def start_recheck(session):
    if session['phase']!='remediate':
        raise ValueError('未进入巩固阶段')
    if any(event.get('phase')=='recheck' for event in session['events']):
        raise ValueError('本轮已完成复测，不能无限重复同一道题')
    out={**session,'phase':'recheck', 'events':[dict(e) for e in session['events']]}
    return out


def progress_summary(sessions):
    """Summarise only completed, developer-authored checks; never a real grade."""
    checks=[s for s in sessions if isinstance(s,dict) and s.get('card_id') in BANK]
    correct=sum(bool(s.get('initial_correct') or s.get('recheck_correct')) for s in checks)
    revised=sum(s.get('initial_correct') is False and s.get('recheck_correct') is True for s in checks)
    return {'sessions':len(checks),'provisionally_passed':correct,'corrected_after_remedy':revised}
