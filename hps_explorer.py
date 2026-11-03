"""Self-contained HPS lessons: history, evidence, reasoning and a scored inquiry task.

Every lesson works without an LLM. Student answers are stored as real demo actions.
"""
from dataclasses import dataclass

# Curated authored teaching modules: not verbatim copies of textbooks or biographies.
HPS_CASES = {
 'cell': dict(title='细胞学说是怎样建立的？', scientist='胡克、列文虎克、施莱登、施旺等',stage='初高中',module='细胞与生命',
   driving='为什么形态差异巨大的动植物，都能用细胞来解释其结构基础？',
   scene='17世纪的显微镜打开了一个以前看不见的世界。胡克观察软木切片并用“cell”描述所见小室，列文虎克进一步观察到多种活的微小生物。',
   evidence='19世纪，施莱登和施旺分别积累植物、动物组织的观察资料，推动了关于细胞共同性的理论。后来细胞来源于已有细胞的认识逐步完善；不能把科学史简化为某一个人一次发现全部结论。',
   reasoning='从具体样本归纳一般规律时，要比较来自不同生物的观察证据，并说明结论的适用范围。例如病毒不具有细胞结构，但仍可作为非细胞形态生物学实体研究。',
   social='显微镜制造与改进、不同研究者之间的交流和对既有学说的修正，都是理论形成的重要条件。',
   q='如果要进一步支持动植物具有共同的细胞结构基础，哪种证据更有力？',
   options=['只观察一种植物叶片','用显微镜比较多类植物和动物组织并记录共同结构','只阅读一位科学家的生平'],answer=1,
   why='跨类型的重复观察与比较，比单个样本更能支持广泛结论；同时还要注意例外和理论边界。',
   misconception='“所有生物都由细胞构成”并不适用于病毒等非细胞结构实体。'),
 'pasteur': dict(title='巴斯德的鹅颈瓶：空气里有什么？', scientist='路易·巴斯德',stage='初高中',module='微生物与科学实验',
   driving='煮沸后的肉汤接触空气，是否必然产生微生物？',
   scene='在有关自然发生论的争论中，巴斯德设计了鹅颈瓶装置。加热后的肉汤可与外界空气相通，但弯曲瓶颈能拦截许多携带微生物的尘粒。',
   evidence='当瓶颈保持完好、肉汤未被污染时可长时间保持澄清；让肉汤接触瓶颈积尘等处理后，则可能发生微生物生长。这种成对比较的关键是空气通行与微生物进入被区分开。',
   reasoning='判断结论必须仔细控制变量：是否煮沸、容器是否完整、肉汤是否接触尘粒。不是简单地说“空气进不去所以没有生命”。',
   social='实验推动了对微生物污染的理解，也影响了消毒与食品保存实践。',
   q='鹅颈瓶实验中，瓶颈弯曲最重要的作用是什么？',
   options=['彻底隔绝所有空气','让空气进入而尽量阻挡携带微生物的尘粒','让营养物质自动消失'],answer=1,
   why='空气能够进入，许多尘粒和其携带的微生物被截留；这一设计有助于区分不同假说。',
   misconception='鹅颈瓶并不是一个完全密封的真空瓶。'),
 'mendel':dict(title='孟德尔：豌豆怎样揭开遗传规律？', scientist='格雷戈尔·孟德尔',stage='高中',module='遗传与进化',
   driving='为什么F₁全表现高茎，F₂却重新出现矮茎？',
   scene='孟德尔选择具有稳定相对性状的豌豆进行杂交，从容易辨认的性状出发，记录大量后代并寻找规律。',
   evidence='纯合高茎与矮茎杂交时，F₁全为高茎；在单基因完全显性条件下，F₁自交的F₂呈约3:1的性状分离。孟德尔提出成对遗传因子形成配子时分离的假说，再通过测交检验预测。',
   reasoning='关键不是死记3:1，而是区分实验观察与模型预测；小样本会随机波动。测交为检验F₁形成配子的假说提供新证据。',
   social='研究工具、数据统计方法及研究传播影响科学成果的接受过程；这一规律也有适用前提，不能解释全部复杂遗传性状。',
   q='为什么与隐性纯合体测交能够检验F₁的遗传因子组成？',
   options=['隐性纯合体只提供同一种隐性遗传因子，便于由后代表现推断待测个体的配子','测交必然得到3:1','测交能让所有后代都表现显性'],answer=0,
   why='Aa×aa在理想模型下产生约1:1的显、隐性后代，对F₁形成两类配子的预测构成检验。',
   misconception='测交理论比例不等于每次有限样本都恰好1:1。'),
 'morgan':dict(title='摩尔根：果蝇为什么出现伴性遗传？',scientist='托马斯·亨特·摩尔根',stage='高中',module='遗传与进化',
   driving='白眼果蝇为什么在特定杂交中表现出与性别有关的分布？',
   scene='摩尔根团队利用果蝇世代短、子代多等特点，研究眼色性状的传递规律。',
   evidence='通过正反交和子代性别分布的观察，研究者发现某些遗传方式与性染色体有关，进一步发展基因位于染色体上的解释。',
   reasoning='“眼色与性别相关”只是现象，需用染色体组成模型预测不同交配结果，并与数据对比，才能论证定位假设。',
   social='果蝇实验依赖团队、积累的育种记录以及显微染色体研究，体现不同证据类型的结合。',
   q='要验证眼色遗传与性染色体有关，以下哪种设计更有帮助？',
   options=['不区分雌雄直接统计全部后代','进行正反交并分别统计雌雄后代的眼色','只研究父本个体的眼色'],answer=1,
   why='正反交及性别分层统计能够检验性染色体相关的不同预测。',
   misconception='并非所有与性别有关的性状差异都由同一种伴性遗传机制决定。'),
 'dna':dict(title='DNA双螺旋：模型如何由证据建立？', scientist='富兰克林、威尔金斯、沃森、克里克等',stage='高中',module='遗传与进化',
   driving='没有直接“看见”DNA分子的日常形态，研究者怎样提出可靠结构模型？',
   scene='20世纪中叶，不同研究者分别利用化学测量、X射线衍射、分子结构和碱基组成等信息研究DNA结构。',
   evidence='X射线衍射图像提供有助于推断结构的空间线索，碱基组成等化学证据为模型设定约束。双螺旋结构模型需要与多种证据相容。',
   reasoning='实验数据不是模型本身。评价结构模型要问：它解释了哪些证据？有什么新预测？有没有与证据冲突的地方？',
   social='这项研究涉及多位科学家的贡献、机构间合作及科学史上关于数据使用和贡献认定的讨论。',
   q='科学家为什么要同时参考衍射数据和碱基组成信息？',
   options=['任何一张图就能独立证明全部结构','多类证据可以相互约束，提高模型解释力','不同证据之间一定相互矛盾'],answer=1,
   why='结构模型要同时满足几何和化学约束，多种独立证据能够减少错误解释。',
   misconception='不能把DNA结构“模型”与直接拍摄的普通照片等同。'),
 'avery':dict(title='遗传物质之争：怎样排除其他解释？',scientist='艾弗里及其同事、赫尔希与蔡斯等',stage='高中',module='遗传与进化',
   driving='蛋白质和DNA都存在于细胞中，如何判断哪种物质承担遗传信息？',
   scene='肺炎链球菌的转化实验从可遗传的性状改变提出问题，进一步的分离与处理实验帮助缩小可能的物质范围。',
   evidence='艾弗里等人通过对提取物的选择性处理与转化能力比较，获得支持DNA为转化因子的证据；噬菌体同位素标记实验提供了另一类证据。',
   reasoning='实验要设计能区分假说的操作，并考虑处理的专一性、污染、对照和重复。不能把单次实验描述成解决了所有生物的全部遗传问题。',
   social='多个研究团队的实验不断积累，构成科学认识逐步建立的过程。',
   q='若要检验DNA在转化中的作用，哪种比较最关键？',
   options=['比较经DNA酶处理与未经处理的提取物的转化能力','只观察菌落颜色','只把试管放在不同光照条件下'],answer=0,
   why='有针对性地去除DNA并比较转化能力，有助于判断DNA是否为关键因素，前提是处理和对照充分。',
   misconception='科学推断依赖有效对照，不是“某种物质出现”就自动证明它是原因。'),
 'photosynthesis':dict(title='光合作用：氧气、碳和能量从何而来？',scientist='普利斯特利、英格豪斯、恩格尔曼、卡尔文等',stage='初高中',module='光合作用',
   driving='植物为什么需要光？释放的氧气来自哪里？',
   scene='从植物与空气变化的观察，到光照条件对照、叶绿体与光谱研究，再到碳固定研究，光合作用的解释由多代实验逐步完善。',
   evidence='不同研究方法回答不同问题。光照对照可检验光的作用；色光相关实验帮助理解有效光谱；同位素示踪可研究物质的去向。',
   reasoning='单次实验不能同时证明氧气来源、碳固定路径和能量转换机制。要根据要检验的命题选择合适指标和变量。',
   social='光合作用的研究关联农业产量、能源转化和全球碳循环，但真实植物的响应取决于物种与环境。',
   q='如果只想检验光照强度的影响，应怎样设置两组植物？',
   options=['同时改变光照、温度和水分','改变光照，尽量保持温度、水分、CO₂等相同','只比较两株不同物种植物'],answer=1,
   why='只有尽量保持其他因素一致，才能更合理地分析光照这一因素的影响。',
   misconception='不能据“光照更强”就推断光合作用永远线性增加。'),
 'hormone':dict(title='促胰液素的发现：只有神经调节吗？',scientist='贝利斯与斯他林',stage='高中',module='稳态与调节',
   driving='小肠受到酸性食糜刺激后，胰腺分泌活动是否只能由神经反射解释？',
   scene='早期研究者讨论消化液分泌中的神经控制。贝利斯与斯他林通过实验提出了体液传递化学信号的解释。',
   evidence='通过排除部分神经联系及向血液中加入肠黏膜提取物等实验比较，研究者获得支持体液调节的证据。',
   reasoning='设计关键对照时要区分“神经联系是否存在”和“血液中是否有能发挥作用的化学物质”。',
   social='这项研究推动了激素概念的发展，体现旧解释如何被新实验完善，而非科学家个人“灵机一动”。',
   q='要区分神经调节和体液调节，最有价值的证据是什么？',
   options=['仅凭胰腺会分泌的现象','在排除部分神经联系时，血液中仍有可引发分泌的活性因子','只看学生是否背出激素名称'],answer=1,
   why='在神经联系不充分的条件下观察化学信号的效应，才对区分两种假说有帮助。',
   misconception='生理活动可以同时受到神经与体液调节，不是只能二选一。'),
 'pcr':dict(title='PCR：怎样让极少量DNA被检测到？',scientist='凯利·穆利斯及相关技术研究团队',stage='高中',module='生物技术与工程',
   driving='很少量的DNA模板如何在试管中扩增成适合后续分析的样本？',
   scene='PCR技术利用DNA变性、引物退火和延伸的循环过程，实现特定DNA片段的体外扩增。',
   evidence='每个循环的温度变化有不同目的；引物决定扩增位置，聚合酶需要适宜条件。阴性、阳性对照和污染控制影响结果可靠性。',
   reasoning='“出现条带”不等于目标一定正确，需要检查片段长度、对照和可能的非特异性扩增。',
   social='PCR广泛用于研究、检测等应用场景，结果解释需要兼顾技术限制和隐私伦理。',
   q='为什么PCR实验需要设置阴性对照？',
   options=['为了让样本更快扩增','帮助识别试剂或操作过程的污染','让DNA永远不变性'],answer=1,
   why='阴性对照出现异常扩增时，需要警惕污染或非特异性反应，不能直接接受目标检测结论。',
   misconception='DNA扩增能力不等于自动获得准确的临床诊断。'),
 'ecology':dict(title='生态调查：怎样估计看不见的种群？',scientist='生态学调查研究者',stage='高中',module='生物与环境',
   driving='无法逐个数清一片林地里的所有动物，怎样估计种群数量？',
   scene='研究者发展了样方法、标记重捕法等方法，依据研究对象的活动能力与环境条件选择抽样策略。',
   evidence='样方代表性、标记后是否充分混合、标记是否脱落以及重捕概率等条件影响估计结果。',
   reasoning='调查方法有适用假设；重复抽样和误差分析比单次计算一个漂亮的数字更重要。',
   social='种群估计服务于保护与资源管理，需要结合环境变化和人类活动判断。',
   q='标记重捕法中，如果部分标记脱落，可能产生什么影响？',
   options=['总能让估计更准确','可能让被识别为已标记的个体偏少，从而高估种群数量','对估计完全没有影响'],answer=1,
   why='标记个体被识别的比例降低，按常见估算关系可能使种群估计偏高。',
   misconception='抽样估计不是毫无条件的真实总体计数。'),
}


def available_cases(stage):
    return {k:v for k,v in HPS_CASES.items() if v['stage'] in (stage,'初高中')}


def assess_case(case_id,choice_idx):
    case=HPS_CASES[case_id]
    if not isinstance(choice_idx,int) or not 0<=choice_idx<len(case['options']):
        raise ValueError('无效的证据判断')
    return {'correct':choice_idx==case['answer'],'feedback':case['why'],
            'selected':case['options'][choice_idx], 'right':case['options'][case['answer']]}


def render_explorer(student,stage,navigate_to_ai):
    import streamlit as st
    from demo_store import add_story_attempt
    st.subheader('跟着科学家探索')
    st.write('从一个真实的科学问题出发，了解不同证据怎样改变人们的认识，然后亲自作出判断。')
    cases=available_cases(stage)
    ids=list(cases)
    suggested='mendel' if stage=='高中' else 'pasteur'
    slug=st.selectbox('选择科学发现专题',ids,
                     index=ids.index(suggested) if suggested in ids else 0,
                     format_func=lambda k:cases[k]['title'],key=f'story_{student}_{stage}')
    item=cases[slug]
    st.divider()
    st.markdown('### '+item['title'])
    st.caption('相关科学家：'+item['scientist']+' · '+item['module'])
    st.info(item['driving'])
    left,right=st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown('**研究起点**')
            st.write(item['scene'])
    with right:
        with st.container(border=True):
            st.markdown('**关键实验与证据**')
            st.write(item['evidence'])
    with st.expander('我能从中学到什么科学方法？',expanded=True):
        st.write(item['reasoning'])
    with st.expander('科学发展与社会的联系'):
        st.write(item['social'])
    st.markdown('#### 轮到你判断证据')
    with st.form(f'story_form_{student}_{slug}'):
        st.write(item['q'])
        chosen=st.radio('选择最合理的解释',item['options'],index=None,key=f'story_answer_{student}_{slug}')
        submitted=st.form_submit_button('提交判断',type='primary')
    if submitted:
        if chosen is None:
            st.warning('先选择一个观点，再提交。')
        else:
            answer=assess_case(slug,item['options'].index(chosen))
            add_story_attempt(student,slug,item['title'],answer['correct'],answer['selected'])
            st.session_state[f'story_feedback_{student}_{slug}']=answer
            st.rerun()
    result=st.session_state.get(f'story_feedback_{student}_{slug}')
    if result:
        if result['correct']:st.success('你的证据判断是合理的。')
        else:st.warning('这个解释还有问题，再对照实验条件想一想。')
        st.write('**关键解释：**'+result['feedback'])
        if not result['correct']:st.write('**更有力的解释：**'+result['right'])
        st.write('**提醒：**'+item['misconception'])
    st.button('继续问AI：关于这项发现我还有疑问',key=f'story_ai_{student}_{slug}',
              on_click=navigate_to_ai,args=('AI学习助手',f'我正在学习「{item["title"]}」。请讲清楚研究者怎样通过证据得出结论，再回答我的问题。'))
