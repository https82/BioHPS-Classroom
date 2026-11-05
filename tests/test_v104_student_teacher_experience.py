"""Acceptance tests designed around an actual student/teacher interaction, not menu counts."""
import os
import json
from pathlib import Path
import pytest
import demo_store as ds
from hps_explorer import HPS_CASES,available_cases,assess_case
from learning_insights import describe_event,human_issue,teacher_story_summary
from hps_models import MEIOSIS_STAGES
from virtual_lab import make_trial,compare_trials,visual_indicator,explain_observation
from offline_tutor import offline_explanation
import service

@pytest.fixture(autouse=True)
def demo_db(monkeypatch,tmp_path):
    monkeypatch.setenv('BIOHPS_DEMO_DB',str(tmp_path/'demo.sqlite'))
    ds.initialize()

@pytest.mark.parametrize('id',list(HPS_CASES))
def test_each_scientist_has_a_substantial_self_contained_lesson(id):
    h=HPS_CASES[id]
    assert len(h['scene']+h['evidence']+h['reasoning']+h['social'])>=130
    assert h['driving'] and h['q'] and h['why'] and h['misconception']
    assert len(h['options'])==3 and len(set(h['options']))==3
    assert assess_case(id,h['answer'])['correct']
    assert not assess_case(id,(h['answer']+1)%3)['correct']

@pytest.mark.parametrize('stage',('初中','高中'))
def test_student_can_open_HPS_without_completing_prior_lessons(stage):
    available=available_cases(stage)
    assert len(available)>=2 and 'cell' in available
    assert 'pasteur' in available
    assert 'mendel' in available if stage=='高中' else 'mendel' not in available


def test_student_wrong_answer_is_shared_with_teacher_and_remains_after_restart():
    assert ds.report()['participants']==0
    first=assess_case('pasteur',0)
    assert not first['correct']
    ds.add_story_attempt('s1','pasteur',HPS_CASES['pasteur']['title'],first['correct'],first['selected'])
    assert len(ds.story_attempts('s1'))==1
    assert ds.story_attempts('s2')==[]
    teacher=ds.report()
    assert teacher['participants']==1 and teacher['story_attempts']==1 and teacher['story_wrong']==1
    assert teacher_story_summary(ds.story_attempts())[0]['wrong']==1
    second=assess_case('pasteur',1)
    ds.add_story_attempt('s1','pasteur',HPS_CASES['pasteur']['title'],second['correct'],second['selected'])
    assert ds.report()['story_attempts']==2 and ds.report()['story_wrong']==1
    ds.reset_demo(confirmed=True)
    assert ds.story_attempts()==[]


def test_photosynthesis_30_80_visual_response_and_meaning():
    common={'temperature':25,'co2':'充足','water':'充足'}
    a=make_trial('光合作用',dict(common,light=30))
    b=make_trial('光合作用',dict(common,light=80))
    cmp=compare_trials(a,b)
    obs=explain_observation('光合作用',a,b,cmp)
    assert cmp['controlled'] and cmp['changed_labels']==['光照强度']
    assert obs['first']<obs['second'] and obs['difference']>=10
    assert '光照强度' in obs['reasoning']
    ds.add_experiment('s2','光合作用',cmp,first=a,second=b)
    record=ds.student_experiments('s2')[0]
    details=json.loads(record['details'])
    assert details['observation']['first']==obs['first']
    assert details['observation']['second']==obs['second']
    assert ds.report()['participants']==1 and ds.report()['experiment_control_errors']==0


def test_mixed_variables_cannot_be_treated_as_evidence_for_one():
    a=make_trial('光合作用',dict(light=30,temperature=25,co2='充足',water='充足'))
    b=make_trial('光合作用',dict(light=80,temperature=40,co2='充足',water='充足'))
    cmp=compare_trials(a,b)
    obs=explain_observation('光合作用',a,b,cmp)
    assert not cmp['controlled'] and '不能判断' in obs['reasoning']


def test_light_does_not_increase_photosynthesis_without_water():
    a=visual_indicator('光合作用',dict(light=80,temperature=25,co2='充足',water='不足'))
    b=visual_indicator('光合作用',dict(light=80,temperature=25,co2='充足',water='充足'))
    assert a<b


def test_seed_dry_or_missing_oxygen_is_unfavorable():
    base=dict(moisture='适量',temperature=25,oxygen='充足')
    good=visual_indicator('种子萌发',base)
    assert good>visual_indicator('种子萌发',dict(base,moisture='干燥'))
    assert good>visual_indicator('种子萌发',dict(base,oxygen='不足'))

@pytest.mark.parametrize('step',MEIOSIS_STAGES)
def test_teacher_can_read_all_meiosis_stages_in_biology_language(step):
    typ='meiosis_step'
    record={'event_type':typ,'data':{'stage':step['id'],'correct':False}}
    label,description,success=describe_event(record)
    assert label=='判断减数分裂阶段'
    assert step['title'] in description and not success
    assert step['title'] in human_issue('减数分裂：'+step['id'])

@pytest.mark.parametrize('kind,data',[
 ('pollination',{'correct':False}),('prediction',{'sound':False}),
 ('f2_trial',{'n':64,'high':46,'short':18}),('testcross',{'prediction_correct':False}),
 ('conclusion',{'sound':True})])
def test_teacher_events_are_human_readable(kind,data):
    label,description,success=describe_event({'event_type':kind,'data':data})
    assert label and description and kind not in label
    assert isinstance(success,bool)


def test_offline_tutor_is_useful_but_does_not_fake_an_llm():
    question='鲸为什么不是鱼？'
    docs=[{'title':'鲸属于哺乳动物','summary':'鲸需要肺呼吸，胎生并哺乳幼崽。','guide_question':'它和鲨鱼有哪些不同？'}]
    answer=offline_explanation(question,docs,history=[('user','鲸生活在哪里')])
    assert '肺呼吸' in answer and '哺乳' in answer and '检查理解' in answer
    assert 'DeepSeek已回答' not in answer


def test_api_connection_diagnostics_and_successful_mock(monkeypatch):
    monkeypatch.setattr(service,'read_config',lambda key,default='': {
        'BIOHPS_API_BASE':'https://api.deepseek.com/v1',
        'BIOHPS_MODEL':'test-model','BIOHPS_API_KEY':'test-only-token'}[key])
    assert service.config_status()['ready']
    class MockResponse:
        ok=True
        def json(self):return {'choices':[{'message':{'content':'连接成功'}}],'model':'test-model'}
    def mocked_post(url,**kwargs):
        assert url=='https://api.deepseek.com/v1/chat/completions'
        assert kwargs['headers']['Authorization']=='Bearer test-only-token'
        return MockResponse()
    result=service.call_ai([{'role':'user','content':'ping'}],requester=mocked_post)
    assert result['ok'] and result['text']=='连接成功'


def test_missing_ai_config_is_reported_without_showing_keys(monkeypatch):
    monkeypatch.setattr(service,'read_config',lambda key,default='': 'local-secret' if key=='BIOHPS_API_KEY' else '')
    result=service.config_status()
    assert not result['ready'] and 'API地址' in result['missing_labels']
    assert 'local-secret' not in str(result)


def test_5000_cards_and_117_questions_still_present():
    from resource_library import records
    from question_bank import BANK
    assert len(records())==5000 and len(BANK)==117


def test_product_secrets_not_checked_in():
    root=Path(__file__).resolve().parents[1]
    assert not (root/'.streamlit'/'secrets.toml').exists()
    assert (root/'配置AI_安全迁移.ps1').exists()
    assert 'secrets.toml' in (root/'.gitignore').read_text()


def test_placeholder_secrets_are_not_treated_as_connected(monkeypatch):
    monkeypatch.setattr(service,'read_config',lambda key,default='': {
        'BIOHPS_API_BASE':'https://api.deepseek.com/v1',
        'BIOHPS_MODEL':'请填写旧版已验证的模型名称',
        'BIOHPS_API_KEY':'请填写自己的API密钥'}[key])
    result=service.config_status()
    assert not result['ready']
    assert set(result['missing_labels'])=={'模型名称','API密钥'}
