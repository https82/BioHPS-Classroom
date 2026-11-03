"""A quality-gated content pipeline for the planned 5,000 resource cards.

Planning entries never become student-facing lesson cards until reviewed and approved.
Existing original V9 short-form cards remain in their separate knowledge lists.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
KINDS={'概念与机制','易错辨析','HPS科学史与证据','实验与建模','衔接与先修','应用伦理'}
REQUIRED={'card_id','section_id','node_ids','kind','title','explanation','misconception',
          'example','limits','source_urls','approval','reviewer','revision'}


def read_plan(root=ROOT):
    p=Path(root)/'knowledge'/'course_construction_plan.json'
    data=json.loads(p.read_text(encoding='utf8'))
    if len(data['sections'])!=82 or len(data['atoms'])!=854 or len(data['hps'])!=42:
        raise ValueError('课程蓝图数量与基线不符')
    if sum(s['quota'] for s in data['sections'])!=3400 or sum(data['targets'].values())!=5000:
        raise ValueError('课程配额未配平')
    return data


def validate_resource_card(card,plan=None):
    if not isinstance(card,dict):raise ValueError('资源必须为字典')
    missing=REQUIRED-card.keys()
    if missing:raise ValueError('缺少字段：'+','.join(sorted(missing)))
    if card['kind'] not in KINDS:raise ValueError('错误资源类型')
    if card['approval'] not in ('待审核','已审核','退回修改'):raise ValueError('审核状态无效')
    if not isinstance(card['node_ids'],list) or not card['node_ids']:
        raise ValueError('需要关联至少一个原子知识节点')
    if not isinstance(card['source_urls'],list) or not card['source_urls']:
        raise ValueError('必须提供可核验参考来源')
    if not isinstance(card['revision'],int) or card['revision']<1:
        raise ValueError('版本号无效')
    if not card['card_id'] or len(card['title'])<5:raise ValueError('无效标题')
    if len(card['explanation'])<180:raise ValueError('知识讲解过于简短，不能当成完整资源')
    if any(len(str(card[k]).strip())<10 for k in ('misconception','example','limits')):
        raise ValueError('误区、例证与模型边界不能只有空话')
    if card['approval']=='已审核' and not str(card['reviewer']).strip():
        raise ValueError('通过审核须记录复核人')
    plan=plan or read_plan()
    ids={s['section_id'] for s in plan['sections']}
    atoms={a['node_id'] for a in plan['atoms']}
    if card['section_id'] not in ids:raise ValueError('未列入五册章节的资源')
    if not set(card['node_ids'])<=atoms:raise ValueError('含不存在的原子知识节点')
    if not all(i.startswith(card['section_id']+'-') for i in card['node_ids']):
        raise ValueError('原子知识点与章节不匹配')
    return True


def load_reviewed_resources(root=ROOT):
    """Returns only cards explicitly approved after checks; no generated filler."""
    root=Path(root)
    plan=read_plan(root)
    folder=root/'knowledge'/'approved'
    files=sorted(folder.glob('*.json')) if folder.exists() else []
    approved=[];used=set()
    for file in files:
        records=json.loads(file.read_text(encoding='utf8'))
        if not isinstance(records,list):raise ValueError('成品文件应为资源数组')
        for card in records:
            validate_resource_card(card,plan)
            if card['card_id'] in used:raise ValueError('知识卡ID重复')
            used.add(card['card_id'])
            if card['approval']=='已审核':approved.append(card)
    return approved
