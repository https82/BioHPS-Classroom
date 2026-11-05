"""Offline full route smoke, including newly added teaching pages and roles.
This uses a UI stub and is NOT a real browser render or live DeepSeek test.
"""
import os, runpy, sys, tempfile
from types import ModuleType, SimpleNamespace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
class State(dict):
    __getattr__=lambda self,k:self[k] if k in self else (_ for _ in ()).throw(AttributeError(k))
    def __setattr__(self,k,v):self[k]=v
class FakeST(ModuleType):
    def __init__(self):
        super().__init__('streamlit')
        self.session_state=State();self.sidebar=self;self.secrets={}
        self.cache_data=lambda *a,**kw:lambda f:f
        self.components=SimpleNamespace(v1=SimpleNamespace(html=lambda *a,**kw:None))
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def __getattr__(self,name):
        if name in ('container','expander','form','spinner'):
            return lambda *a,**kw:self
        return lambda *a,**kw:None
    def selectbox(self,name,choices,**kw):return self._pick(choices,**kw)
    def radio(self,name,choices,**kw):return self._pick(choices,**kw)
    def _pick(self,choices,**kw):
        options=list(choices)
        assert options,f'UI choices empty'
        default=kw.get('index',0)
        v= self.session_state.get(kw.get('key'), options[default] if default is not None else options[0])
        if v not in options:v=options[0]
        if kw.get('key'):self.session_state[kw['key']]=v
        return v
    def columns(self,cols,**kw):return [self]*(cols if isinstance(cols,int) else len(cols))
    def form_submit_button(self,*a,**kw):return False
    def button(self,*a,**kw):return False
    def checkbox(self,*a,**kw):return False
    def text_area(self,*a,**kw):return kw.get('value','')
    def text_input(self,*a,**kw):return kw.get('value','')
    def slider(self,*a,**kw):return kw.get('value',a[3] if len(a)>=4 else 0)
    def select_slider(self,*a,**kw):return kw.get('value',a[1][0] if len(a)>=2 else None)
    def number_input(self,*a,**kw):return kw.get('value',1)
with tempfile.TemporaryDirectory() as td:
    os.environ['BIOHPS_DEMO_DB']=str(Path(td)/'demo.sqlite')
    count=0
    for actor in ('演示学生A','演示学生B','演示学生C','演示学生D','演示教师'):
        pages=['班级学情','课后问题与任务','备课与PPT'] if actor=='演示教师' else ['学课程','问AI','做练习','科学探究','我的学习']
        grades=['高中'] if actor=='演示教师' else ['初中','高中']
        for grade in grades:
            for page in pages:
                variants=[None]
                if grade=='高中' and page=='学课程' and actor!='演示教师':variants=['mendel','meiosis']
                for variant in variants:
                    subpages=['系统讲解','动手探究','章节检测','我的学习报告'] if variant else [None]
                    for subpage in subpages:
                        f=FakeST();f.session_state.demo_actor=actor;f.session_state.student_grade=grade
                        f.session_state['flag_course_'+{'演示学生A':'s1','演示学生B':'s2','演示学生C':'s3','演示学生D':'s4'}.get(actor,'s1')]=variant if variant else 'mendel'
                        f.session_state['flag_page_'+{'演示学生A':'s1','演示学生B':'s2','演示学生C':'s3','演示学生D':'s4'}.get(actor,'s1')]=subpage or '系统讲解'
                        def choose(label,choices,**kw):
                            if label in ('教师工作台','学生学习导航'):return page
                            return FakeST._pick(f,choices,**kw)
                        f.radio=choose
                        sys.modules['streamlit']=f
                        runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
                        count+=1
    print('OFFLINE UI BRANCHES PASS:',count)
