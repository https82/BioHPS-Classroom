import json
import pytest
import demo_store as ds
import service
from question_bank import BANK
from teaching_exchange import build_evidence,plan_template,json_text,task_card
from collaboration_store import publish_task,student_tasks,submit_task_answer,reserve_request,task_progress


@pytest.fixture(autouse=True)
def isolated(monkeypatch,tmp_path):
    monkeypatch.setenv('BIOHPS_DEMO_DB',str(tmp_path/'isolated.sqlite'))
    ds.initialize()


def test_native_responses_protocol_ignores_reasoning_and_keeps_provenance(monkeypatch):
    config={'BIOHPS_API_BASE':'https://openapi.teleagi.cn/aipaas/telechat3-438b-a24b/v1',
            'BIOHPS_API_KEY':'test-key','BIOHPS_MODEL':'TeleChat3-438B-A24B'}
    monkeypatch.setattr(service,'read_config',lambda key,default='':config.get(key,default))
    class Response:
        ok=True;status_code=200
        def json(self):return {'id':'resp-test','status':'completed','model':'TeleChat3-438B-A24B',
            'output':[{'type':'reasoning','summary':[{'type':'summary_text','text':'PRIVATE'}]},
                      {'type':'message','content':[{'type':'output_text','text':'结论'}]}],
            'usage':{'input_tokens':10,'output_tokens':2}}
    def request(url,**kwargs):
        assert url.endswith('/v1/responses')
        assert kwargs['json']['input'][0]['role']=='system'
        assert kwargs['json']['reasoning']=={'effort':'none'}
        assert kwargs['json']['text']['format']['type']=='json_object'
        return Response()
    result=service.call_ai([{'role':'system','content':'教学规则'},{'role':'user','content':'问题'}],
                           requester=request,json_output=True)
    assert result['text']=='结论' and result['response_id']=='resp-test'
    assert result['provider']=='中国电信星辰大模型' and 'PRIVATE' not in result['text']


def test_legacy_helper_question_ids_are_in_topic_evidence():
    ds.add_question('s1','为什么测交不是3:1？','高中','测交','BIO-HLP-MENDEL','本地课程')
    ds.add_question('s2','姐妹染色单体如何分离？','高中','减数分裂','BIO-HLP-MEIOSIS','本地课程')
    assert build_evidence('B2-S01')['summary']['questions']==1
    assert build_evidence('B2-S03')['summary']['questions']==1
    assert build_evidence('B2-S01','s2')['summary']['questions']==0


def test_task_publish_is_idempotent_and_other_student_cannot_answer():
    packet=build_evidence('B2-S01');plan=plan_template(packet)
    card=task_card(plan,'先解释配子，再完成迁移练习。')
    assert publish_task(card,['s1'])==1
    assert publish_task(card,['s1'])==0
    assert student_tasks('s2')==[]
    task=student_tasks('s1')[0];qid=card['question_ids'][0]
    with pytest.raises(ValueError,match='不属于'):submit_task_answer('s2',task['id'],qid,0)
    submit_task_answer('s1',task['id'],qid,BANK[qid]['answer'])
    submit_task_answer('s1',task['id'],qid,BANK[qid]['answer'])
    assert build_evidence('B2-S01')['summary']['attempts']==1
    assert task_progress()[0]['answered']==1
    assert len(student_tasks('s1')[0]['answers'])==1
    ds.reset_demo(confirmed=True)
    assert student_tasks('s1')==[]


def test_request_budget_is_persistent_and_separate_per_identity():
    assert all(reserve_request('s1','student_question') for _ in range(30))
    assert not reserve_request('s1','student_question')
    assert reserve_request('s2','student_question')
    assert all(reserve_request('teacher','mentor_plan') for _ in range(12))
    assert not reserve_request('teacher','mentor_plan')


def test_mentor_agent_uses_scoped_evidence_and_validates_output():
    from mentor_agent import generate_plan
    ds.add_attempt('s1',BANK['V10-M05'],0)
    packet=build_evidence('B2-S01')
    def client(messages,**kwargs):
        assert kwargs['json_output']
        assert packet['packet_id'] in messages[1]['content']
        assert '有限后代全显性不能证明' in messages[0]['content']
        value=plan_template(packet)
        value['sections']=list(reversed(value['sections']))
        return {'ok':True,'text':json_text(value),'model':'test-model'}
    result=generate_plan(packet,client=client)
    assert result['ok'] and len(result['plan']['sections'])==7


def test_access_codes_lock_student_role_until_logout(monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    for sid in ('S1','S2','S3','S4','TEACHER'):
        monkeypatch.setenv('BIOHPS_ACCESS_'+sid,'test-access-'+sid)
    at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
    assert not at.exception
    assert any(b.label=='进入工作区' for b in at.button)
    at.text_input(key='login_access_code').set_value('test-access-S1')
    next(b for b in at.button if b.label=='进入工作区').click().run(timeout=30)
    assert at.session_state['_signed_actor']=='学生A'
    assert not any(s.key=='db_toolbar_actor' for s in at.selectbox)
    at.session_state['demo_actor']='教师'
    at.run(timeout=30)
    assert at.session_state['demo_actor']=='学生A'
    at.button(key='workspace_logout').click().run(timeout=30)
    assert any(b.label=='进入工作区' for b in at.button)
