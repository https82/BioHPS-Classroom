"""100 authored/previously authored multiple-choice items, all deterministic to score.

72 items come unchanged from the V8 curated teaching bank (two per 36 knowledge points).
28 original HPS inquiry items are appended from knowledge/hps_questions.json.
No AI-generated question is ever silently treated as verified/graded.
"""
import json
from pathlib import Path
from learning_loop import BANK as JUNIOR_BANK
from senior_practice import SENIOR_BANK

ROOT=Path(__file__).resolve().parent


def load_bank(root=ROOT):
    root=Path(root)
    cards=json.loads((root/'knowledge'/'curriculum_cards.json').read_text(encoding='utf-8'))
    cards+=json.loads((root/'knowledge'/'high_school_cards.json').read_text(encoding='utf-8'))
    card_by_id={c['id']:c for c in cards}
    output={}
    for card_id, bundle in {**JUNIOR_BANK,**SENIOR_BANK}.items():
        c=card_by_id[card_id]
        for label,name in (('initial','初测'),('recheck','巩固')):
            stem, opts, answer=bundle[label]
            qid=f'{card_id}-{label}'
            output[qid]={
                'id':qid,'card_id':card_id,'grade':c.get('grade','初中'),
                'chapter':c.get('unit',c.get('theme','其他')),
                'topic':c['title'],'type':'基础与理解','stage':name,
                'question':stem,'options':list(opts),'answer':answer,
                'explanation':bundle.get('remedy',''),
                'error_tag':bundle.get('misconception','概念理解'),
                'origin':'V8预编写练习题（待教师审核）',
            }
    more=json.loads((root/'knowledge'/'hps_questions.json').read_text(encoding='utf-8'))
    for i,item in enumerate(more,1):
        card=card_by_id[item['card_id']]
        qid=f'HPS-{i:03d}'
        output[qid]={
            'id':qid,'grade':card.get('grade','高中'),
            'chapter':card.get('unit','未知'),'type':'HPS科学探究',
            'stage':'综合','origin':'V9原创HPS题（待教师审核）',
            **item,
        }
    _validate(output,card_by_id)
    return output


def _validate(bank, cards):
    for qid,q in bank.items():
        if not qid or q['card_id'] not in cards:
            raise ValueError(f'无效的知识点映射：{qid}')
        if not isinstance(q['question'],str) or len(q['question'])<8:
            raise ValueError(f'无效的题干：{qid}')
        opts=q['options']
        if not isinstance(opts,list) or len(opts)<2 or len(set(opts))!=len(opts):
            raise ValueError(f'选项无效：{qid}')
        if type(q['answer']) is not int or not 0<=q['answer']<len(opts):
            raise ValueError(f'答案越界：{qid}')
        if not q.get('explanation'):
            raise ValueError(f'缺少解析：{qid}')

BANK=load_bank()

# V10 flagship unit checks. Original V9 questions are preserved unchanged.
from flagship_questions import QUESTIONS as FLAGSHIP_QUESTIONS
BANK.update(FLAGSHIP_QUESTIONS)
