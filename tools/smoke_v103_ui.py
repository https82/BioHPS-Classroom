"""V10.3 no-network UI branch smoke with Streamlit stub, not browser QA."""
import os,runpy,sys,tempfile
from pathlib import Path
from types import ModuleType,SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
class State(dict):
    __getattr__=lambda self,k:self[k] if k in self else (_ for _ in ()).throw(AttributeError(k))
    def __setattr__(self,k,v):self[k]=v
class FakeST(ModuleType):
    def __init__(self):
        super().__init__('streamlit');self.session_state=State();self.sidebar=self;self.secrets={}
        self.cache_data=lambda *a,**kw:lambda f:f
        self.components=SimpleNamespace(v1=SimpleNamespace(html=lambda *a,**kw:None))
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def __getattr__(self,name):
        if name in ('container','expander','form','spinner'):return lambda *a,**kw:self
        return lambda *a,**kw:None
    def columns(self,n,**kw):return [self]*(n if isinstance(n,int) else len(n))
    def tabs(self,x,**kw):return [self]*len(x)
    def selectbox(self,label,options,**kw):return self._pick(options,**kw)
    def radio(self,label,options,**kw):return self._pick(options,**kw)
    def segmented_control(self,label,options,**kw):return self._pick(options,**kw)
    def _pick(self,options,**kw):
        opts=list(options);assert opts
        key=kw.get('key');index=kw.get('index',0)
        value=self.session_state.get(key,opts[0 if index is None else index]) if key else opts[0 if index is None else index]
        if value not in opts:value=opts[0]
        if key:self.session_state[key]=value
        return value
    def form_submit_button(self,*a,**kw):return False
    def button(self,*a,**kw):return False
    def checkbox(self,*a,**kw):return False
    def text_area(self,*a,**kw):return kw.get('value','')
    def text_input(self,*a,**kw):return kw.get('value','')
    def chat_input(self,*a,**kw):return None
    def slider(self,*a,**kw):return kw.get('value',a[3] if len(a)>=4 else 0)
    def select_slider(self,*a,**kw):return kw.get('value',a[1][0] if len(a)>=2 else None)
    def number_input(self,*a,**kw):return kw.get('value',1)
with tempfile.TemporaryDirectory() as tmp:
    os.environ['BIOHPS_DEMO_DB']=str(Path(tmp)/'demo.sqlite')
    count=0
    actor_map={'学生A':'s1','学生B':'s2','学生C':'s3','学生D':'s4'}
    for actor in ['学生A','学生B','学生C','学生D','教师']:
        student=actor_map.get(actor,'s1')
        grades=['高中'] if actor=='教师' else ['初中','高中']
        pages=['班级学情','课后问题与任务','备课与PPT'] if actor=='教师' else ['首页','课程学习','AI学习助手','章节练习','科学探究','学习档案']
        for grade in grades:
            for page in pages:
                variants=['按教材找知识','精讲课'] if grade=='高中' and page=='课程学习' else [None]
                for v in variants:
                    f=FakeST()
                    f.session_state.demo_actor=actor
                    f.session_state.student_grade=grade
                    f.session_state.student_page=page
                    f.session_state.teacher_page=page if actor=='教师' else '班级学情'
                    if v is not None:f.session_state[f'course_kind_{student}']=v
                    f.session_state[f'flag_course_{student}']='mendel'
                    sys.modules['streamlit']=f
                    runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
                    count+=1
    print('V10.3 OFFLINE UI BRANCHES PASS:',count)
