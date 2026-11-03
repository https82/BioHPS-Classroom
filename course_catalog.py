"""Student-facing map of the agreed curriculum blueprint.

Planning nodes are not substituted for authored teaching lessons. This distinction is
important both educationally and for honest contest communication.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def load_plan(path=None):
    p = Path(path) if path else ROOT / 'knowledge' / 'course_construction_plan.json'
    obj = json.loads(p.read_text(encoding='utf-8'))
    if not all(k in obj for k in ('books', 'sections', 'atoms', 'hps')):
        raise ValueError('课程目录文件缺少字段')
    return obj


def books(plan):
    return [(code, title) for code, title in plan['books'].items()]


def chapters(plan, book_code):
    return list(dict.fromkeys(s['chapter'] for s in plan['sections'] if s['book_code'] == book_code))


def sections(plan, book_code, chapter):
    return [s for s in plan['sections'] if s['book_code'] == book_code and s['chapter'] == chapter]


def terms(plan, section_id):
    return [a['term'] for a in plan['atoms'] if a['node_id'].startswith(section_id + '-K')]


def matching_cards(cards, book_code, term, limit=5):
    """Return direct title/keyword matches only, not proof of a completed lesson."""
    book_names={'B1':'分子与细胞','B2':'遗传与进化','X1':'稳态与调节','X2':'生物与环境','X3':'生物技术与工程'}
    module=book_names.get(book_code,'')
    term=str(term).strip()
    if not term or not module:
        return []
    candidates=[]
    for c in cards:
        if c.get('grade')!='高中' or c.get('module')!=module:
            continue
        title=str(c.get('title',''))
        words=[title,*c.get('keywords',[])]
        if any(len(w)>=2 and (w in term or term in w) for w in words):
            candidates.append(c)
    return candidates[:limit]


def deep_teaching_question(stage, book_name, section, term):
    """A request for the model, never misrepresented as prewritten reviewed content."""
    return (f'我正在学习{stage}生物，教材模块是《{book_name}》，章节是“{section}”，'
            f'知识点是“{term}”。请像认真负责的生物老师一样，完整而循序渐进地教我：'
            '先解释为什么需要学这个概念，再用准确的定义和机制一步步讲清楚；'
            '配一个典型例题或情境并完整推理，指出两种常见误解以及怎样纠正；'
            '如果有可靠的科学发现史或经典实验，请讲清问题—假设—证据—结论；'
            '最后给我一道不泄露答案的理解检查题。'
            '请不要虚构教材页码、科学家语录或未提供的实验数据；'
            '如果材料不支持细节要说明。')


def quality_state(plan):
    return {'books':len(plan['books']), 'sections':len(plan['sections']),
            'candidate_concepts':len(plan['atoms']), 'hps_topics':len(plan['hps']),
            'target_cards':sum(plan['targets'].values())}
