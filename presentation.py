"""Auditable, static public-facing descriptions and developer demonstration content.

The scenario is a developer simulation, NOT an evaluation involving real students.
"""

PUBLIC_NAME = '探知 · BioHPS'
ONE_LINE = '从一个生物学问题开始，开启主动学习。'

PRODUCT_VALUES = [
    ('自由问答', '围绕初中生物课程七大主题开展知识讲解和理解检查。'),
    ('分层引导', '按学生需求进行启发式提问、解释及练习，而不是一律套用实验流程。'),
    ('误解诊断', '识别常见概念混淆，说明修正依据；形成性判断须教师复核。'),
    ('特色探究', 'HPS融入三个深度实验，用证据链训练实验设计与科学推理。'),
    ('教师辅助', '为课堂导入、活动设计和练习评价提供备课参考。'),
]

# Developer-simulated conversation provided and run during program debugging.
# These lines must NEVER be reported as a measured student learning gain.
DEMO_STORY = [
    {
        'who': '模拟学生 · 典型误解',
        'title': '先提出错误解释',
        'body': '我认为鹅颈瓶里肉汤没有出现微生物，是因为空气完全无法进入瓶内。',
        'meaning': '待诊断：混淆空气流通与携带微生物的尘埃传播。',
    },
    {
        'who': 'BioHPS · 引导追问',
        'title': '引导观察实验事实',
        'body': '鹅颈瓶的瓶口并未密封，空气其实可以进出。如果空气能进入而肉汤仍保持澄清，关键可能是什么？',
        'meaning': '不是直接给完整答案，而是让学生检验最初解释。',
    },
    {
        'who': '模拟学生 · 修正理解',
        'title': '重新理解瓶颈作用',
        'body': '我明白了，鹅颈瓶允许空气进入，但弯曲处可以截留带有微生物的尘埃。',
        'meaning': '可记录科学概念修正，但还不能当作实验设计能力达标。',
    },
    {
        'who': '模拟学生 · 提出预测',
        'title': '转化成可检验假设',
        'body': '如果倾斜鹅颈瓶，让肉汤接触瓶颈积尘，那么肉汤可能出现微生物生长、变得浑浊；保持直立的瓶中肉汤则可能保持澄清。',
        'meaning': '出现条件和预期现象后，才可继续检查阶段条件。',
    },
]

CASE_PITCH = {
    '鹅颈瓶实验': ('空气可以进入，为什么肉汤仍可能保持澄清？', '科学事实、可检验假设、对照与证据'),
    '光合作用': ('光照增强后气泡变多，就一定是光照导致的吗？', '控制变量、测量局限与解释'),
    '种子萌发': ('两组种子萌发不同，到底是水分还是温度的作用？', '对照设计、重复观察与替代解释'),
}

LIVE_EXAMPLES = {
    '鹅颈瓶实验': [
        ('识别错误想法', '我认为鹅颈瓶里肉汤没有出现微生物，是因为空气完全无法进入瓶内。'),
        ('科学概念修正', '我明白了，鹅颈瓶允许空气进入，但弯曲处可以截留带有微生物的尘埃。'),
        ('提出实验预测', '如果倾斜鹅颈瓶让肉汤接触瓶颈积尘，那么肉汤可能变浑浊；直立组可能保持澄清。'),
    ],
    '光合作用': [
        ('识别变量混杂', '我想同时提高光照和温度，如果气泡变多就说明光照增强了光合作用。'),
        ('修正实验方案', '研究光照作用时，我会保持温度和植物材料相同，只改变光照。'),
        ('提出实验预测', '如果仅增强光照并保持温度等因素一致，在适当范围内单位时间气泡数可能增加。'),
    ],
    '种子萌发': [
        ('识别变量混杂', '我想让一组种子不浇水还放冰箱，另一组浇水并放在暖房里，比较萌发数量。'),
        ('修正实验方案', '我应当只改变水分，保持温度、种子来源和观察时间一致。'),
        ('提出实验预测', '如果种子来自同一批次、温度相同，一组适量供水一组不给水，那么适量供水组萌发数量可能更高。'),
    ],
}


def demo_is_simulated():
    return True


def clean_model_history(records, current_question):
    """Exclude failed/API-disabled turns from future LLM context.

    Return only verified successful student/assistant pairs followed by the
    current user turn. The UI audit keeps all attempts independently.
    """
    items=[]
    for record in records[-12:]:
        if (isinstance(record,dict) and str(record.get('status','')).startswith('成功')
                and isinstance(record.get('student'),str)
                and isinstance(record.get('reply'),str)):
            items.extend([('user',record['student']),('assistant',record['reply'])])
    items.append(('user',current_question))
    return items[-13:]
