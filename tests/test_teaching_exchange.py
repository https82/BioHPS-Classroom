import copy
from io import BytesIO
import json
import pytest
import demo_store as ds
from question_bank import BANK
from teaching_exchange import (build_evidence,plan_template,validate_plan,json_text,
                              task_card,validate_task,as_lesson)
from lesson_planner import pptx_bytes


@pytest.fixture(autouse=True)
def isolated(monkeypatch,tmp_path):
    monkeypatch.setenv('BIOHPS_DEMO_DB',str(tmp_path/'demo.sqlite'))
    ds.initialize()


def seed():
    ds.add_attempt('s1',BANK['V10-M05'],0)
    ds.add_attempt('s1',BANK['V10-M05'],2)
    ds.add_attempt('s2',BANK['V10-M07'],0)
    ds.add_attempt('s3',BANK['V10-J01'],1)
    ds.add_question('s1','测交为什么是1:1？','高中','孟德尔分离定律','HS-028')
    ds.add_hps_event('s2','B2-S01','testcross',{'prediction_correct':False})


def test_student_data_stays_own_and_teacher_uses_only_selected_course():
    seed()
    own=build_evidence('B2-S01','s1')
    assert {e['learner_alias'] for e in own['evidence']}=={'demo-A'}
    group=build_evidence('B2-S01')
    assert group['summary']==dict(participants=2,attempts=3,incorrect_attempts=2,questions=1,hps_events=1)
    assert not any(e.get('question_id')=='V10-J01' for e in group['evidence'])
    assert group['scope']['truncated'] is False
    assert build_evidence('B2-S01','s4')['summary']['attempts']==0


def test_date_scope_and_identity_validation():
    seed()
    assert build_evidence('B2-S01',since='2100-01-01')['evidence']==[]
    with pytest.raises(ValueError):build_evidence('B2-S01','teacher')
    with pytest.raises(ValueError):build_evidence('B2-S01',since='2026-11-06',until='2026-11-05')
    with pytest.raises(ValueError):build_evidence(['B2-S01'])


def test_same_data_same_version_new_activity_invalidates_old_plan():
    seed();packet=build_evidence('B2-S01');text=json_text(plan_template(packet))
    assert packet['packet_id']==build_evidence('B2-S01')['packet_id']
    validate_plan(text,packet)
    ds.add_attempt('s1',BANK['V10-M06'],1)
    with pytest.raises(ValueError,match='版本不一致'):
        validate_plan(text,build_evidence('B2-S01'))


@pytest.mark.parametrize('change',('foreign_evidence','unknown_question','other_course','bad_sections'))
def test_mentor_import_rejects_fabricated_or_mismatched_references(change):
    seed();packet=build_evidence('B2-S01');plan=plan_template(packet)
    if change=='foreign_evidence':plan['evidence_ids']=['A-9999']
    if change=='unknown_question':plan['recommended_question_ids']=['imaginary-question']
    if change=='other_course':plan['recommended_question_ids']=['V10-J01']
    if change=='bad_sections':plan['sections']=plan['sections'][:6]
    with pytest.raises(ValueError):validate_plan(json_text(plan),packet)


def test_teacher_edits_reach_actual_editable_deck():
    from pptx import Presentation
    seed();packet=build_evidence('B2-S01');plan=plan_template(packet)
    plan['sections'][0]['bullets']=['教师审核后补充：先比较两种亲本的配子来源']
    plan=validate_plan(json_text(plan),packet)
    deck=Presentation(BytesIO(pptx_bytes(as_lesson(plan,packet))))
    assert len(deck.slides)==7
    assert any('教师审核后补充' in sh.text for sh in deck.slides[0].shapes if sh.has_text_frame)


def test_task_has_no_class_evidence_or_answers_and_recheck_feeds_teacher():
    seed();packet=build_evidence('B2-S01');plan=plan_template(packet)
    plan['recommended_question_ids']=['V10-M06','V10-M09']
    card=task_card(plan,'根据配子来源解释测交，再完成不同的题目。')
    text=json_text(card)
    assert 'reference_answer' not in text and 'demo-B' not in text and 'evidence' not in card
    loaded=validate_task(text)
    ds.add_attempt('s1',BANK[loaded['question_ids'][0]],BANK[loaded['question_ids'][0]]['answer'])
    after=build_evidence('B2-S01')
    assert after['summary']['attempts']==packet['summary']['attempts']+1
    assert after['summary']['incorrect_attempts']==packet['summary']['incorrect_attempts']
    tampered=copy.deepcopy(card);tampered['question_ids']=['V10-M10']
    with pytest.raises(ValueError,match='编号不一致'):validate_task(json_text(tampered))


def test_empty_data_does_not_invent_students_and_json_fences_supported():
    packet=build_evidence('B2-S01')
    assert packet['summary']['participants']==0
    assert validate_plan('```json\n'+json_text(plan_template(packet))+'\n```',packet)['evidence_ids']==[]
    with pytest.raises(ValueError):validate_plan('not json',packet)
