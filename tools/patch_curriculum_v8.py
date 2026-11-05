from pathlib import Path
p=Path(__file__).resolve().parents[1]/'curriculum.py'
s=p.read_text(encoding='utf-8')
anchor='OFFICIAL_CURRICULUM = '
idx=s.index(anchor)
line_end=s.index('\n',idx)
s=s[:line_end+1]+'''SENIOR_THEMES = ['高中·分子与细胞', '高中·遗传与进化', '高中·稳态与调节', '高中·生物与环境', '高中·生物技术与工程']
SENIOR_CURRICULUM = 'https://www.pep.com.cn/xw/zt/rjwy/gzkb2020/202205/P020220517519140545267.pdf'


def load_all_cards(root=BASE):
    """Merge the existing 153 junior cards and additional senior-level seed notes.

    Keeps load_cards() unchanged for V6.2 test/API compatibility.
    """
    root=Path(root)
    junior=load_cards(root)
    senior=json.loads((root/'knowledge'/'high_school_cards.json').read_text(encoding='utf-8'))
    merged=junior+senior
    ids=[card['id'] for card in merged]
    if len(ids)!=len(set(ids)):
        raise ValueError('课程知识卡ID重复')
    return merged


def filter_stage(cards, stage='全部'):
    if stage in ('初中','高中'):
        return [c for c in cards if c.get('grade','初中')==stage]
    return list(cards)

''' +s[line_end+1:]
s=s.replace('if theme and theme not in THEMES:\n        return []','if theme and theme not in THEMES+SENIOR_THEMES:\n        return []')
s=s.replace("def retrieve(question, cards, selected_id=None, theme=None, limit=3):", "def retrieve(question, cards, selected_id=None, theme=None, limit=3, stage='全部'):")
s=s.replace('    if selected_id:\n        lead = next((c for c in cards if c[\'id\'] == selected_id), None)',"    cards=filter_stage(cards,stage)\n    if selected_id:\n        lead = next((c for c in cards if c['id'] == selected_id), None)")
s=s.replace('def resolve_course_context(question, cards, selected_id=None, theme=None, previous=None, limit=3):',"def resolve_course_context(question, cards, selected_id=None, theme=None, previous=None, limit=3, stage='全部'):")
s=s.replace('    hits, label = retrieve(question, cards, selected_id, theme, limit)', '    cards=filter_stage(cards,stage)\n    hits, label = retrieve(question, cards, selected_id, theme, limit)')
s=s.replace("'本地课程知识库未匹配到合适知识卡。请用你掌握的通用初中生物学知识谨慎回答；'", "'本地课程知识库未匹配到合适知识卡。请用你掌握的通用初高中生物学知识谨慎回答；'")
s=s.replace('不得输出任何“参考资料卡：[BIO-xxx]”引用。', '不得输出任何虚构的知识卡编号或教材引用。')
s=s.replace('如果用户提问不属于初中生物学习，简短说明适用范围；', '如果用户提问不属于初高中生物学习，简短说明适用范围；')
s=s.replace('你是探知 BioHPS 的初中生物学教学助手。目标是服务课程全学段的知识学习', '你是探知 BioHPS 的初高中生物学教学助手。目标是服务初高中学段的知识学习')
s=s.replace('中文清晰、符合初中生知识水平', '中文清晰、符合本轮初中或高中学习层次')
s=s.replace('以“参考资料卡：[BIO-xxx]”列出相应编号', '以“参考资料卡：[BIO-xxx或HS-xxx]”列出相应编号')
s=s.replace("r'BIO-\\d{3}'", "r'(?:BIO|HS)-\\d{3}'")
p.write_text(s,encoding='utf-8')
