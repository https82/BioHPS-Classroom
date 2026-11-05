"""Build populated, role-specific microlearning resources from editorial curriculum content.

The output is original pedagogical draft content, NOT 5000 independent textbook
chapters, a claim of full curriculum completeness, or teacher-verified material.
This is a deterministic *build-time* authoring helper: the shipped JSONL exists
independently and is read directly by the app.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
from itertools import cycle
import json, random, re

ROOT = Path(__file__).resolve().parents[1]
K = ROOT/'knowledge'
plan=json.loads((K/'course_construction_plan.json').read_text('utf-8'))
junior=json.loads((K/'curriculum_cards.json').read_text('utf-8'))
senior=json.loads((K/'high_school_cards.json').read_text('utf-8'))
from sys import path
path.insert(0,str(ROOT))
from section_lessons import SECTION_CORE
from junior_theme_lessons import THEME_INTRO

# Careful topic-specific, broadly true factual anchors for canonical secondary-school topics.
# These are deliberately not asserted to be complete textbook explanations.
FACT_RULES=[
 (r'胡克', '胡克观察软木薄片时看到了许多小室并使用了“细胞”这一名称；他看到的主要是死细胞留下的细胞壁轮廓。'),
 (r'列文虎克','列文虎克改进显微观察，观察过多种活的微小生物和细胞；观察工具提高了对肉眼不可见生命现象的认识。'),
 (r'施莱登|施旺','施莱登和施旺分别研究植物和动物，推动形成生物体由细胞构成的共同认识。'),
 (r'魏尔肖','魏尔肖强调新细胞来自已有细胞，这一认识完善了细胞学说的相关表述。'),
 (r'细胞学说','细胞学说指出细胞是动植物体的基本结构单位，新细胞由原有细胞产生；其形成依赖显微观察和不同生物的比较。'),
 (r'生命系统的结构层次','生命系统可从细胞、组织、器官、个体、种群、群落、生态系统等层次认识，但单细胞生物和植物的层次不能机械套用人体结构。'),
 (r'病毒','病毒没有细胞结构，其生命活动与宿主细胞密切相关；不能把所有病毒都说成由细胞组成。'),
 (r'高倍镜|低倍镜|显微镜','观察生物材料一般先用低倍镜定位，再换高倍镜细调；放大倍数增大时视野通常变小、变暗。'),
 (r'原核|真核|核膜界限','原核细胞没有核膜包围的细胞核，但具有遗传物质和基本生命活动；真核细胞通常具有细胞核及多种膜性细胞器。'),
 (r'蓝细菌|细菌','细菌属于原核生物，没有核膜包围的细胞核；有些蓝细菌能够进行光合作用，但不具有植物叶绿体。'),
 (r'糖原|淀粉|纤维素','淀粉和糖原主要与储能有关，纤维素是植物细胞壁的重要组成成分；三者都是由葡萄糖单位构成的多糖。'),
 (r'蛋白质|氨基酸|肽键|脱水缩合','蛋白质由氨基酸经脱水缩合形成多肽，氨基酸种类、排列和空间结构共同影响蛋白质的功能。'),
 (r'自由水|结合水|极性|氢键','水的极性和氢键与其良好的溶剂性质、比热等特性有关；细胞中自由水和结合水的状态与细胞生命活动相关。'),
 (r'核酸|核苷酸|五碳糖','核酸由核苷酸组成；DNA与RNA在糖的类型、部分碱基和常见结构上不同，均与遗传信息相关过程联系密切。'),
 (r'膜脂|膜蛋白|细胞膜|流动镶嵌','细胞膜以磷脂双分子层为基本支架，膜蛋白承担运输、识别和信号传递等功能；膜的结构具有动态性。'),
 (r'线粒体','线粒体参与细胞中许多有氧呼吸相关过程，但细胞利用能量的全部反应并不都只在其中发生。'),
 (r'叶绿体','叶绿体的类囊体膜上有参与光反应的结构，基质中有参与碳同化的酶；叶绿体并非所有植物细胞都有。'),
 (r'内质网|高尔基体','内质网和高尔基体参与细胞内多种蛋白质和脂质的加工、运输等过程；细胞器之间存在功能联系。'),
 (r'核糖体','核糖体是蛋白质合成的场所，可位于细胞质基质或附着于部分内质网膜。'),
 (r'渗透|质壁分离','渗透涉及水通过选择透过性屏障的净移动；成熟植物细胞在适当高渗外液中可能发生质壁分离。'),
 (r'自由扩散|协助扩散|被动运输','被动运输沿物质的电化学梯度进行；自由扩散不依赖特定转运蛋白，而协助扩散需要相应膜蛋白。'),
 (r'主动运输|胞吞|胞吐','主动运输可依靠特定蛋白质并利用能量进行逆梯度运输；胞吞和胞吐涉及膜与囊泡的变化，不能简单归入自由扩散。'),
 (r'酶|活化能|专一性|最适温度|pH','酶能降低反应活化能并加快反应达到平衡的速度，但不改变反应平衡的位置；温度和pH可能影响酶活性。'),
 (r'ATP|ADP','ATP可通过与ADP相互转化参与细胞内的直接能量转移；ATP不是长期储存全部生命活动能量的仓库。'),
 (r'有氧呼吸|无氧呼吸|酒精发酵|乳酸','细胞呼吸使有机物中储存的化学能逐步转移或释放；有氧和无氧条件下的代谢途径与产物有所不同。'),
 (r'光反应|暗反应|碳反应|光合作用|光合色素','光合作用利用光能推动物质与能量转化，光反应与碳同化相互关联；反应速率可受光照、二氧化碳和温度等条件限制。'),
 (r'有丝分裂|细胞周期|染色体凝缩','有丝分裂过程中染色体复制后经排列和分离进入子细胞；DNA分子数与染色体条数的变化时点并不完全相同。'),
 (r'分化|全能性|干细胞','细胞分化常与基因选择性表达相关；已分化细胞是否能重新获得发育潜能取决于细胞和培养条件。'),
 (r'孟德尔|分离定律|测交|显隐性|性状分离','一对等位基因控制的完全显性典型模型中，Aa自交产生AA、Aa、aa约1:2:1的基因型理论比，测交Aa×aa的表现型预期约1:1。'),
 (r'自由组合|双杂合|9:3:3:1','两对基因独立遗传且完全显性等前提下，AaBb自交可出现9:3:3:1的典型表现型比例；连锁等情形不能直接套用。'),
 (r'减数分裂|同源染色体|姐妹染色单体|联会|四分体','减数分裂通常在一次DNA复制之后经历两次分裂；减Ⅰ以同源染色体分离为主要特征，减Ⅱ通常分离姐妹染色单体。'),
 (r'伴性遗传|X连锁|Y染色体','性染色体上的基因可表现特定的遗传规律；推断伴X隐性遗传时应考虑性别及亲子之间的基因传递关系。'),
 (r'噬菌体|肺炎链球菌|转化实验|遗传物质','遗传物质的研究利用转化、标记及对照等证据逐渐确定DNA的重要作用，但部分病毒的遗传物质是RNA。'),
 (r'DNA.*双螺旋|DNA结构|碱基互补','DNA双螺旋通常由反向平行的两条链组成，碱基之间遵循特定互补配对规律；模型构建依赖多来源实验证据。'),
 (r'DNA复制|半保留复制','DNA复制以亲代链为模板合成新链，每个子代DNA通常保留一条亲代链和一条新链。'),
 (r'转录|翻译|密码子|反密码子','转录以DNA链为模板合成RNA，翻译时核糖体依据mRNA密码子合成多肽；密码子与tRNA上的反密码子不是同一结构。'),
 (r'突变|基因重组|染色体变异','突变可能形成新的遗传变异，重组改变已有等位基因的组合；变异产生并不意味着一定有利或有方向。'),
 (r'自然选择|达尔文|进化','自然选择通过可遗传性状导致的生存和繁殖差异改变种群的遗传组成，而不是个体有目的地把基因改成需要的形式。'),
 (r'基因频率|种群基因库|遗传漂变','基因频率以种群中特定等位基因的拷贝数占对应等位基因总拷贝数的比例来描述，受选择、漂变等因素影响。'),
 (r'内环境|稳态','内环境稳态指多种理化性质在调节作用下维持动态的相对稳定，不等于所有数值完全不波动。'),
 (r'反射弧|反射','反射活动需要相应的神经结构及信息传递通路；有动作出现不一定就能证明它是一个完整反射。'),
 (r'动作电位|静息电位|突触','动作电位与膜两侧离子梯度和通道状态相关，突触通常通过递质与受体等完成细胞间信息传递。'),
 (r'胰岛素|血糖|胰高血糖素','血糖稳态涉及胰岛素、胰高血糖素以及肝脏、肌肉等组织；不同信号调节血糖变化的方向和机制不同。'),
 (r'促胰液素|神经调节|体液调节','促胰液素研究启发人们通过排除神经联系等方法检验体液调节假说；神经与体液调节在生命活动中经常协调。'),
 (r'抗体|B细胞|T细胞|免疫','适应性免疫涉及抗原识别、淋巴细胞活化、效应反应和免疫记忆；抗体与细胞毒性T细胞作用方式不同。'),
 (r'生长素|向光性|胚芽鞘','胚芽鞘向光性研究帮助区分感受光刺激的部位与发生生长响应的部位；生长素分布与细胞生长效应相关。'),
 (r'种群密度|样方|标记重捕','样方法通过抽取代表性区域估算种群密度，标记重捕法适用条件不同；抽样方式不当会造成估计偏差。'),
 (r'J型|S型|环境容纳量','种群的J型增长和S型增长都是具有特定假设的模型；环境容纳量受资源与环境条件影响，不是永恒不变的数字。'),
 (r'食物链|营养级|能量流动','生态系统中的能量经不同营养级传递并有散失，食物链箭头通常指向利用前一营养级生物的后者。'),
 (r'碳循环|物质循环|氮循环','物质可在生物群落与非生物环境之间循环，而能量流动一般具有单向性；二者不可混作同一种过程。'),
 (r'生态系统稳定性|抵抗力|恢复力','生态系统受到扰动时的抵抗与恢复能力受结构、物种组成和扰动条件影响，不存在简单适用于一切情境的固定关系。'),
 (r'发酵|酵母|乳酸菌','酵母菌与乳酸菌的生物学类别和代谢方式不同；发酵产物及过程受微生物与环境条件影响。'),
 (r'组织培养|植物细胞工程','植物组织培养在适当条件下可利用细胞发育潜能，但并非任何细胞无需条件就能再生完整植株。'),
 (r'限制酶|连接酶|重组DNA','限制性内切核酸酶负责识别并切割特定DNA序列，DNA连接酶参与连接DNA片段；二者不能混为一谈。'),
 (r'PCR|引物|电泳','PCR依赖模板、引物、DNA聚合酶和温度循环扩增特定DNA片段；检测还需考虑对照与污染可能。'),
 (r'基因工程|转基因','基因工程涉及目标基因获取、载体构建、导入、筛选和鉴定，导入DNA不等于已证明稳定表达或产生预期性状。'),
 (r'生态伦理|生物安全|基因编辑伦理','生物技术的可行性不自动等于伦理与法律许可；应具体评价潜在收益、风险、对象及适用规范。'),
]
# Per-concept explanations override overly broad section summaries. Each entry
# describes the actual named idea, not a restatement of the whole chapter.
EXACT_FACTS = {
'四分体':'减数第一次分裂前期，同源染色体联会，每一对已复制的同源染色体含四条染色单体，称为一个四分体；四分体不是四条染色体。',
'同源染色体与联会':'同源染色体在减Ⅰ前期联会并可发生非姐妹染色单体间的交换；同源染色体并不等于姐妹染色单体。',
'染色体染色单体DNA计数':'染色体条数通常按着丝粒数判断。DNA复制后每条染色体含两条姐妹染色单体，因此DNA分子数可能先增加而染色体条数不增加。',
'豌豆适合作遗传材料的原因':'豌豆通常自花传粉、闭花受粉，便于保持纯系；多个相对性状容易观察，人工控制杂交也相对方便。',
'自花传粉与闭花受粉':'自花传粉指一朵花的花粉传到同一朵花的柱头，闭花受粉是花尚未开放时已完成传粉；豌豆具有这些特点，有利于获得较稳定的亲本。',
'人工杂交操作':'豌豆人工杂交通常先在花粉成熟前去雄以防自花授粉，再套袋隔离，随后人工授粉并重新套袋标记，避免非目标花粉干扰。',
'相对性状':'相对性状是同一种生物同一性状的不同表现类型，例如豌豆茎的高与矮；不能把植物高度与种子颜色当作一对相对性状。',
'亲本与F1 F2':'亲代记为P，杂交产生的第一代为F₁，F₁自交等繁殖产生第二代F₂；不同世代必须区分清楚才能推导遗传比例。',
'一对性状杂交现象':'纯合高茎与矮茎豌豆杂交，典型完全显性模型下F₁可表现高茎；F₁自交后F₂出现显、隐性性状分离。',
'分离现象解释':'杂合体形成配子时，一对等位基因随同源染色体分离而分开；不同配子随机结合后可形成不同基因型和性状表现。',
'遗传因子成对存在假说':'孟德尔提出控制一对相对性状的遗传因子在体细胞中成对存在、形成配子时分离，并通过配子受精重新组合的假说。',
'配子与受精的随机结合':'在基因型Aa形成A和a配子且概率相同的模型中，雌雄配子的随机结合使AA、Aa、aa的理论概率分别约为1/4、1/2、1/4。',
'3比1与1比2比1':'在一对等位基因、完全显性、等概率配子及随机受精等条件下，Aa自交F₂的表现型理论比为3:1，基因型理论比为1:2:1。',
'小样本随机波动':'遗传分离比是概率预期而非每次实验必须精确出现的固定数值。后代数较少时偏离更明显，样本增加通常更接近理论比例。',
'测交验证':'测交通常让待测显性个体与隐性纯合体杂交；若待测个体为Aa且完全显性，后代显隐性表现型的理论比例约为1:1。',
'两对相对性状的杂交':'研究两对独立遗传的相对性状时，应分别跟踪各对等位基因，再分析它们在形成配子及受精过程中的组合。',
'两对遗传因子的解释':'AaBb在两对基因位于不同对同源染色体等独立分配条件下，可形成AB、Ab、aB、ab四种配子，理论上各占1/4。',
'9比3比3比1的条件':'AaBb自交出现9:3:3:1表现型理论比需要两对基因独立遗传、相应位点完全显性等前提；基因连锁或上位效应可能改变比例。',
'独立分配的适用条件':'自由组合定律最典型地适用于位于不同对同源染色体上的非等位基因；同一条染色体上的基因不应不加分析直接当作独立。',
'配子种类和比例':'双杂合AaBb在两对基因独立分配时可产生AB、Ab、aB、ab四类配子，每类理论概率1/4；实际比例有随机波动。',
'卵细胞形成':'卵细胞形成过程中通常发生不均等细胞质分裂，最终形成一个主要功能性卵细胞及极体；与精子形成过程不完全相同。',
'有性生殖与配子':'典型有性生殖以产生并结合配子为重要环节；减数分裂使配子染色体数减半，受精恢复受精卵相应的染色体数。',
'有丝和减数区别':'有丝分裂通常形成与母细胞染色体组数相同的子细胞；减数分裂经一次DNA复制、连续两次分裂形成染色体数减半的配子或孢子细胞。',
'基因与染色体平行关系':'基因和染色体在遗传过程中都可表现成对存在、形成配子时分离、受精时重新组合的平行规律，为基因位于染色体上的假说提供启示。',
'摩尔根果蝇研究':'摩尔根等利用果蝇眼色等性状的杂交结果发现性别相关的遗传模式，为某些基因位于性染色体上提供实验证据。',
'X射线衍射证据':'DNA纤维的X射线衍射图样为推测分子周期性和螺旋结构提供了重要约束，但单张图像不是完整结构模型的全部证据。',
'碱基组成规律':'DNA中嘌呤碱基A与T、G与C的数量通常各自对应，这是理解互补配对和双链结构的重要线索。',
'脱氧核糖磷酸骨架':'DNA每条链中脱氧核糖和磷酸交替连接形成骨架，含氮碱基朝向双螺旋内侧参与互补配对。',
'反向平行':'DNA双链的两条链方向相反，一条沿5′到3′方向，另一条沿3′到5′方向；复制和转录的方向理解以此为基础。',
'DNA多样性与特异性':'DNA分子中的碱基排列次序存在多样性，不同DNA片段可具有特定碱基序列；序列差异与遗传信息有关。',
'基因的定义与边界':'教材常把基因理解为具有遗传效应的DNA片段，但并非染色体上每段DNA都编码蛋白质；基因还涉及非编码RNA等功能。',
'非编码序列':'DNA中存在不直接编码蛋白质的序列，其中一些参与基因调控或形成非编码RNA，另一些功能尚不明确。',
'基因表达调控':'不同细胞可以在DNA序列基本相同的情况下表达不同基因，使其结构与功能发生差异；表达还受环境和调控信号影响。',
'携带者概念':'隐性遗传病的杂合携带者通常不表现相应的隐性疾病性状，但可以把相关等位基因传给后代；具体仍依遗传机制判断。',
'单倍体和二倍体':'单倍体通常由配子直接发育等途径形成，二倍体常含两套染色体组；判断倍性需要结合染色体组数与发育来源。',
'非整倍体':'非整倍体是个别染色体数目相对正常染色体组发生增减的情况，不同于整套染色体组倍增形成的多倍体。',
'比较解剖学':'比较不同物种器官的基本结构与发育来源，可以寻找共同祖先的线索；相似功能不一定意味着相同演化起源。',
'胚胎学证据':'不同生物的胚胎发育可显示某些保守特征，为推断演化关系提供线索，但不能机械认为个体发育简单重演全部演化史。',
'系统发育':'系统发育研究不同物种或类群之间的演化关系，常综合分子、形态及化石证据构建关系假说。',
'过度繁殖':'生物在一定条件下产生的后代数量可能超过环境能长期支持的数量，为自然选择中的资源竞争提供背景。',
'适者生存与繁殖':'自然选择中的适合度不仅指个体能否存活，也涉及其可遗传特征对繁殖贡献的影响；适应具有环境依赖性。',
'种群密度':'种群密度是单位面积或体积中的个体数量，调查时应明确样地边界、研究对象和抽样方法。',
'年龄结构':'种群的年龄结构反映不同年龄阶段个体的比例，可为分析潜在增长趋势提供线索，但不能单凭它精确预测未来种群数量。',
'迁入率迁出率':'种群个体迁入和迁出会改变当地个体数量，讨论增长时需与出生率、死亡率共同考虑。',
'增长速率与增长率':'增长率通常表示相对变化比例，增长速率表示单位时间增加的个体数量；增长曲线的斜率不能直接无条件等同增长率。',
'物种丰富度':'物种丰富度指某区域内物种种类数，不直接等同于每个物种的个体数或完整生物多样性指数。',
'群落垂直结构':'群落垂直结构指生物在不同高度或深度的分层分布，如森林植物分层及相关动物栖息分布。',
'群落水平结构':'群落水平结构描述物种在平面空间的分布差异，常受地形、湿度、光照及种间关系影响。',
'同化量':'同化量是生物摄入物质中实际被吸收、利用并转化为自身可用能量的部分；摄入量不等于同化量。',
'能量金字塔':'能量金字塔按不同营养级的能量量绘制，能量通常逐级减少；它与生物数量或生物量金字塔不是同一个概念。',
'负反馈':'负反馈是系统输出改变后反过来抑制引发变化的过程，有助于维持相对稳定；它不意味着调节结果完全没有波动。',
'缓冲作用':'血浆等体液含有缓冲物质，能在一定范围内减轻酸碱变化；缓冲能力有限，不等于酸碱度无论何时都不改变。',
'反馈控制基础':'稳态调节需要识别偏离、形成调节信号并影响效应器，负反馈能减少原有偏离；不要把反馈理解成独立于生理系统的另一套器官。',
'中枢神经系统':'中枢神经系统包括脑和脊髓，负责多种信息整合及运动、内脏活动调节；周围神经系统与其形成联系。',
'周围神经系统':'周围神经系统主要包括连接中枢与身体其他部位的神经结构，传递感觉信息和运动或内脏调节信号。',
'交感与副交感':'交感和副交感神经通常具有不同的作用模式，并可共同调节内脏活动；具体效果取决于受体与器官。',
'传入神经与传出神经':'传入神经将感受器等产生的信息送向中枢，传出神经把中枢输出传向效应器；二者功能方向不同。',
'神经纤维上的传导':'神经冲动的传导与可兴奋细胞膜局部电位变化和相邻区域的连续激活有关，不是信号沿神经纤维内部简单流动。',
'感觉与运动皮层':'大脑皮层不同区域参与感觉信息加工与随意运动控制，但复杂行为通常依靠多个脑区协同完成。',
'抗原呈递':'抗原呈递细胞加工并展示抗原相关信息，参与激活特定T细胞；它与直接分泌抗体的浆细胞功能不同。',
'免疫屏障':'皮肤、黏膜及其分泌物构成机体对病原体的第一道重要防线，是非特异性防御的一部分。',
'顶端优势':'植物顶芽存在时可抑制部分侧芽生长，与生长素分布等调节有关；摘除顶芽可能促进侧枝发育。',
'光周期':'光周期指昼夜光暗时长的规律变化，一些植物的开花反应受到光周期信号调节；并非所有植物都受相同光周期条件控制。',
'春化作用':'某些植物需要经历一段低温条件才能顺利进入开花过程，这种低温诱导的发育现象称为春化作用。',
'泡菜制作原理':'泡菜发酵主要依赖乳酸菌等微生物产生有机酸并改变食物风味；课堂中应区分发酵原理与食品安全规范。',
'果酒与果醋':'果酒通常利用酵母发酵产生乙醇，果醋制作可利用醋酸菌在合适条件下使乙醇等转化为醋酸；两者菌种及需氧条件不同。',
'无氧与有氧差异':'不同微生物在有氧与无氧环境下代谢途径、产物和能量利用方式不同，必须结合具体菌种和工艺判断。',
'平板划线法':'平板划线法通过在固体培养基表面分区划线逐步稀释细胞，以便得到分离的菌落；课堂教学不应代替规范实验室无菌操作。',
'稀释涂布平板法':'稀释涂布平板法把适当稀释的样品涂布于培养基表面，常用于菌落计数或分离，结果会受到样品处理与培养条件影响。',
'CFU解释':'CFU是菌落形成单位，反映在相应培养条件下能够形成可观察菌落的活性单位数，不等于样品中所有细胞的精确总数。',
'原代培养与传代':'原代培养从组织样本得到初始培养细胞，传代培养指将已培养的细胞转移到新的培养条件继续增殖；细胞状态可能随培养发生改变。',
'原生质体融合':'植物细胞去除细胞壁后可形成原生质体，某些技术可促进不同来源原生质体融合，后续还需筛选及再生。',
'激素比例调控':'植物组织培养中不同植物生长调节物质及其配比可影响愈伤组织形成、芽分化或生根，不能脱离材料条件机械套用固定比例。',
'脱毒苗':'植物脱毒苗通常利用适当的无病毒组织材料、检测及培养等技术获得，结果需要病原检测确认，不能仅凭外观判断无病毒。',
'体外受精':'体外受精指在体外适宜条件下完成精卵结合及受精过程；受精后的胚胎是否正常发育需要进一步观察与条件保障。',
'胚胎移植':'胚胎移植把适宜发育阶段的胚胎转移到受体动物体内继续发育，涉及供受体生理状态和胚胎质量等条件。',
'黏性末端和平末端':'限制性核酸内切酶切割双链DNA可能形成有单链突出部分的黏性末端，也可能形成平末端；不同末端连接条件不同。',
'启动子终止子':'启动子是参与转录起始调控的DNA序列，终止子参与转录终止；表达载体中二者作用不同，不能互换。',
'目的基因获取':'目的基因可通过已有材料分离、核酸扩增或适当的人工合成等方式获得；获取后仍需确认其序列及适用表达系统。',
'引物与模板':'PCR的模板包含待扩增目标片段，引物与模板特定区域互补并提供DNA合成的起点；引物选择影响扩增特异性。',
'医学药物生产':'重组蛋白等生物技术可用于生产某些药物或诊断材料，但产品必须经过质量控制及相应评价。',
'基因治疗入门':'基因治疗通过特定方式补充、修正或调节与疾病有关的遗传功能，具体安全性与有效性必须通过严格研究判断。',
'国际禁令':'禁止生物武器的国际规则强调生物科学和平应用；讨论此问题应着眼风险防范、国际责任和伦理，而不是危害性操作。',
'双重用途风险':'同一生物学技术可能具有合理研究与潜在滥用风险，风险管理需要考虑目的、具体情境、监督与透明度。',
}

RULES=[(re.compile(p, re.I),fact) for p,fact in FACT_RULES]


def best_fact(term,context,section_core,related_summary):
    if term in EXACT_FACTS:return EXACT_FACTS[term],True
    for pat,fact in RULES:
        if pat.search(term):return fact,True
    # If the term has direct lexical overlap with existing card, that is a valid factual base.
    if related_summary and len(related_summary)>=24:return related_summary,True
    sent=re.split(r'(?<=[。！？])',section_core or '')
    wordset=set(term)
    ranked=sorted((s.strip() for s in sent if len(s)>=20),key=lambda s:len(wordset & set(s)),reverse=True)
    if ranked:return ranked[0],False
    return (section_core or context)[:240],False


def support_info(term, peer, card_type, fact, section_core, base_wrong, hps, round_i):
    """Produce different *teaching functions*, no copy/paste filler card repetitions."""
    section_core=(section_core or '').strip()
    anchor=section_core[:250] if section_core else ''
    pe=f'“{peer}”' if peer else '本节其他概念'
    if card_type=='概念与机制':
        body=f'**核心解释**：{fact}。' if not fact.endswith('。') else f'**核心解释**：{fact}'
        body+=f'\n\n**理解脉络**：{anchor}' if anchor and anchor not in fact else ''
        body+=f'\n\n**知识关联**：把“{term}”和{pe}联系起来，分别说明它们的研究对象、作用条件与可观察结果。'
        inquiry=f'请不用背诵原句，解释“{term}”的核心含义，并指出它与{pe}的联系。'
    elif card_type=='易错辨析':
        err=base_wrong if base_wrong else f'只根据“{term}”这个名称推断所有情境中的结果。'
        body=f'**常见误区**：{err}\n\n**怎样纠正**：{fact} 要判断某个说法是否成立，应明确条件和研究对象；不要把{pe}与“{term}”混为一谈。'
        inquiry=f'有人说“掌握{term}后，任何情况下都可以直接照搬同一结论”。你会用什么条件或证据反驳？'
    elif card_type=='HPS科学史与证据':
        history=(f'**科学发现线索**：{hps["title"]}。{hps["driving_question"]}。\n\n' if hps else '**科学推理**：先明确观察与解释的区别，再比较替代假设。\n\n')
        body=history+f'**已有知识**：{fact}\n\n**证据任务**：围绕“{term}”，先写出两个可能的解释，再说明什么观察结果可用于区分它们；如需比较{pe}，应保持其他条件可比。'
        inquiry=f'如果研究者只得到一次关于“{term}”的观察，哪一类证据可以帮助排除其他解释？'
    elif card_type=='实验与建模':
        body=f'**研究问题**：怎样通过观察或模型验证有关“{term}”的解释？\n\n**理论起点**：{fact}\n\n**设计思路**：选择可观察的指标，明确实验组与比较组；如需改变条件，一次尽量只改变一个主要变量，并记录{pe}可能带来的干扰。模型结论只在假设满足时适用。'
        inquiry=f'请确定研究“{term}”的一个可观察指标、一个主要变量，以及至少一个需要控制的条件。'
    elif card_type=='衔接与先修':
        body=f'**先建立联系**：{fact}\n\n**前后知识**：理解“{term}”之前，先确认是否能说明{pe}的含义。再把两者画成“条件—过程—结果”的关系图；对于无法推出的关系，不要强行画因果箭头。'
        inquiry=f'如果学生把“{term}”与{pe}混淆，你会从哪一个最基本的概念重新讲起？'
    else:
        body=f'**应用情境**：在处理与“{term}”有关的生活、健康、农业或生态问题时，先建立科学事实与决策建议之间的联系。\n\n**知识依据**：{fact}\n\n**评价方式**：比较方案能解释什么、仍有哪些不确定性，再考虑成本、风险或公平性。不要把课堂模型直接当作现实操作指导。'
        inquiry=f'如果要把“{term}”用于实际问题，你还需要哪些证据，才能负责任地提出建议？'
    if round_i>0:
        # Repeated references to the same topic must have a DIFFERENT purpose and
        # explanation structure, not just one swapped word at the end.
        if card_type=='概念与机制':
            pathways=[
              (f'**从实例理解**：{fact}\n\n先选择本节提到的一个真实现象，区分观察事实和“{term}”所解释的机制。再对照{pe}，说明哪些条件相同、哪些条件不同。\n\n**补充脉络**：{anchor}',
               f'如果只看到“{term}”的结论，怎样利用{pe}举出一个说明其适用条件的例子？'),
              (f'**推理链条**：{anchor}\n\n据此理解“{term}”时，需要先说清研究对象，再交代条件与机制，最后给出可观察的证据。关键依据是：{fact}',
               f'请用“前提→发生的过程→结果”的顺序解释“{term}”，并明确哪个环节可以观察。'),
              (f'**比较学习**：{pe}与“{term}”都属于本节知识网络，但判断两者是否相同不能只看名称。\n\n**可靠依据**：{fact}\n\n**本节联系**：{anchor}',
               f'请列出“{term}”与{pe}各自的一个判定依据，而不是只写相同点。'),
              (f'**模型前提：{term}**：{fact}\n\n**用模型解释**：根据本节知识，检验你在图示或公式中使用的对象、箭头、单位和条件是否一致。{anchor}',
               f'如果更改关于“{term}”的一个重要前提，哪些结论还成立，哪些需要重新验证？'),
              (f'**复习与迁移**：{anchor}\n\n本节这一内容可用下述依据检查：{fact} 学习后尝试把它讲给不熟悉本章的同学，并说明与{pe}的联系。',
               f'如果要给初次学习者解释“{term}”，你会先讲哪一个现象，再引出哪个机制？')
            ]
            body,inquiry=pathways[(round_i-1)%len(pathways)]
        elif card_type=='HPS科学史与证据':
            body=f'**不同证据怎么比较**：{fact}\n\n先列出与“{term}”有关的两种可能解释，分别写出能支持或反驳它们的观察。然后讨论{pe}会不会改变结果的解释。若历史资料不足，不要杜撰科学家原话或实验记录。'
            inquiry=f'在研究“{term}”时，哪项证据仅支持相关性，哪项证据更接近对因果解释的检验？'
        elif card_type=='易错辨析':
            body=f'**判断边界**：{fact}\n\n试把“{term}”分别放入典型情境和条件变化的情境，判断同一句结论能否照搬。如果把{pe}混在推理中，应指出究竟混淆了对象、过程还是结论。'
            inquiry=f'给“{term}”设计一道会诱发概念混淆的判断题，并解释正确判据。'
        elif card_type=='实验与建模':
            body=f'**换一种检验方式**：{fact}\n\n把“{term}”的相关预测转化为可以记录的现象或数据。如果研究对象不能安全地做真实实验，可采用图示、已公开数据或模拟模型，并说明模型简化掉了什么。'
            inquiry=f'请给“{term}”设计一种不需要危险材料的模型分析活动，并明确它不能证明什么。'
        else:
            body+=f'\n\n**进一步比较**：请把{pe}纳入判断，检查自己的结论是否遗漏前提。'
    if round_i>0:
        distinct_skills=[
            '用一个身边可以观察到的例子说明它适用的条件，并明确例子不能证明的部分。',
            '画一张概念关系图，标出至少两个概念之间的方向或包含关系。',
            '面对一条与本节内容冲突的说法，说明需要哪一项反证。',
            '把过程拆成先后步骤，分别说明参与的结构、物质或环境条件。',
            '比较图示与文字，找出其中一个容易遗漏的条件或数量关系。',
            '根据已有结论作出一个可检验的预测，再考虑结果不符时如何修正解释。',
            '寻找一个不符合简化模型的边界情形，说明它为什么不推翻所有已有证据。',
            '向另一位同学口头解释，并回答他提出的“为什么不是另一种解释”问题。',
            '从不同尺度分析同一现象，区分分子、细胞、个体或群落层次。',
            '归纳本节最容易混淆的两个术语，编写一个正确示例和一个反例。',
            '列出研究时必须控制的一项条件，说明不控制可能造成什么误判。',
            '阅读两条相互矛盾的观察记录，确定哪些信息不足以作因果判断。',
        ]
        body+='\n\n**本项训练**：'+distinct_skills[(round_i-1)%len(distinct_skills)]
    return body,inquiry


def related_card(term,possible):
    from difflib import SequenceMatcher
    def score(c):
        title=c.get('title','')
        s=SequenceMatcher(None,term,title).ratio()
        return max(s,max((SequenceMatcher(None,term,w).ratio() for w in c.get('keywords',[]) if len(w)>1),default=0))
    ranked=sorted(possible,key=score,reverse=True)
    return ranked[0] if ranked and score(ranked[0])>=.48 else None


def hps_for_section(sec):
    hits=[]
    for h in plan['hps']:
        if h.get('book_code')!=sec['book_code']:continue
        linked=h.get('linked_section','').replace('第','')
        sect=sec['section'].replace('第','')
        if linked and (linked in sect or sect in linked):hits.append(h)
    return hits[0] if hits else None


def make_record(idx,node,typ,ordinal,stage,scope):
    term=node['term']; peers=node['peer_terms']; peer=peers[(ordinal+node['node_index']+1)%len(peers)] if peers else ''
    source_summary=node.get('summary',''); section_core=node.get('core','')
    fact,kind=best_fact(term,scope,section_core,source_summary)
    hps=node.get('hps')
    body,q=support_info(term,peer,typ,fact,section_core,node.get('misconception',''),hps,ordinal)
    return {
      'id':f'BH-{idx:05d}',
      'stage':stage, 'scope':scope, 'book_code':node.get('book_code',''),
      'chapter':node.get('chapter',''), 'section_id':node.get('section_id',''),
      'section':node.get('section',''), 'knowledge_id':node['node_id'],
      'term':term, 'category':typ,
      'title':f'{term} · {typ}'+(f'（进阶{ordinal+1}）' if ordinal else ''),
      'content':body, 'thinking_question':q,
      'context':section_core[:260],
      'source_basis':node.get('source',''),
      'editorial_status':'初稿未逐条核验',
      'fact_specific_anchor':kind,
    }


def nodes_for_junior():
    groups=defaultdict(list)
    for i,c in enumerate(junior):
        theme=c['theme'];groups[theme].append(c)
    nodes=[]
    for i,c in enumerate(junior):
        theme=c['theme'];peers=[r['title'] for r in groups[theme] if r['id']!=c['id']]
        nodes.append(dict(node_id=c['id'],term=c['title'],node_index=i,peer_terms=peers,
                          summary=c['summary'],misconception=c.get('misconception',''),
                          core=THEME_INTRO.get(theme,''),section=theme,book_code='J',
                          source=c.get('curriculum_reference',''),hps=None,chapter=theme,section_id='J-'+str(i+1)))
    return nodes


def nodes_for_senior(code):
    result={}
    for sec in plan['sections']:
        if sec['book_code']!=code:continue
        all_nodes=[]
        for i,term in enumerate(sec['terms']):
            m=related_card(term,[c for c in senior if c.get('module')=={'B1':'分子与细胞','B2':'遗传与进化','X1':'稳态与调节','X2':'生物与环境','X3':'生物技术与工程'}[code]])
            all_nodes.append(dict(node_id=f'{sec["section_id"]}-K{i+1:02d}',term=term,
                node_index=i,peer_terms=[x for x in sec['terms'] if x!=term],
                summary=(m.get('summary') if m else ''),
                misconception=(m.get('misconception') if m else ''),
                section_id=sec['section_id'],section=sec['section'],
                chapter=sec['chapter'],book_code=code,
                core=SECTION_CORE.get(sec['section_id'],''),source=sec.get('source',''),
                hps=hps_for_section(sec)))
        result[sec['section_id']]=(sec,all_nodes)
    return result


def schedule_for(scope,counts,slots,rng):
    cats=[]
    for typ,qty in counts.items():cats.extend([typ]*qty)
    assert len(cats)==len(slots),(scope,len(cats),len(slots))
    # Reserve one concept explanation for EVERY knowledge node before distributing
    # the remainder. Category quotas are still exactly fulfilled.
    node_pos={}
    for i,node in enumerate(slots):
        node_pos.setdefault(node['node_id'],i)
    concept_needed=len(node_pos)
    assert counts['概念与机制']>=concept_needed,(scope,concept_needed)
    result=[None]*len(slots)
    for i in node_pos.values():result[i]='概念与机制'
    remainder=[]
    for typ,qty in counts.items():
        remainder.extend([typ]*(qty-concept_needed if typ=='概念与机制' else qty))
    rng.shuffle(remainder)
    remaining_iter=iter(remainder)
    for i in range(len(result)):
        if result[i] is None:result[i]=next(remaining_iter)
    used=Counter(); records=[]
    for node,typ in zip(slots,result):
        key=(node['node_id'],typ)
        ordinal=used[key];used[key]+=1
        records.append((node,typ,ordinal))
    return records


def build():
    rng=random.Random(20261102)
    data=[];idx=0
    jnodes=nodes_for_junior()
    # Spreading 1600 entries across all 153 junior topics; at least one entry per type where possible.
    jslots=[jnodes[i%len(jnodes)] for i in range(1600)]
    rng.shuffle(jslots)
    jcounts=plan['allocation']['初中生物']
    for n,typ,ordinal in schedule_for('初中生物',jcounts,jslots,rng):
        idx+=1;data.append(make_record(idx,n,typ,ordinal,'初中','初中生物'))
    for code,scope in plan['books'].items():
        parts=nodes_for_senior(code)
        slots=[]
        for sec,nodes in parts.values():
            quota=sec['quota']
            # Round robin, every atomic knowledge point is used multiple times.
            slots.extend(nodes[i%len(nodes)] for i in range(quota))
        rng.shuffle(slots)
        counts=plan['allocation'][scope]
        for n,typ,ordinal in schedule_for(scope,counts,slots,rng):
            idx+=1;data.append(make_record(idx,n,typ,ordinal,'高中',scope))
    assert len(data)==5000
    path_out=K/'learning_resources_5000.jsonl'
    path_out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data),encoding='utf-8')
    meta={'records':len(data),'by_scope':dict(Counter(x['scope'] for x in data)),
          'by_type':dict(Counter(x['category'] for x in data)),
          'unique_knowledge_nodes':len(set(x['knowledge_id'] for x in data)),
          'science_anchor_count':sum(bool(x['fact_specific_anchor']) for x in data),
          'unique_titles':len(set(x['title'] for x in data)),
          'min_content_chars':min(len(x['content']) for x in data),
          'median_content_chars':sorted(len(x['content']) for x in data)[len(data)//2],
          'status':'编写并接入的微型学习资源草稿，非5000篇独立深度课程；尚未逐条教材核对'}
    (K/'resource_statistics.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
    print('bytes',path_out.stat().st_size)

if __name__=='__main__':build()
