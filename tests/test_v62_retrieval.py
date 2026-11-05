"""The expanded course dataset and paraphrase/regression checks."""
import json
from pathlib import Path
import pytest
from curriculum import load_cards,retrieve,THEMES,resolve_course_context

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'knowledge'/'retrieval_smoke_cases.json').read_text(encoding='utf-8'))
CARDS=load_cards(ROOT)

def test_dataset_size_and_status():
    assert len(CARDS)==153
    assert {c['theme'] for c in CARDS}==set(THEMES)
    assert len({c['id'] for c in CARDS})==153
    assert all(c['review_status']=='待教师审核' for c in CARDS)
    assert all(c['source_title'] for c in CARDS)

@pytest.mark.parametrize('item',DATA,ids=[f"{i+1:02d}" for i in range(len(DATA))])
def test_retrieval_offline(item):
    hits,_=retrieve(item['question'],CARDS)
    ids=[c['id'] for c in hits]
    if item['expected'] is None:assert ids==[]
    else:assert item['expected'] in ids

@pytest.mark.parametrize('query',[
   '我的鲸鱼问题还想再讲简单点',
   '这个DNA和基因还有啥关系啊',
   '蒸腾作用在阴天会减少吗',
   '什么动物需要胎生哺乳',
   '肺动脉为什么含氧少',
])
def test_independent_paraphrases_have_some_relevant_card(query):
    hits,_=retrieve(query,CARDS)
    assert hits,query

def test_unrelated_question_never_carries_old_topic():
    previous={'knowledge_ids':['BIO-007']}
    hits,_=resolve_course_context('我的键盘为什么打不出字',CARDS,previous=previous)
    assert hits==[]
