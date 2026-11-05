"""V8 curriculum and senior practice invariants; no external AI needed."""
import pytest
from pathlib import Path
from curriculum import (load_cards, load_all_cards, filter_stage, SENIOR_THEMES,
                        THEMES, retrieve, make_course_messages, sanitize_course_answer)
from senior_practice import SENIOR_BANK
import learning_loop

ROOT=Path(__file__).resolve().parents[1]
ALL=load_all_cards(ROOT)


def test_retains_existing_junior_notes():
    assert len(load_cards(ROOT))==153
    junior=filter_stage(ALL,'初中')
    assert len(junior)==153
    assert [c['id'] for c in junior]==[c['id'] for c in load_cards(ROOT)]


def test_high_school_modular_curriculum():
    senior=filter_stage(ALL,'高中')
    assert len(senior)==112
    assert {c['theme'] for c in senior}==set(SENIOR_THEMES)
    assert len(ALL)==265
    assert len({c['id'] for c in ALL})==len(ALL)


def test_high_school_notes_have_reviews_and_prompts():
    for c in filter_stage(ALL,'高中'):
        assert c['summary'] and c['guide_question'] and c['misconception']
        assert c['review_status']=='待教师审核'
        assert c['curriculum_reference'].startswith('https://')
        assert c['grade']=='高中'

@pytest.mark.parametrize('question,expected', [
    ('原核细胞与真核细胞区别是什么','HS-002'),
    ('减数分裂染色体数目变化','HS-025'),
    ('血糖调节胰岛素作用','HS-060'),
    ('为什么种群的环境容纳量会改变','HS-077'),
    ('PCR为什么需要引物','HS-104'),
])
def test_senior_auto_retrieval(question,expected):
    hits,_=retrieve(question,ALL,stage='高中',limit=5)
    assert expected in [x['id'] for x in hits]


def test_stage_blocks_cross_level_bleed():
    junior,_=retrieve('细胞结构',ALL,stage='初中')
    assert all(x['grade']=='初中' for x in junior)
    senior,_=retrieve('细胞结构',ALL,stage='高中')
    assert all(x['grade']=='高中' for x in senior)


def test_senior_model_prompt_is_high_school_level():
    hs=filter_stage(ALL,'高中')[:2]
    messages=make_course_messages('这些知识与高中遗传有什么关系？',hs,level='高中课程')
    assert '高中课程' in messages[0]['content']
    assert '高中生物学教学助手' in messages[0]['content']


def test_senior_citation_allowlist_and_fake_rejection():
    good=next(x for x in ALL if x['id']=='HS-025')
    assert 'HS-025' in sanitize_course_answer('参考资料卡：[HS-025]',[good])
    assert 'HS-999' not in sanitize_course_answer('参考资料卡：[HS-999]',[good])


def test_senior_exercises_valid_and_distinct():
    seniorids={c['id'] for c in filter_stage(ALL,'高中')}
    assert len(SENIOR_BANK)==15
    for cid,item in SENIOR_BANK.items():
        assert cid in seniorids
        assert item['misconception'] and item['remedy']
        questions=[]
        for phase in ('initial','recheck'):
            q,options,right=item[phase]
            assert q and len(options)==3 and len(set(options))==3
            assert type(right) is int and 0<=right<len(options)
            questions.append(q)
        assert questions[0]!=questions[1]


def test_senior_exercises_are_compatible_with_v7_engine(monkeypatch):
    monkeypatch.setitem(learning_loop.BANK,'HS-025',SENIOR_BANK['HS-025'])
    state=learning_loop.new_session('HS-025')
    q=learning_loop.current_question(state)
    state,event=learning_loop.submit_answer(state,(q['right']+1)%3)
    assert not event['correct']
    state=learning_loop.start_recheck(state)
    q=learning_loop.current_question(state)
    state,event=learning_loop.submit_answer(state,q['right'])
    assert event['correct'] and state['phase']=='passed'
