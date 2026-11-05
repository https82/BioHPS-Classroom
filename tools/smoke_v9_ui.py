"""Offline UI routing smoke. Does not claim real browser or paid API testing."""
import os
import runpy
import sys
import tempfile
from pathlib import Path
from types import ModuleType

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class State(dict):
    def __getattr__(self,k):
        try:return self[k]
        except KeyError:raise AttributeError(k)
    def __setattr__(self,k,v):self[k]=v

class FakeST(ModuleType):
    def __init__(self):
        super().__init__('streamlit')
        self.session_state=State()
        self.sidebar=self
        self.secrets={}
        self.cache_data=lambda *a,**k: lambda f:f
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def __getattr__(self,k):
        if k in ('container','expander','form','spinner'):
            return lambda *a,**kw:self
        return lambda *a,**kw:None
    def _choice(self,values,**kw):
        values=list(values)
        if not values:raise RuntimeError('Widget with empty options')
        key=kw.get('key')
        selected=self.session_state.get(key,values[kw.get('index',0)])
        if selected not in values:selected=values[0]
        if key:self.session_state[key]=selected
        return selected
    def selectbox(self,label,options,**kw):return self._choice(options,**kw)
    def radio(self,label,options,**kw):return self._choice(options,**kw)
    def columns(self,cols,**kw):return [self]*(cols if type(cols)==int else len(cols))
    def form_submit_button(self,*a,**kw):return False
    def button(self,*a,**kw):return False
    def checkbox(self,*a,**kw):return False
    def text_area(self,*a,**kw):return a[1] if len(a)>1 else kw.get('value','')
    def text_input(self,*a,**kw):return kw.get('value','')

with tempfile.TemporaryDirectory() as temp:
    os.environ['BIOHPS_DEMO_DB']=str(Path(temp)/'demo.sqlite')
    for actor in ('演示学生A','演示学生B','演示学生C','演示学生D','演示教师'):
        pages=(['学课程','问AI','做练习','科学探究','我的学习']
               if actor!='演示教师' else ['班级学情','课后问题与任务','备课与PPT'])
        stages=['初中','高中'] if actor!='演示教师' else ['高中']
        for stage in stages:
            for page in pages:
                fake=FakeST()
                fake.session_state.demo_actor=actor
                fake.session_state.student_grade=stage
                sys.modules['streamlit']=fake
                # Page widget's label is unique for teacher and student.
                old=fake.radio
                def choose(label,options,**kw):
                    if label in ('教师工作台','学生学习导航'):
                        return page
                    return old(label,options,**kw)
                fake.radio=choose
                try:
                    runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
                except Exception as exc:
                    raise RuntimeError(f'{actor}/{stage}/{page}: {type(exc).__name__}: {exc}') from exc
                print('PASS',actor,stage,page)
    print('PASS: 所有页面分支离线执行完成')
