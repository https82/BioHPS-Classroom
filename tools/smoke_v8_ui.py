"""Offline control-flow UI smoke for all V8 pages, no network or external Streamlit dependency."""
import runpy
import sys
from pathlib import Path
from types import ModuleType
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class State(dict):
    def __getattr__(self,k):
        try:return self[k]
        except KeyError: raise AttributeError(k)
    def __setattr__(self,k,v):self[k]=v

class FakeST(ModuleType):
    def __init__(self):
        super().__init__('streamlit'); self.session_state=State();self.sidebar=self;self.secrets={}
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def __getattr__(self,name):
        def dummy(*args,**kw):
            if name in ('expander','form','spinner','chat_message'):
                return self
            return None
        return dummy
    def _choice(self,opts,**kw):
        values=list(opts); k=kw.get('key')
        if not values: raise RuntimeError('Empty select widget: '+repr(kw))
        if k and k in self.session_state and self.session_state[k] in values:
            return self.session_state[k]
        idx=kw.get('index',0)
        v=values[idx]
        if k:self.session_state[k]=v
        return v
    def radio(self,label,options,**kw):return self._choice(options,**kw)
    def selectbox(self,label,options,**kw):return self._choice(options,**kw)
    def columns(self,n,**kw):return [self]*(n if isinstance(n,int) else len(n))
    def slider(self,label,low,high,default,step=1,**kw):
        k=kw.get('key')
        if k:self.session_state.setdefault(k,default)
        return self.session_state[k] if k else default
    def text_input(self,*args,**kw):return self.session_state.get(kw.get('key'),kw.get('value',''))
    def text_area(self,*args,**kw):return self.session_state.get(kw.get('key'),kw.get('value',''))
    def button(self,*args,**kw):return False
    def toggle(self,*args,**kw):return True
    def form_submit_button(self,*args,**kw):return False
    def chat_input(self,*args,**kw):return None

pages=['🏠 首页','🧠 科学探究','📊 学习记录','📚 科学故事','🧑‍🏫 教师与帮助',
       '💬 问问题','✅ 做练习','🧪 做实验','📖 学课程']
for page in pages:
    for stage in (['初中','高中'] if page in (pages[0],pages[5],pages[6],pages[8]) else ['初中']):
        fake=FakeST();fake.session_state.navigation=page;fake.session_state.site_stage=stage
        if page==pages[5]:fake.session_state.course_stage=stage
        if page==pages[6]:fake.session_state.practice_stage=stage
        if page==pages[8]:fake.session_state.catalog_stage=stage
        sys.modules['streamlit']=fake
        result=runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
        assert len(result['CURRICULUM_CARDS'])==265
        assert len(result['BANK'])==36
        if page==pages[0]:
            result['go_course']('为什么要研究细胞膜？',stage=stage)
            assert fake.session_state.navigation==pages[5]
            assert fake.session_state.course_stage==stage
        print('PASS',page,stage)

from curriculum import load_all_cards,filter_stage,retrieve,make_course_messages,sanitize_course_answer
cards=load_all_cards(ROOT)
assert len(filter_stage(cards,'初中'))==153
assert len(filter_stage(cards,'高中'))==112
queries=[('减数分裂为什么染色体数减半','HS-025'),('血糖如何通过胰岛素调节','HS-060'),('PCR为什么需要引物','HS-104'),('生态系统环境容纳量是什么','HS-077')]
for query,target in queries:
    choices,_=retrieve(query,cards,stage='高中',limit=5)
    assert target in [c['id'] for c in choices],(query,choices)
    print('PASS 高中检索',query,[(c['id'],c['title']) for c in choices[:3]])
assert '高中' in make_course_messages('解释减数分裂',filter_stage(cards,'高中')[:2],level='高中课程')[0]['content']
assert sanitize_course_answer('解释\n参考资料卡：[HS-025]',[next(x for x in cards if x['id']=='HS-025')]).endswith('[HS-025]')
print('PASS 课程范围、答案引用与高校分级')
