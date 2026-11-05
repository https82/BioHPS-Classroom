"""Smoke-test page rendering with a minimal Streamlit stand-in.

This DOES NOT replace rendering in a real browser. It checks startup control-flow
when Streamlit cannot be installed in the packaging environment.
"""
import runpy
import sys
from pathlib import Path
from types import ModuleType

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class State(dict):
    def __getattr__(self,key):
        return self[key]
    def __setattr__(self,key,value):
        self[key]=value

class RerunSignal(Exception):
    pass

class FakeST(ModuleType):
    def __init__(self):
        super().__init__('streamlit')
        self.session_state=State()
        self.secrets={}
        self.sidebar=self
        self.simulate_submit=False
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def __getattr__(self,name):
        def dummy(*args,**kwargs):
            if name in ('expander','form','spinner','chat_message'):
                return self
            return None
        return dummy
    def radio(self,label,options,**kwargs):
        self.session_state.setdefault(kwargs.get('key','navigation'),options[0])
        return self.session_state[kwargs.get('key','navigation')]
    def columns(self,n,**kwargs):
        count = n if isinstance(n,int) else len(n)
        return [self]*count
    def selectbox(self,label,options,**kwargs):
        values=list(options)
        key=kwargs.get('key')
        if key and key in self.session_state and self.session_state[key] in values:
            return self.session_state[key]
        index=kwargs.get('index',0)
        selected=values[index]
        if key:self.session_state[key]=selected
        return selected
    def slider(self,label,lo,hi,value,step,*args,**kwargs):
        key=kwargs.get('key')
        if key and key in self.session_state:return self.session_state[key]
        if key:self.session_state[key]=value
        return value
    def toggle(self,*args,**kwargs): return True
    def button(self,*args,**kwargs): return False
    def chat_input(self,*args,**kwargs): return None
    def text_area(self,*args,**kwargs): return self.session_state.get(kwargs.get('key'),kwargs.get('value',''))
    def form_submit_button(self,label,*args,**kwargs):
        return self.simulate_submit and label.startswith(('发送给真实AI','发送给AI'))
    def rerun(self): raise RerunSignal()

pages=['🏠 智慧课堂首页','🧪 HPS实验探究','📊 学习诊断档案','📚 知识与科学史','🎬 项目与评委指南','💬 全课程AI课堂','🎯 自适应学练','🔬 虚拟实验室']
for page in pages:
    fake=FakeST()
    fake.session_state.navigation=page
    sys.modules['streamlit']=fake
    runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
    print('OK',page)

# V6 landing navigation: teacher and student CTA prefill without API calls.
fake=FakeST()
sys.modules['streamlit']=fake
module=runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
module['go_course']('鲸鱼为什么不是鱼？')
assert fake.session_state.navigation==pages[5]
assert fake.session_state.course_question=='鲸鱼为什么不是鱼？'
assert fake.session_state.course_mode=='知识理解'
assert fake.session_state.get('course_calls',0)==0
module['go_course']('请设计一节食物链课程','教师备课')
assert fake.session_state.course_mode=='教师备课'
assert fake.session_state.course_question=='请设计一节食物链课程'
print('OK V6 student and teacher navigation prefills without API calls')

# A mocked LLM call should not make a factually wrong hypothesis pass.
import json
import service
sample='我认为鹅颈瓶里肉汤没有出现微生物，是因为空气完全无法进入瓶内。'
service.call_ai=lambda _messages: {
    'ok':True,'model':'mocked-test-model', 'error':'', 'tokens':{'total_tokens':20},
    'text':json.dumps({'feedback':'鹅颈瓶没有封口；空气可以进入。你认为弯颈起了什么作用？',
                       'diagnosis':'学生误认为空气无法进入', 'evidence':'空气完全无法进入瓶内',
                       'achieved':True,'confidence':'high','concepts':[]},ensure_ascii=False),
}
fake=FakeST()
fake.session_state.navigation=pages[1]
fake.session_state.pending_prompt=(sample,'预置模拟输入')
fake.session_state.old_case='鹅颈瓶实验'
fake.simulate_submit=True
sys.modules['streamlit']=fake
try:
    runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
except RerunSignal:
    pass
assert len(fake.session_state.records)==1
assert fake.session_state.records[0]['advanced'] is False
assert fake.session_state.stage==0
assert '"achieved"' not in fake.session_state.records[0]['reply']
print('OK mocked-LLM interaction: rejected false pass, normal feedback')

# The new curriculum path should route a previously unsupported question and call the API.
service.call_ai=lambda _messages: {
  'ok': True,'model':'mocked-course-model','error':'','tokens':None,
  'text':'鲸属于哺乳动物，与其呼吸、哺育后代等特征有关。参考资料卡：[BIO-007]'
}
fake=FakeST()
fake.session_state.navigation=pages[5]
fake.session_state.course_question='鲸鱼为什么不是鱼？'
fake.simulate_submit=True
sys.modules['streamlit']=fake
try:
    runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
except RerunSignal:
    pass
assert fake.session_state.course_calls==1
assert len(fake.session_state.course_dialogues['自动识别||知识理解|初中通用'])==1
assert fake.session_state.course_dialogues['自动识别||知识理解|初中通用'][0]['ok']
print('OK mocked curriculum classroom: routed off-topic-from-old-demo question, obtained answer')

# Unseen lesson question: automatic AI fallback MUST work without choosing any chapter.
service.call_ai=lambda msgs: {
    'ok': True, 'model':'mocked-general-model', 'error':'', 'tokens':None,
    'text':'睡眠节律可能与昼夜变化及生物钟相关。参考资料卡：[BIO-999]'
}
fake=FakeST()
fake.session_state.navigation=pages[5]
fake.session_state.course_question='生物钟为什么影响睡眠？'
fake.simulate_submit=True
sys.modules['streamlit']=fake
try:
    runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
except RerunSignal:
    pass
records=fake.session_state.course_dialogues['自动识别||知识理解|初中通用']
assert fake.session_state.course_calls==1 and len(records)==1
assert records[0]['ok'] is True
assert records[0]['grounded'] is False
assert records[0]['knowledge_ids']==[]
assert 'BIO-999' not in records[0]['answer']
print('OK unmatched curriculum question: AI fallback ran, no fake card citation')

# V7 landing links and offline screen flow.
fake=FakeST()
sys.modules['streamlit']=fake
module=runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
module['go_learning']('BIO-007')
assert fake.session_state.navigation==pages[6]
assert fake.session_state.learning_card_choice=='BIO-007'
assert fake.session_state.get('course_calls',0)==0
module['go_lab']('种子萌发')
assert fake.session_state.navigation==pages[7]
assert fake.session_state.lab_kind=='种子萌发'
print('OK V7 navigation to offline learning and seed lab')

from learning_loop import new_session, current_question, submit_answer
fake=FakeST()
fake.session_state.navigation=pages[6]
fake.session_state.learning_card_choice='BIO-007'
s=new_session('BIO-007')
s,_=submit_answer(s,current_question(s)['right'])
fake.session_state.learning_sessions={'BIO-007':s}
sys.modules['streamlit']=fake
runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
print('OK V7 completed learning session rendered in offline stub')

from virtual_lab import make_trial
fake=FakeST()
fake.session_state.navigation=pages[7]
fake.session_state.lab_kind='光合作用'
confa={'light':20,'temperature':25,'co2':'充足','water':'充足'}
confb={'light':80,'temperature':25,'co2':'充足','water':'充足'}
fake.session_state.lab_trials={'光合作用':[make_trial('光合作用',confa,'弱光较低','A'),make_trial('光合作用',confb,'强光较高','B')],'种子萌发':[]}
sys.modules['streamlit']=fake
runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
print('OK V7 comparison with two recorded virtual trials rendered in offline stub')
