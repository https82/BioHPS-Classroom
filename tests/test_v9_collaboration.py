import os
from pathlib import Path
import pytest
from question_bank import BANK
from lesson_planner import make_plan, plan_markdown, pptx_bytes, ai_rewrite_messages
import demo_store as ds
from curriculum import load_all_cards

@pytest.fixture(autouse=True)
def isolated_database(monkeypatch,tmp_path):
    monkeypatch.setenv('BIOHPS_DEMO_DB',str(tmp_path/'demo.sqlite'))
    ds.initialize()


def test_question_bank_structure():
    assert len(BANK)==117
    assert sum(q['type']=='HPS科学探究' for q in BANK.values())==34
    assert sum(q['grade']=='高中' for q in BANK.values())==75
    assert sum(q['grade']=='初中' for q in BANK.values())==42
    assert len({q['id'] for q in BANK.values()})==117

@pytest.mark.parametrize('qid',list(BANK))
def test_each_question_has_valid_answer_and_original_card(qid):
    q=BANK[qid]
    assert q['question'] and q['explanation']
    assert 0<=q['answer']<len(q['options'])
    assert len(set(q['options']))==len(q['options'])
    assert q['card_id'] in {c['id'] for c in load_all_cards()}


def test_demo_records_are_real_actions_and_persistent():
    assert ds.report()['attempts']==0 and ds.report()['questions']==0
    q=BANK['HS-028-initial']
    ds.add_question('s1','孟德尔测交实验为什么需要隐性纯合子？','高中','测交与遗传推断','HS-030')
    out=ds.add_attempt('s1',q,(q['answer']+1)%len(q['options']))
    assert not out['correct']
    summary=ds.report()
    assert summary['participants']==1 and summary['questions']==1 and summary['wrong']==1
    assert len(ds.student_attempts('s1'))==1 and len(ds.student_questions('s1'))==1
    assert ds.student_attempts('s2')==[]


def test_teacher_gets_cross_role_activity_and_rechecks():
    q=BANK['HS-028-initial']
    ds.add_attempt('s1',q,(q['answer']+1)%len(q['options']))
    ds.add_attempt('s1',q,q['answer'])
    r=ds.student_summary('s1')
    assert r['answered']==2 and r['correct']==1
    assert len(r['needs_review'])==0  # latest answer supersedes old wrong answer
    assert ds.report()['wrong']==1  # teacher keeps all historical attempts


def test_only_known_demo_id_and_limits():
    with pytest.raises(ValueError): ds.add_question('other','我想学习孟德尔分离定律','高中','遗传')
    with pytest.raises(ValueError): ds.add_question('s1','a'*501,'高中','遗传')
    with pytest.raises(ValueError): ds.add_attempt('s1',BANK['HS-028-initial'],99)
    with pytest.raises(ValueError): ds.reset_demo()


def test_sql_parameters_not_injectable():
    malicious="'); DROP TABLE attempts; -- 孟德尔"
    ds.add_question('s1',malicious,'高中','测试')
    assert ds.student_questions('s1')[0]['text']==malicious
    assert ds.report()['attempts']==0


def test_assignment_and_teacher_reset():
    ds.post_assignment('高中','必修2','复习分离定律')
    assert len(ds.active_assignments())==1
    ds.close_assignment(ds.active_assignments()[0]['id'])
    assert ds.active_assignments()==[]
    ds.post_assignment('高中','必修2','探究练习')
    ds.reset_demo(confirmed=True)
    assert ds.active_assignments()==[]


def test_lesson_plan_grounded_and_editable():
    q=BANK['HS-028-initial']
    ds.add_question('s2','为什么分离定律需要测交来检验？','高中',q['topic'],q['card_id'])
    ds.add_attempt('s2',q,(q['answer']+1)%len(q['options']))
    r=ds.report()
    plan=make_plan(r)
    assert plan['topic']==q['topic']
    assert len(plan['sections'])==7
    md=plan_markdown(plan)
    assert '1次学生提问' in md and '1次答错' in md
    assert '演示' in md
    txt=''.join(str(x) for x in ai_rewrite_messages(plan))
    assert '演示学生B' not in txt and 's2' not in txt
    assert '匿名演示数据' in txt


def test_teacher_pptx_can_be_opened_and_customized():
    from pptx import Presentation
    from io import BytesIO
    plan=make_plan(ds.report(),'孟德尔分离定律')
    data=pptx_bytes(plan)
    prs=Presentation(BytesIO(data))
    assert len(prs.slides)==7
    assert int(prs.slide_width)>int(prs.slide_height)
    assert '孟德尔' in '\n'.join(sh.text for sh in prs.slides[0].shapes if sh.has_text_frame)
    custom=[['教师编辑的课堂问题']]+[[x for x in sec['bullets']] for sec in plan['sections'][1:]]
    prs=Presentation(BytesIO(pptx_bytes(plan,custom)))
    assert '教师编辑的课堂问题' in '\n'.join(sh.text for sh in prs.slides[0].shapes if sh.has_text_frame)


def test_demo_data_not_packed_as_source(tmp_path,monkeypatch):
    ds.add_question('s3','为什么DNA的两条链能够互补配对？','高中','DNA结构')
    assert Path(os.environ['BIOHPS_DEMO_DB']).exists()
    assert '演示学生C' not in str(ds.report()['question_topics'])


def test_experiment_reaches_teacher_records():
    from virtual_lab import make_trial, compare_trials
    a=make_trial('光合作用',{'light':30,'temperature':25,'co2':'充足','water':'充足'})
    b=make_trial('光合作用',{'light':80,'temperature':35,'co2':'充足','water':'充足'})
    result=compare_trials(a,b)
    assert not result['controlled']
    ds.add_experiment('s3','光合作用',result)
    assert ds.report()['experiments']==1
    assert ds.report()['experiment_control_errors']==1
    assert len(ds.student_experiments('s3'))==1
    assert ds.student_experiments('s2')==[]
