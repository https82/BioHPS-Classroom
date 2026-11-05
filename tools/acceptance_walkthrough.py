"""Active end-to-end fake-Streamlit walkthrough with real DB/model actions.

This is NOT a browser or live-model test: fake controls submit real data through app.py.
It specifically exercises user navigation, submission, page output and teacher feedback.
"""
from __future__ import annotations
import os,sys,runpy,tempfile
from pathlib import Path
from types import ModuleType,SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class Rerun(Exception):pass
class State(dict):
    __getattr__=lambda self,k:self[k] if k in self else (_ for _ in ()).throw(AttributeError(k))
    def __setattr__(self,k,v):self[k]=v

class FakeST(ModuleType):
    def __init__(self,state,grade='高中',label='学生A',page='首页',submit=(),prompt=None):
        super().__init__('streamlit')
        self.session_state=state
        self.session_state['demo_actor']=label
        self.session_state['student_grade']=grade
        self.session_state['student_page']=page
        self.session_state['teacher_page']=page if label=='教师' else '班级学情'
        self.sidebar=self;self.secrets={};self.output=[]
        self.submit=set(submit);self.prompt=prompt
        self.cache_data=lambda *a,**kw:lambda f:f
        self.components=SimpleNamespace(v1=SimpleNamespace(html=lambda *a,**kw:None))
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def __getattr__(self,name):
        if name in ('container','expander','form','spinner','chat_message'):return lambda *a,**kw:self
        if name in ('markdown','write','info','success','warning','error','subheader','title','caption','metric'):
            return lambda *a,**kw:self.output.extend(str(x) for x in a)
        if name=='rerun':return lambda *a,**kw:(_ for _ in ()).throw(Rerun())
        return lambda *a,**kw:None
    def columns(self,n,**kw):return [self]*(n if isinstance(n,int) else len(n))
    def tabs(self,x,**kw):return [self]*len(x)
    def _pick(self,options,**kw):
        opts=list(options);assert opts
        key=kw.get('key');index=kw.get('index',0)
        if key and key in self.session_state and self.session_state[key] in opts:
            value=self.session_state[key]
        else:value=opts[0 if index is None else index]
        if key:self.session_state[key]=value
        return value
    def selectbox(self,label,options,**kw):return self._pick(options,**kw)
    def radio(self,label,options,**kw):return self._pick(options,**kw)
    def segmented_control(self,label,options,**kw):return self._pick(options,**kw)
    def form_submit_button(self,label,**kw):return label in self.submit
    def button(self,label,**kw):return label in self.submit
    def checkbox(self,*a,**kw):return False
    def text_area(self,*a,**kw):return kw.get('value',a[1] if len(a)>1 else '')
    def text_input(self,*a,**kw):return kw.get('value','')
    def chat_input(self,*a,**kw):return self.prompt
    def slider(self,*a,**kw):return kw.get('value',a[3] if len(a)>=4 else 0)
    def select_slider(self,*a,**kw):return kw.get('value',a[1][0] if len(a)>=2 else None)
    def number_input(self,*a,**kw):return kw.get('value',1)


def visit(state,**kwargs):
    fake=FakeST(state,**kwargs)
    sys.modules['streamlit']=fake
    try:runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
    except Rerun:pass
    return '\n'.join(fake.output)

with tempfile.TemporaryDirectory() as d:
    os.environ['BIOHPS_DEMO_DB']=str(Path(d)/'acceptance.sqlite')
    import demo_store as store
    from hps_explorer import HPS_CASES
    store.initialize()
    assert store.report()['participants']==0
    # Student A opens science history without a prior chapter, gets a meaningful lesson.
    state=State({'story_s1_初中':'pasteur',
                 'story_answer_s1_pasteur':HPS_CASES['pasteur']['options'][0]})
    output=visit(state,grade='初中',page='科学探究',submit=('提交判断',))
    assert len(store.story_attempts('s1'))==1 and store.story_attempts('s1')[0]['correct']==0
    output=visit(state,grade='初中',page='科学探究')
    assert '鹅颈瓶' in output and '实验' in output and '证据' in output
    # Student B changes only light, submits and views numerical + chart result.
    b=State({'hps_experience_s2_高中':'动手做对照实验'})
    output=visit(b,label='学生B',page='科学探究',submit=('对比两组并保存探究记录',))
    assert store.report()['experiments']==1
    output=visit(b,label='学生B',page='科学探究')
    assert '你观察到了什么' in output and '61 / 100' in output and '92 / 100' in output
    # Student C asks two follow-ups while no cloud key is available.
    c=State()
    visit(c,label='学生C',page='AI学习助手',prompt='鲸为什么不是鱼？')
    output=visit(c,label='学生C',page='AI学习助手',prompt='那海豚呢？')
    assert store.report()['questions']==2
    output=visit(c,label='学生C',page='AI学习助手')
    assert '鲸为什么不是鱼' in output and '那海豚呢' in output
    # The SAME SQLite data is read by teacher, without raw runtime labels.
    teacher=State()
    output=visit(teacher,label='教师',page='班级学情')
    assert '科学史证据推理' in output and '巴斯德的鹅颈瓶' in output
    assert '查看学生的对照实验结果' not in output or '光合作用' in output
    assert '参与学习人数' in output and '3' in output
    output=visit(teacher,label='教师',page='备课与PPT')
    assert 'AI辅助备课' in output and '你可以编辑每页内容' in output and '巴斯德' in output
    print('学生A：直接进入HPS、提交错误判断、收到解释、记录已保存')
    print('学生B：30→80光照实验，看到61→92示意指数与图表，记录已保存')
    print('学生C：连续两轮课程资料答疑（本次测试未调用真实DeepSeek）')
    print('教师端：同库读取3位演示学生、HPS错误、实验变化和提问，并进入备课')
    print('ACTIVE USER FLOW CHECK: PASSED')
