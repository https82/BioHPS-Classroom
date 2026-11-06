"""BioHPS V10.1 – restored student homepage and continuous AI learning assistant.

No student accounts, no real names, no real classroom claims. A fictional set of four
students share an SQLite demo store with one demonstration teacher. Not production-safe.
"""
from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import time

import streamlit as st

from curriculum import (load_all_cards, retrieve, resolve_course_context,
                        make_course_messages, sanitize_course_answer,
                        THEMES, SENIOR_THEMES)
from demo_store import (DEMO_STUDENTS, initialize, add_question, add_attempt,
                        student_summary, report, post_assignment, active_assignments,
                        reset_demo, close_assignment, add_experiment, student_experiments)
from lesson_planner import make_plan, plan_markdown, ai_rewrite_messages, pptx_bytes, hps_prompt
from virtual_lab import make_trial, compare_trials
from question_bank import BANK
from service import call_ai, read_config, config_status, provider_name
from teaching_exchange import learning_card_id
from hps_classroom import render_flagship, mendel_lab, meiosis_lab
from course_catalog import load_plan, books, chapters, sections, terms, matching_cards, deep_teaching_question
from section_lessons import get_section_core
from junior_theme_lessons import THEME_INTRO
from cell_theory_course import render_cell_lesson
from resource_library import by_selected_term, by_junior_card, search as search_resources, summary as resource_summary
from demo_store import hps_report, hps_events, story_attempts
from hps_explorer import render_explorer
from learning_insights import describe_event, human_issue, friendly_time, teacher_story_summary
from offline_tutor import offline_explanation, highlighted_course_context
from virtual_lab import visual_indicator, explain_observation
from lab_experience import render_lab
from dashboard_ui import (local_today,weekly_activity,student_numbers,teacher_numbers,
                          hero_html,metric_html,month_calendar,activity_html,accuracy_html,
                          progress_line,issue_html,esc)

st.set_page_config(page_title='探知·BioHPS | 师生协同生物学习',page_icon='🌱',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>
.block-container{max-width:1450px;padding-top:3.3rem!important;padding-bottom:3rem!important}
/* Reserve a stable top safe area: the Streamlit deployment toolbar must never cover headings. */
header[data-testid="stHeader"]{background:transparent!important;min-height:2.5rem!important}
[data-testid="stToolbar"]{display:none!important}
@media (max-width: 700px){.block-container{padding-top:4rem!important;padding-left:1rem!important;padding-right:1rem!important}}
h1{font-weight:760!important;letter-spacing:.3px}
[data-testid="stSidebar"]{background:#f4f8f5}
[data-testid="stChatMessage"]{border:1px solid #e2e9e5;border-radius:12px;padding:10px 14px}
.bio-hero{padding:26px 30px;border:1px solid #d8e7dd;border-radius:18px;background:linear-gradient(110deg,#f3faf5,#eef6f3);margin:0 0 18px}
.bio-hero h1{font-size:32px;color:#173c30;margin:.3em 0}
.bio-hero p{color:#50685f;margin:0;font-size:15px}
.bio-card{border:1px solid #dfe9e1;border-radius:13px;padding:18px 18px;margin:6px 0;background:#fff;min-height:132px;display:flex;flex-direction:column;gap:10px;box-sizing:border-box}
.bio-card h4{min-height:31px;line-height:1.45!important;margin:0}
.bio-card p{flex:1;min-height:48px}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{min-width:0}
.bio-card h4{margin:3px 0 7px;color:#164d3b}
.bio-card p{color:#596f65;line-height:1.6;margin:0}
[data-testid="stMetric"]{background:#f5f9f6;padding:14px;border-radius:13px;border:1px solid #e3ece5}
[data-testid="stHorizontalBlock"]{gap:1rem}
.stButton button[kind="primary"]{background:#236e54;border-color:#236e54}
.stButton button{border-radius:10px}
blockquote{border-left-color:#1f7455}

/* V10.7 DESKTOP LEARNING EXPERIENCE */
html{scroll-behavior:smooth}
[data-testid="stAppViewContainer"]{background:linear-gradient(180deg,#f8fbf9 0,#fff 300px)}
[data-testid="stSidebar"]{border-right:1px solid #dfe9e3;background:#f4f8f5!important}
[data-testid="stSidebar"] .stRadio label{line-height:1.55}
[data-testid="stMainBlockContainer"]{padding-left:2.35rem!important;padding-right:2.35rem!important}
.block-container{margin-left:auto;margin-right:auto}
.block-container p{line-height:1.72}
h1,h2,h3{color:#153e32!important;letter-spacing:-.3px!important}
h2{font-weight:750!important}
.stSelectbox>div,.stTextInput>div{border-radius:11px}
[data-testid="stChatMessage"]{background:#fff;box-shadow:0 3px 16px rgba(26,72,51,.035)}
[data-testid="stMetric"]{background:#fff;border:1px solid #e1ebe6;box-shadow:0 4px 20px rgba(26,72,51,.035);min-height:105px}
[data-testid="stHorizontalBlock"]{align-items:stretch}
[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{align-self:stretch}
.bio-hero{background:linear-gradient(110deg,#eaf6ee 0%,#f2f9f6 68%,#d8efe4 100%);border-color:#d2e9db;padding:36px 40px;min-height:186px;position:relative;overflow:hidden}
.bio-hero:after{content:'✦';position:absolute;right:6%;top:-21px;color:#b9e2c9;font-size:190px;line-height:1;opacity:.65;pointer-events:none}
.bio-hero h1{font-size:clamp(29px,3vw,42px);margin:10px 0 14px;position:relative;z-index:1}
.bio-hero p{position:relative;z-index:1;max-width:720px;font-size:16px}
.bio-card{min-height:185px;border:1px solid #dcece2;box-shadow:0 8px 27px rgba(14,74,45,.035);border-radius:20px;padding:25px;background:#fff;gap:13px;transition:box-shadow .2s}
.bio-card h4{font-size:20px;line-height:1.4!important;margin:0;color:#185540}
.bio-card p{font-size:14px;line-height:1.65;min-height:59px}
.bio-section-kicker{color:#23845c;font-size:12px;font-weight:800;letter-spacing:1.8px;margin:8px 0 7px}
.bio-lab-title{font-size:clamp(27px,2.6vw,36px)!important;margin:0 0 8px!important}
.bio-lead{font-size:15px;color:#60776d;max-width:860px;margin:0 0 22px}
.bio-lab-brief{border:1px solid #d5e8dd;border-radius:19px;background:linear-gradient(110deg,#eef8f2,#f9fcf9);padding:25px 30px;margin:12px 0 25px}
.bio-lab-brief h3{font-size:24px!important;margin:8px 0 12px!important}
.bio-lab-brief p{color:#51675d;font-size:15px}
.bio-step-tag{font-size:12px;letter-spacing:1.5px;color:#27845d;font-weight:800}
.bio-brief-goal{background:#fff;border-left:4px solid #2a8961;padding:13px 16px;border-radius:6px;margin-top:16px;line-height:1.8}
.bio-lab-preview{border-radius:20px;border:1px solid #d6e7e0;background:linear-gradient(#f2faf6,#ffffff);padding:19px 20px 21px;min-height:345px;box-shadow:0 8px 26px rgba(31,81,58,.04)}
.bio-lab-heading{display:flex;justify-content:space-between;align-items:center;font-size:18px;font-weight:750;color:#184737;gap:14px}
.bio-lab-heading span{font-size:12px;font-weight:500;color:#658276;background:#e8f3ed;padding:6px 10px;border-radius:99px;white-space:nowrap}
.bio-observation{text-align:center;color:#1b6848;font-size:19px;font-weight:800;margin:5px 0 8px}
.bio-note{font-size:12px;text-align:center;color:#627d70;line-height:1.6}
.bio-result-focus{border-left:4px solid #2e9c6a;background:#eef8f2;padding:18px 24px;border-radius:11px;margin:16px 0 22px}
.bio-result-focus h3{font-size:21px!important;margin:8px 0!important}
.bio-result-focus p{margin:0;color:#4c695c}
.bio-explanation{border:1px solid #ddeae3;border-radius:16px;background:#fff;padding:22px 26px;margin-bottom:18px}
.bio-explanation b{font-size:18px;color:#1a6549}
.bio-explanation p{margin:12px 0 3px;color:#3d574d}
.bio-empty-view{border:1px dashed #c3dcca;border-radius:16px;padding:28px;background:#f6faf7;margin-top:18px}
.bio-empty-view b{color:#246b4f}
.bio-empty-view p{color:#668174;margin:6px 0 0}
@media (max-width:900px){
 [data-testid="stMainBlockContainer"]{padding-left:1rem!important;padding-right:1rem!important}
 .bio-hero{padding:24px;min-height:0}
 .bio-hero:after{font-size:110px;right:0}
 .bio-card{min-height:150px}
 .bio-lab-preview{min-height:300px}
}
</style>''',unsafe_allow_html=True)

ROOT=Path(__file__).resolve().parent
st.markdown("<style>" + (ROOT/"dashboard_styles.css").read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)
initialize()

@st.cache_data(show_spinner=False)
def content():
    return load_all_cards(ROOT)

CARDS=content()
COURSE_PLAN=load_plan()
CARD_BY_ID={c['id']:c for c in CARDS}

ACTORS={'学生A':'s1','学生B':'s2','学生C':'s3','学生D':'s4','教师':'teacher'}


def card_title(cid):
    return CARD_BY_ID.get(cid,{}).get('title','相关课程知识')


def plain_response(text):
    lines=[]
    for line in str(text).splitlines():
        if line.strip().startswith(('参考资料卡：','知识卡编号：')):continue
        lines.append(line)
    return '\n'.join(lines).strip()


def set_student_page(page, question=None):
    """Real page navigation from the student home and contextual lesson buttons."""
    st.session_state['student_page']=page
    if question is not None:
        st.session_state['pending_ai_question']=question


def go_home_question(student,stage):
    q=st.session_state.get(f'home_question_{student}_{stage}','').strip()
    set_student_page('AI学习助手',q or None)


def go_flagship(student,slug):
    st.session_state[f'flag_course_{student}']=slug
    st.session_state[f'course_kind_{student}']='精讲课'
    set_student_page('课程学习')


def go_selected_knowledge(stage,book_code,section_id,term):
    section=next(s for s in COURSE_PLAN['sections'] if s['section_id']==section_id)
    book=COURSE_PLAN['books'][book_code]
    set_student_page('AI学习助手',deep_teaching_question(stage,book,section['section'],term))


def student_quick_actions(student):
    """Three actionable, aligned entry cards immediately below the welcome banner."""
    st.markdown('<div class="db-section-title db-quick-heading">快速开始学习</div>',unsafe_allow_html=True)
    destinations=[
        ('course','📘','课程学习','教材目录、知识详解和深度课程','课程学习'),
        ('hps','🧪','科学探究','科学家实验、证据推理与动手操作','科学探究'),
        ('ai','💬','AI学习助手','连续提问、解释难点、即时巩固','AI学习助手'),
    ]
    for col,(theme,icon,title,subtitle,target) in zip(st.columns(3,gap='medium'),destinations):
        with col:
            st.markdown(f'<div class="db-quick-card db-quick-{theme}">'
                        f'<span class="db-quick-icon">{icon}</span>'
                        f'<div class="db-quick-title">{title}</div>'
                        f'<div class="db-quick-sub">{subtitle}</div></div>',unsafe_allow_html=True)
            st.button('进入'+title+'  →',key=f'db_action_{student}_{target}',
                      on_click=set_student_page,args=(target,),use_container_width=True)


def student_landing(student,stage):
    """Real desktop dashboard. All scores and timelines use saved demo records."""
    info=student_summary(student)
    numbers=student_numbers(info)
    explored=hps_events(student_id=student)
    stories=story_attempts(student)
    labs=student_experiments(student)
    today=local_today()
    started=st.session_state.setdefault(f'learning_started_{student}',time.time())
    session_minutes=max(0,int((time.time()-started)//60))
    data=weekly_activity(info['questions'],info['attempts'],labs,explored,stories,today)
    name=DEMO_STUDENTS[student]['label']
    a,b=st.columns([1.95,1],gap='medium')
    with a:
        st.markdown(hero_html('🌱 探知 · BioHPS  /  '+stage+'生物',
            '你好，'+name.replace('演示','')+'！今天学点什么？',
            '初中七大学习主题与高中五本教材，课程、AI答疑、科学探究和练习自由切换。'),
            unsafe_allow_html=True)
    with b:
        st.markdown(month_calendar(today),unsafe_allow_html=True)
    # Put the most-used learning destinations ABOVE analytics and course history.
    student_quick_actions(student)
    st.markdown('<div class="db-stage-heading">📚 按学段浏览课程 <span>初中与高中均可自由学习</span></div>',unsafe_allow_html=True)
    junior_col,senior_col=st.columns(2,gap='medium')
    with junior_col:
        st.button('🌿 初中生物  ·  七大学习主题  →',key=f'db_open_junior_{student}',
                  on_click=open_stage_course,args=('初中',),use_container_width=True,
                  type='primary' if stage=='初中' else 'secondary')
    with senior_col:
        st.button('🧬 高中生物  ·  五本教材  →',key=f'db_open_senior_{student}',
                  on_click=open_stage_course,args=('高中',),use_container_width=True,
                  type='primary' if stage=='高中' else 'secondary')
    st.markdown('<div class="db-topgap"></div>',unsafe_allow_html=True)
    stats=st.columns(4,gap='medium')
    for col,(label,value,subtitle,icon) in zip(stats,[
            ('本次学习时间',f'{session_minutes} 分钟','本次浏览器会话的经过时间','◷'),
            ('已完成练习',numbers['answered'],'你的实际作答次数','✓'),
            ('答题正确率',f"{numbers['accuracy']}%" if numbers['accuracy'] is not None else '—',
             '尚未完成练习时不显示分数','◉'),
            ('待复习知识点',numbers['review'],'最近一次作答需要巩固的知识','↺')]):
        with col:
            st.markdown(metric_html(label,value,subtitle,icon),unsafe_allow_html=True)
    st.markdown('<div class="db-section-title">继续探索你的生物课程</div>',unsafe_allow_html=True)
    c_main,c_side=st.columns([1.85,1],gap='medium')
    with c_main:
        if stage=='高中':
            rec=[('必修2 · 遗传与进化','孟德尔的豌豆杂交实验','从性状分离现象出发，提出遗传假说、模拟杂交与测交。','mendel'),
                 ('必修2 · 遗传与进化','减数分裂与受精作用','观察染色体如何复制、配对和分离，理解遗传规律。','meiosis')]
            for idx,(tag,title,subtitle,slug) in enumerate(rec):
                st.markdown(f'<div class="db-course-tile"><span class="db-course-tag">{tag}</span>'
                    f'<div class="db-course-title">{title}</div><div class="db-course-desc">{subtitle}</div></div>',
                    unsafe_allow_html=True)
                st.button('继续学习这一课  →',key=f'db_course_{student}_{idx}',
                    on_click=go_flagship,args=(student,slug),use_container_width=True)
        else:
            st.markdown('<div class="db-course-tile"><span class="db-course-tag">初中生物 · 课程学习</span>'
                '<div class="db-course-title">从一个好问题开始</div>'
                '<div class="db-course-desc">选择初中学习主题，学习细胞、人体、遗传与环境等知识。</div></div>',
                unsafe_allow_html=True)
            st.button('浏览初中课程  →',key=f'db_junior_{student}',on_click=set_student_page,
                args=('课程学习',),use_container_width=True)
        st.markdown('<div class="db-panel"><div class="db-panel-title">🔍 向AI学习助手提问</div>'
            '<div class="db-panel-desc">从课程中遇到的问题出发，连续追问、举例和巩固。</div></div>',unsafe_allow_html=True)
        st.text_input('你的生物问题',placeholder='例如：孟德尔为什么要设计测交实验？',
            key=f'home_question_{student}_{stage}')
        st.button('和AI一起探讨  →',type='primary',key=f'db_homeask_{student}',
            on_click=go_home_question,args=(student,stage),use_container_width=True)
    with c_side:
        st.markdown('<div class="db-panel"><div class="db-panel-title">🗒️ 当前学习任务</div>'
            '<div class="db-panel-desc">老师布置的任务会同步到这里</div></div>',unsafe_allow_html=True)
        assign=[x for x in active_assignments() if x.get('stage')==stage]
        from collaboration_store import student_tasks
        assigned_tasks=[t for t in student_tasks(student) if len(t['answers'])<len(t['card']['question_ids'])]
        if assigned_tasks:
            st.info(f'有{len(assigned_tasks)}项导师专题任务待完成。')
            st.button('进入导师任务  →',key='home_mentor_tasks_'+student,on_click=set_student_page,
                      args=('学习档案',),use_container_width=True)
        if assign:
            for x in assign[:3]:
                st.markdown(f'<div class="db-course-tile"><div class="db-course-title">{esc(x["chapter"])}</div>'
                    f'<div class="db-course-desc">{esc(x["note"])}</div></div>',unsafe_allow_html=True)
            st.button('去完成练习  →',key=f'db_assigned_{student}',on_click=set_student_page,
                      args=('章节练习',),use_container_width=True)
        elif not assigned_tasks:
            st.markdown('<div class="db-empty">目前没有老师布置的任务。你可以自主选择知识点学习，'
                        '完成练习后会生成自己的错题记录。</div>',unsafe_allow_html=True)
            st.button('开始章节练习  →',key=f'db_quiz_{student}',on_click=set_student_page,
                      args=('章节练习',),use_container_width=True)
        st.markdown('<div class="db-topgap"></div>',unsafe_allow_html=True)
        unique_topics=len({r['topic'] for r in info['attempts']})
        st.markdown('<div class="db-panel"><div class="db-panel-title">📚 学习足迹</div>'
            +progress_line('已经练过的知识点',unique_topics,len({q['topic'] for q in BANK.values() if q['grade']==stage}),
                           '统计的是题库知识点，不是整本教材掌握度')+'</div>',unsafe_allow_html=True)
        st.button('查看我的学习档案  →',key=f'db_record_{student}',on_click=set_student_page,
                  args=('学习档案',),use_container_width=True)
        st.markdown('<div class="db-topgap"></div>',unsafe_allow_html=True)
        catalog=resource_summary()
        st.markdown('<div class="db-panel"><div class="db-panel-title">📁 课程资源库</div>'
                    f'<div class="db-stat-number">{catalog["total"]:,}</div>'
                    '<div class="db-panel-desc">初高中生物知识与科学史探究资源</div></div>',
                    unsafe_allow_html=True)
        st.button('按教材浏览资源  →',key=f'db_catalog_{student}',on_click=set_student_page,
                  args=('课程学习',),use_container_width=True)
    st.markdown('<div class="db-section-title">学习表现与活动</div>',unsafe_allow_html=True)
    left,right=st.columns([1.8,1],gap='medium')
    with left: st.markdown(activity_html(data),unsafe_allow_html=True)
    with right: st.markdown(accuracy_html(numbers['accuracy']),unsafe_allow_html=True)


def student_course(stage,student):
    st.title('课程学习')
    st.caption('当前学段：'+stage+'生物。你可以通过顶部“初中 / 高中”切换完整课程。')
    lookup=st.text_input('搜索知识点',placeholder='例如：四分体、光合作用、神经调节',
                         key=f'knowledge_search_{student}_{stage}')
    if lookup.strip():
        found=search_resources(lookup,stage=stage,limit=6)
        if found:
            st.markdown('#### 与你搜索内容有关的学习资料')
            for item in found:
                with st.expander(item['scope']+' · '+item['term']):
                    st.markdown(item['content'])
                    st.markdown('**想一想**：'+item['thinking_question'])
        else:
            st.caption('没找到完全对应的知识点，你也可以使用AI学习助手自由提问。')
    if stage=='高中':
        view=st.radio('学习入口',['按教材找知识','精讲课'],key=f'course_kind_{student}',horizontal=True)
        if view=='精讲课':
            st.write('选一节课，跟着讲解学习，再动手探究并完成练习。')
            render_flagship(student)
            st.divider()
            st.button('向AI追问本节课',key=f'flag_ask_{student}',on_click=set_student_page,
                      args=('AI学习助手', '我正在学习高中生物的孟德尔分离定律和减数分裂。请根据我的下一步提问耐心讲解，先问我具体哪里不理解。'))
            return
        # The five-book plan is a navigation MAP, not 854 fully written lectures.
        codes=books(COURSE_PLAN)
        book_code=st.selectbox('选择教材', [x[0] for x in codes],
                      format_func=lambda x:dict(codes)[x],key=f'book_{student}')
        ch=st.selectbox('选择章节',chapters(COURSE_PLAN,book_code),key=f'chapter_{student}_{book_code}')
        sects=sections(COURSE_PLAN,book_code,ch)
        sid=st.selectbox('选择小节',[x['section_id'] for x in sects],
                          format_func=lambda x:next(s['section'] for s in sects if s['section_id']==x),
                          key=f'section_{student}_{book_code}_{ch}')
        sec=next(x for x in sects if x['section_id']==sid)
        st.markdown('### '+sec['section'])
        core=get_section_core(sid)
        if core:
            st.markdown('#### 这一节要理解什么？')
            st.write(core)
        if sid=='B1-S01':
            render_cell_lesson(student)
            st.divider()
        if sid in ('B2-S01','B2-S03'):
            slug={'B2-S01':'mendel','B2-S03':'meiosis'}[sid]
            st.write('这节课可以跟着科学家做实验，一步步理解原理。')
            st.button('进入本节完整精讲',type='primary',key=f'go_flag_{student}_{sid}',
                      on_click=go_flagship,args=(student,slug))
        st.markdown('#### 本节知识路线')
        atoms=terms(COURSE_PLAN,sid)
        st.write(' → '.join(atoms))
        term=st.selectbox('我想深入学习',atoms,key=f'term_{student}_{sid}')
        matched=matching_cards(CARDS,book_code,term)
        st.markdown('#### 这一知识点的学习资料')
        resources=by_selected_term(sid,term)
        if resources:
            kinds=list(dict.fromkeys(r['category'] for r in resources))
            kind=st.segmented_control('我想学习',kinds,default=kinds[0],key=f'resource_kind_{student}_{sid}_{term}')
            options=[r for r in resources if r['category']==kind]
            for item in options[:2]:
                with st.container(border=True):
                    st.markdown(item['content'])
                    st.markdown('**想一想**：'+item['thinking_question'])
            if len(options)>2:
                with st.expander('继续深入学习'):
                    for item in options[2:]:
                        st.markdown(item['content'])
                        st.markdown('**尝试回答**：'+item['thinking_question'])
                        st.divider()
        elif matched:
            for c in matched[:1]:
                st.write(c['summary'])
        else:
            st.write('围绕这个知识点，可以先观察现象、理解概念，再联系本节相关知识。')
        st.button('让AI系统讲解这个知识点',type='primary',key=f'deep_{student}_{sid}_{term}',
                  on_click=go_selected_knowledge,args=(stage,book_code,sid,term))
        with st.expander('查看科学发现与探究线索'):
            relevant=[h for h in COURSE_PLAN['hps'] if h.get('book_code')==book_code and
                      (h.get('linked_section') in sec['section'] or sec['section'] in h.get('linked_section',''))]
            if relevant:
                for h in relevant:st.write('**'+h['title']+'**：'+h['driving_question'])
            else:st.write('可从本节相关实验、观察证据与历史研究方法切入。')
        return
    st.subheader('初中生物课程')
    themes=THEMES
    theme=st.selectbox('学习主题',themes,key=f'course_theme_{stage}')
    if theme in THEME_INTRO:
        st.markdown('### 主题导学')
        st.write(THEME_INTRO[theme])
    cards=[c for c in CARDS if c.get('grade','初中')==stage and c['theme']==theme]
    if not cards:
        st.write('换一个学习主题看看。');return
    by_id={c['id']:c for c in cards}
    cid=st.selectbox('选择知识点',list(by_id),format_func=lambda x:by_id[x]['title'],key=f'course_card_{stage}_{theme}')
    c=by_id[cid]
    st.markdown('### '+c['title'])
    st.write(c['summary'])
    resources=by_junior_card(cid)
    if resources:
        kinds=list(dict.fromkeys(r['category'] for r in resources))
        kind=st.segmented_control('学习重点',kinds,default=kinds[0],key=f'junior_kind_{student}_{cid}')
        options=[r for r in resources if r['category']==kind]
        for item in options[:2]:
            with st.container(border=True):
                st.markdown(item['content'])
                st.markdown('**想一想**：'+item['thinking_question'])
        if len(options)>2:
            with st.expander('继续深入学习'):
                for item in options[2:]:
                    st.markdown(item['content'])
                    st.markdown('**尝试回答**：'+item['thinking_question'])
                    st.divider()
    if c.get('guide_question'):st.info('再思考：'+c['guide_question'])
    st.button('让AI详细讲解并举例',type='primary',key=f'jr_deep_{student}_{cid}',
              on_click=set_student_page,args=('AI学习助手',deep_teaching_question(stage,theme,theme,c['title'])))
    st.button('查看相关练习',key=f'jr_quiz_{student}_{cid}',on_click=set_student_page,args=('章节练习',))


def student_ask(student,stage):
    """True multi-turn assistant, retains current student browser context and saves questions."""
    st.title('AI学习助手')
    st.write('任何生物问题都可以问。没听懂就继续追问，让AI举例、画思路或检查你的解释。')
    configured=config_status()['ready']
    status_key=f'ai_last_status_{student}_{stage}'
    if not configured:
        st.info('尚未设置在线AI，当前可使用课程资料学习。')
    elif st.session_state.get(status_key):
        st.warning('上一次在线AI调用失败：'+st.session_state[status_key])
    else:
        st.caption('已配置'+provider_name()+'。每次回答下方显示实际调用来源。')
    key=f'ai_chat_{student}_{stage}'
    if key not in st.session_state:st.session_state[key]=[]
    messages=st.session_state[key]
    if not messages:
        st.markdown('**可以这样开始**')
        prompts=('孟德尔为什么要进行测交实验？','减数第一次分裂与第二次分裂有什么不同？',
                 '光合作用的科学家是怎样一步步发现规律的？') if stage=='高中' else (
                 '鲸为什么不是鱼？','细胞和组织有什么区别？','怎么设计种子萌发的对照实验？')
        cols=st.columns(3)
        for idx,(col,q) in enumerate(zip(cols,prompts)):
            with col:
                st.button(q,key=f'ai_sample_{student}_{stage}_{idx}',use_container_width=True,
                          on_click=set_student_page,args=('AI学习助手',q))
    for entry in messages:
        with st.chat_message('assistant' if entry['role']=='assistant' else 'user'):
            st.markdown(entry['content'])
            if entry['role']=='assistant':
                # The source is based on the actual API response, not merely a configured key.
                if entry.get('origin')=='online':
                    model_name=entry.get('model') or '在线模型'
                    st.caption(f'本条回答：{entry.get("provider") or provider_name()}（{model_name}）')
                elif entry.get('origin')=='offline':
                    st.caption('本条回答：本地课程资料（未调用在线模型）')
                else:
                    st.caption('历史回答：未记录来源')
    if st.button('清空当前对话',key=f'clear_chat_{student}_{stage}'):
        st.session_state[key]=[]
        st.session_state.pop(status_key,None)
        st.session_state.pop(f'last_course_context_{student}_{stage}',None)
        st.rerun()
    pending=st.session_state.pop('pending_ai_question',None)
    incoming=st.chat_input('继续提问，例如：能不能用一个简单例子解释？',key=f'chat_input_{student}_{stage}')
    question=(pending or incoming or '').strip()
    if not question:return
    if len(question)<2:
        st.warning('可以再多说一点你想了解什么。');return
    if len(question)>1300:
        st.warning('问题太长了，请分成几个小问题。');return
    previous=st.session_state.get(f'last_course_context_{student}_{stage}')
    hits,_=resolve_course_context(question,CARDS,previous=previous,stage=stage,limit=3)
    extra=search_resources(question,stage=stage,limit=2)
    # A high-school learner may ask a middle-school prerequisite. Do not reject it.
    if not hits and not extra:
        hits,_=resolve_course_context(question,CARDS,previous=None,stage=None,limit=3)
        extra=search_resources(question,stage=None,limit=2)
    # The large library is used as a focused supplementary source, never injected in bulk.
    supplement=[{'id':r['id'],'theme':r['scope'],'title':r['term'],
                 'summary':r['content'].replace('**','').replace('\n',' ')[:900],
                 'misconception':'','guide_question':r['thinking_question']} for r in extra]
    grounding=(supplement[:1]+hits[:2]) if supplement else hits
    # Specific, teacher-authored explanatory material takes priority over generic match names.
    focused=highlighted_course_context(question,[(m['role'],m['content']) for m in messages[-6:]])
    if focused:
        grounding=[focused]+[g for g in grounding if g.get('id')!=focused['id']][:2]
    prev_history=[(m['role'],m['content']) for m in messages[-8:]]
    response='';source='已有课程内容'
    response_origin='offline';response_model=None;response_provider='';response_id=''
    if configured:
        try:
            from collaboration_store import reserve_request
            if reserve_request(student,'student_question'):
                with st.spinner('正在结合课程资料思考…'):
                    result=call_ai(make_course_messages(question,grounding,'知识理解',stage,history=prev_history))
            else:result={'ok':False,'error':'当前学习身份本小时的在线提问额度已用完，可继续浏览课程和练习。'}
        except Exception:
            result={'ok':False,'error':'调用遇到异常，请检查模型服务或网络设置'}
        if result.get('ok'):
            response=plain_response(sanitize_course_answer(result.get('text',''),grounding))
            if response:
                source='AI学习助手'
                response_origin='online'
                response_model=str(result.get('model') or read_config('BIOHPS_MODEL','在线模型'))
                response_provider=result.get('provider') or provider_name()
                response_id=result.get('response_id','')
                source=response_provider
                st.session_state.pop(status_key,None)
        else:
            # The next st.rerun() would otherwise remove this warning.
            # Keep the failure visible until a successful online response.
            st.session_state[status_key]=result.get('error','连接异常')
    if not response:
        response=offline_explanation(question,grounding,prev_history)
    topic=grounding[0]['title'] if grounding else '待归类问题'
    add_question(student,question,stage,topic,learning_card_id(grounding[0]['id']) if grounding else '',source)
    messages.extend([{'role':'user','content':question},
                     {'role':'assistant','content':response,'origin':response_origin,
                      'model':response_model,'provider':response_provider,'response_id':response_id}])
    st.session_state[f'last_course_context_{student}_{stage}']={'knowledge_ids':[h['id'] for h in grounding]}
    st.rerun()

def student_quiz(student,stage):
    st.subheader('✅ 章节练习')
    st.write('学完一节就来练练，做错的题可以在学习档案里复习。')
    mode=st.radio('选择练习', ['基础与理解','HPS科学探究','全部'] if stage=='高中' else ['基础与理解','全部'],horizontal=True,key=f'q_mode_{student}_{stage}')
    pool=[q for q in BANK.values() if q['grade']==stage and (mode=='全部' or q['type']==mode)]
    if not pool:
        st.info('当前学段还没有这一类型的预编写练习。');return
    chapters=sorted(set(q['chapter'] for q in pool))
    chapter=st.selectbox('课程模块',chapters,key=f'q_chapter_{student}_{stage}_{mode}')
    pool=[q for q in pool if q['chapter']==chapter]
    topics=sorted(set(q['topic'] for q in pool))
    topic=st.selectbox('学习知识点',topics,key=f'q_topic_{student}_{stage}_{mode}_{chapter}')
    pool=[q for q in pool if q['topic']==topic]
    scope=f'{student}|{stage}|{mode}|{chapter}|{topic}'
    if st.session_state.get('q_scope')!=scope:
        st.session_state.q_scope=scope
        st.session_state.q_cursor=0
    pos=st.session_state.get('q_cursor',0)%len(pool)
    q=pool[pos]
    st.caption(f'第 {pos+1}/{len(pool)} 题 · {q["type"]}')
    st.markdown('### '+q['question'])
    with st.form(f'answer_form_{student}_{q["id"]}'):
        choices=['请选择答案']+q['options']
        selected=st.radio('选择答案',choices,index=0,key=f'answer_choice_{student}_{q["id"]}')
        submit=st.form_submit_button('提交并查看反馈',type='primary')
    if submit:
        if selected==choices[0]:
            st.warning('请先选择一个答案。')
        else:
            result=add_attempt(student,q,choices.index(selected)-1)
            st.session_state[f'quiz_feedback_{student}_{q["id"]}']=result
            st.rerun()
    feedback=st.session_state.get(f'quiz_feedback_{student}_{q["id"]}')
    if feedback:
        if feedback['correct']:
            st.success('本题答对了。请继续说明为什么正确，才能证明自己真正理解。')
        else:
            st.error('这次没有选对。它已经进入你的错题记录。')
            st.write('**正确答案：** '+q['options'][q['answer']])
            st.write('**解析：** '+q['explanation'])
            st.caption('可巩固知识点：'+card_title(q['card_id']))
        st.button('做下一题',type='primary',on_click=next_quiz,args=(len(pool),),key=f'next_{student}_{q["id"]}')



def next_quiz(size):
    st.session_state.q_cursor=(st.session_state.get('q_cursor',0)+1)%size


HPS_STORIES={
    '细胞学说的建立':('研究者通过显微观察比较不同生物的细胞结构。',
                    '不同生物体有哪些共同的结构证据？为什么理论需要明确适用范围？'),
    '光合作用的发现与证据':('从观察植物放氧，到设计对照与同位素示踪，科学家逐渐完善解释。',
                    '同一实验中同时改变光照和温度，能说明哪个因素真正起作用吗？'),
    '孟德尔的假说与验证':('从豌豆杂交现象出发，提出遗传因子假说，并尝试通过测交验证。',
                    '理论上的3:1与每次观察的数据之间是什么关系？'),
    '测交的逻辑与设计':('用隐性纯合子与待测个体杂交，通过后代类型检验遗传解释。',
                    '为什么小样本的结果不能被解释成对所有情况的绝对证明？'),
    'DNA结构的证据链':('化学分析、X射线衍射和模型构建等不同线索共同推动双螺旋结构研究。',
                    '实验观察与结构模型有什么区别？科学合作为什么重要？'),
    '激素发现与实验推理':('研究消化液分泌时，科学家比较神经与体液途径，提出新的调节解释。',
                    '怎样设计实验区分两种可能的机制？'),
    'PCR与生物技术发展':('DNA扩增技术依赖基础研究，也进入检测与社会应用场景。',
                    '为什么必须同时考虑对照、污染与结果的适用范围？'),
}


def _lab_controls(kind,prefix):
    """Form-bound choices for exactly the fields supported by the V8 teaching model."""
    if kind=='光合作用':
        return {'light':st.slider('光照强度',0,100,30 if prefix=='A' else 80,key=f'{prefix}_light'),
                'temperature':st.slider('温度（℃）',5,45,25,key=f'{prefix}_temp'),
                'co2':st.selectbox('CO₂供应',['不足','适中','充足'],index=2,key=f'{prefix}_co2'),
                'water':st.selectbox('水分状态',['充足','不足'],key=f'{prefix}_water')}
    return {'moisture':st.selectbox('水分状态',['干燥','适量','完全浸没'],index=1,key=f'{prefix}_moisture'),
            'temperature':st.slider('温度（℃）',5,45,25,key=f'{prefix}_seedtemp'),
            'oxygen':st.selectbox('氧气条件',['充足','不足'],key=f'{prefix}_oxygen')}


def student_lab(student):
    """Teaching-first interactive inquiry; records are shared with teacher."""
    return render_lab(st,student)


def student_hps(student,stage):
    st.subheader('🔬 科学发现与动手探究')
    choices=['科学家与发现故事','豌豆杂交与测交','减数分裂推演','动手做对照实验'] if stage=='高中' else ['科学家与发现故事','动手做对照实验']
    method=st.radio('选择你想探索的内容',choices,horizontal=True,key=f'hps_experience_{student}_{stage}')
    if method=='豌豆杂交与测交':
        mendel_lab(student)
    elif method=='减数分裂推演':
        meiosis_lab(student)
    elif method=='动手做对照实验':
        student_lab(student)
    else:
        render_explorer(student,stage,set_student_page)


def student_record(student):
    st.subheader('📒 我的学习')
    from exchange_ui import render_student_exchange
    render_student_exchange(student)
    info=student_summary(student)
    a,b,c=st.columns(3)
    a.metric('提出问题',len(info['questions']))
    b.metric('答题记录',info['answered'])
    c.metric('答对次数',info['correct'])
    st.markdown('**建议复习**')
    if info['needs_review']:
        for topic,num in info['needs_review'].most_common(6):
            st.markdown(f'• **{topic}**：当前有{num}道不同练习的最近一次作答未正确，建议回看知识点后换题复测。')
    else:st.write('暂时没有需要优先补救的错题，继续完成章节练习。')
    with st.expander('查看最近练习'):
        if not info['attempts']:st.caption('暂无答题记录。')
        for r in info['attempts'][:20]:
            st.write(('✅ ' if r['correct'] else '❌ ')+r['topic']+' · '+r['question_id'])
    deep=hps_events(student_id=student)
    if deep:
        st.markdown('**科学探究学习记录**')
        st.write(f'已完成 {len(deep)} 次实验操作与证据判断。')
    stories=story_attempts(student)
    if stories:
        st.markdown('**科学发现与证据判断**')
        for rec in stories[:8]:
            st.write(('✅ ' if rec['correct'] else '↻ ')+rec['title']+' · '+('判断合理' if rec['correct'] else '建议重新分析证据'))
    labs=student_experiments(student)
    if labs:
        st.markdown('**实验设计记录**')
        for r in labs[:5]:
            st.write(('✅ ' if r['controlled'] else '🟠 ')+r['kind']+f' · 改变{r["changed_count"]}个条件')



def teacher_dashboard():
    """Teacher-facing entry dashboard, with raw evidence still accessible below."""
    data=report()
    n=teacher_numbers(data)
    st.markdown(hero_html('👩‍🏫 教师工作台  /  演示班级',
        '今天的课堂，从学生真正的问题开始',
        '查看学生答题与科学探究，整理班级共性困难，再为下一节课准备讲解与练习。',teacher=True),
        unsafe_allow_html=True)
    st.markdown('<div class="db-topgap"></div>',unsafe_allow_html=True)
    stats=st.columns(4,gap='medium')
    for col,(label,value,sub,icon) in zip(stats,[
        ('参与学习',n['participants'],'四名预设演示学生中的实际参与人数','♧'),
        ('学生提问',n['questions'],'已保存的课后问题','✎'),
        ('练习完成',n['attempts'],'班级累计作答次数','✓'),
        ('需要订正',n['wrong'],'当前累计错误作答','↺')]):
        with col: st.markdown(metric_html(label,value,sub,icon),unsafe_allow_html=True)
    st.markdown('<div class="db-section-title">教学概览</div>',unsafe_allow_html=True)
    left,middle,right=st.columns([1.45,1.0,1],gap='medium')
    with left:
        issues=sorted(((p['topic'],p['wrong']) for p in data['focus'] if p.get('wrong')),
                      key=lambda x:-x[1])
        st.markdown('<div class="db-panel db-panel-issues"><div class="db-panel-title">📌 班级重点知识</div>'
                    '<div class="db-panel-desc">按实际错误次数汇总，不预设成绩</div>'
                    +issue_html(issues)+'</div>',unsafe_allow_html=True)
    with middle:
        st.markdown(accuracy_html(n['accuracy'],'全班实际作答正确率'),unsafe_allow_html=True)
    with right:
        st.markdown(month_calendar(),unsafe_allow_html=True)
    st.markdown('<div class="db-section-title">为下一节课做准备</div>',unsafe_allow_html=True)
    l,r=st.columns([1.25,1],gap='medium')
    with l:
        st.markdown('<div class="db-panel db-panel-questions"><div class="db-panel-title">✍️ 最近的学生问题</div></div>',unsafe_allow_html=True)
        questions=data.get('recent_questions',[])
        if questions:
            for item in questions[:3]:
                who=DEMO_STUDENTS.get(item['student_id'],{}).get('label','学生')
                st.markdown(f'<div class="db-course-tile"><div class="db-course-tag">{esc(who)} · {esc(item["topic"])}</div>'
                            f'<div class="db-course-desc">{esc(item["text"])}</div></div>',unsafe_allow_html=True)
        else: st.info('还没有学生提问。切换学生身份提问后，这里就会出现记录。')
        st.button('查看问题与布置任务  →',key='db_teacher_questions',on_click=set_teacher_page,
                  args=('课后问题与任务',),use_container_width=True)
    with r:
        st.markdown('<div class="db-panel db-panel-prep"><div class="db-panel-title">📑 根据学情备课</div>'
                    '<div class="db-panel-desc">把真实错因和高频疑问转化为下一节课的教学重点。</div>'
                    '</div>',unsafe_allow_html=True)
        st.button('进入AI备课并导出PPT  →',key='db_teacher_prepare',type='primary',
                  on_click=set_teacher_page,args=('备课与PPT',),use_container_width=True)
        st.markdown('<div class="db-topgap"></div>',unsafe_allow_html=True)
        st.markdown('<div class="db-panel"><div class="db-panel-title">🏫 演示班级</div>'
                    '<div class="db-panel-desc">目前使用4名虚构学生身份；数据来自实际演示操作。</div>'
                    '</div>',unsafe_allow_html=True)
    with st.expander('展开班级完整统计与实验记录',expanded=False):
        teacher_dashboard_detail()


def teacher_dashboard_detail():
    st.subheader('📊 班级学习概况')
    if st.button('刷新班级记录',key='teacher_refresh'):
        st.rerun()
    summary=report()
    a,b,c,d=st.columns(4)
    a.metric('参与学习人数',summary['participants'])
    b.metric('课后提问',summary['questions'])
    c.metric('答题记录',summary['attempts'])
    d.metric('需要订正的作答',summary['wrong'])
    if summary['experiments']:
        st.caption(f'科学探究记录：{summary["experiments"]}组；其中{summary["experiment_control_errors"]}组存在对照设计问题。')
    from demo_store import all_experiments
    experiments=all_experiments()
    if experiments:
        with st.expander('查看学生的对照实验结果'):
            for rec in experiments[:12]:
                who=DEMO_STUDENTS.get(rec['student_id'],{}).get('label','学生')
                st.markdown(f'**{who} · {rec["kind"]}** · '+('对照合理' if rec['controlled'] else '需调整对照条件'))
                try:
                    details=json.loads(rec.get('details') or '{}')
                    obs=details.get('observation') or {}
                    if obs:st.write(f'第一组示意指数 {obs["first"]} → 第二组 {obs["second"]}。'+obs['reasoning'])
                    else:st.write('两组改变的条件：'+(rec['changed_fields'] or '无'))
                except (ValueError,KeyError,TypeError):
                    st.write('两组改变的条件：'+(rec['changed_fields'] or '无'))
    deep=hps_report()
    if deep['events']:
        st.markdown('**样板课程探究反馈**')
        st.write(f'课程操作记录 {deep["events"]} 条，涉及 {deep["participants"]} 名学生。')
        for label,cnt in sorted(deep['errors'].items(),key=lambda r:-r[1]):
            st.write(f'• {human_issue(label)}：{cnt}次需要调整')
        with st.expander('查看具体实验操作与反馈'):
            for rec in deep['recent'][:20]:
                label,feedback,ok=describe_event(rec)
                display_name=DEMO_STUDENTS[rec['student_id']]['label']
                st.markdown(('✅ ' if ok else '🟠 ')+f'**{display_name} · {label}** · {friendly_time(rec["created_at"])}')
                st.write(feedback)

    stories=story_attempts()
    if stories:
        st.markdown('**科学史证据推理**')
        for item in teacher_story_summary(stories)[:8]:
            st.write(f'• {item["title"]}：完成{item["attempts"]}次，需重新理解{item["wrong"]}次')
    if not summary['questions'] and not summary['attempts'] and not summary['experiments'] and not deep['events'] and not stories:
        st.info('暂时没有学习记录。请先让学生完成提问或练习。')
        return
    st.markdown('**最值得关注的知识点**')
    for item in summary['focus'][:6]:
        st.write(f'• **{item["topic"]}**：提问 {item["questions"]} 次，答题 {item["attempts"]} 次，答错 {item["wrong"]} 次')
    if summary['error_tags']:
        with st.expander('按错因查看'):
            for name,n in sorted(summary['error_tags'].items(),key=lambda x:-x[1]):
                st.write(f'{name}：{n}次')
    st.divider()
    st.markdown('**学生学习情况**')
    rows=[{'演示身份':x['name'],'提问':x['questions'],'答题':x['attempts'], '探究操作':x['hps_events'],
           '答对':x['correct'],'答错':x['wrong']} for x in summary['students']]
    st.dataframe(rows,hide_index=True,use_container_width=True)
    


def teacher_questions():
    st.subheader('💬 学生课后问题')
    data=report()
    if not data['recent_questions']:
        st.info('暂无学生提问，可以先布置练习任务。')
    st.markdown('**按知识点归类**')
    for topic,count in sorted(data['question_topics'].items(),key=lambda x:-x[1]):
        st.write(f'• {topic}：{count}条')
    with st.expander('展开查看学生原始提问'):
        for r in data['recent_questions']:
            name=DEMO_STUDENTS.get(r['student_id'],{}).get('label','演示身份')
            st.markdown(f'**{name} · {r["topic"]}**')
            st.write(r['text'])
    with st.expander('AI辅助总结班级问题'):
        
        if st.button('生成班级问题总结',key='teacher_summary_ai'):
            from lesson_planner import ai_report_messages
            with st.spinner('正在整理班级问题…'):
                result=call_ai(ai_report_messages(data))
            if result.get('ok'):
                st.session_state['teacher_issue_summary']=result['text']
            else:
                st.warning('AI当前未生成总结：'+result.get('error','未知原因'))
        if st.session_state.get('teacher_issue_summary'):
            st.markdown(st.session_state['teacher_issue_summary'])
    st.divider()
    st.markdown('**布置下一轮章节练习**')
    chapters=sorted({(q['grade'],q['chapter']) for q in BANK.values()})
    pick=st.selectbox('选择学段及课程模块',chapters,format_func=lambda x:x[0]+' · '+x[1])
    with st.form('assignment_form'):
        note=st.text_input('任务说明',value='完成本模块的基础练习，并挑选一道HPS探究题解释理由。')
        submitted=st.form_submit_button('发布练习',type='primary')
    if submitted:
        post_assignment(pick[0],pick[1],note)
        st.success('任务已发布。学生端刷新后可查看。')
    active=active_assignments()
    if active:
        st.markdown('**当前学习任务**')
        for a in active[:5]:
            c1,c2=st.columns([5,1])
            c1.write(f'{a["stage"]} · {a["chapter"]}：{a["note"]}')
            if c2.button('完成',key=f'close_{a["id"]}'):
                close_assignment(a['id']);st.rerun()


def teacher_prepare():
    st.subheader('🧑‍🏫 导师工作区 · AI辅助备课')
    from exchange_ui import render_mentor_exchange
    render_mentor_exchange()
    st.divider()
    st.markdown('### 原有备课与课程支持')
    data=report()
    options=['自动选择班级高频问题']+[r['topic'] for r in data['focus'][:8]]
    choice=st.selectbox('准备下一节课的主题',options)
    deep=hps_report()
    if choice==options[0] and not data['focus'] and deep['events']:
        from collections import Counter as _C
        most=_C(r['course_id'] for r in deep['recent']).most_common(1)[0][0]
        selected_topic='孟德尔分离定律' if most=='B2-S01' else '减数分裂'
    else:
        selected_topic='' if choice==options[0] else choice
    # Generic or unclassified AI questions should not displace a real science lesson.
    if selected_topic in ('','待归类问题','相关课程知识'):
        studies=story_attempts()
        if studies:
            selected_topic=teacher_story_summary(studies)[0]['title']
        elif deep['events']:
            most=Counter(r['course_id'] for r in deep['recent']).most_common(1)[0][0]
            selected_topic='孟德尔分离定律' if most=='B2-S01' else '减数分裂'
        elif data['experiments']:
            from demo_store import all_experiments
            selected_topic=all_experiments()[0]['kind']+'的对照实验'
    plan=make_plan(data,selected_topic)
    if deep['events']:
        plan['sections'][0]['bullets']=[b for b in plan['sections'][0]['bullets'] if not b.startswith('当前该知识点暂无')]
        plan['sections'][0]['bullets'].append(f'两节样板课共有{deep["events"]}条实际演示操作记录，涉及{deep["participants"]}个学生身份。')
        for issue,count in sorted(deep['errors'].items(),key=lambda x:-x[1])[:3]:
            plan['sections'][5]['bullets'].append(f'样板课程操作待改进：{human_issue(issue)}（{count}次记录）；建议安排针对性练习。')

    stories=story_attempts()
    if stories:
        for item in teacher_story_summary(stories)[:3]:
            if item['wrong']:
                plan['sections'][5]['bullets'].append(f'科学发现证据判断需巩固：{item["title"]}（{item["wrong"]}次需要调整）。')

    st.write('根据当前学习记录生成。你可以编辑每页内容，再导出可修改的课件。')
    if not data['questions'] and not data['attempts'] and not deep['events'] and not stories and not data['experiments']:
        st.info('暂时没有学生学情记录。可先选择学生身份完成探究与练习。')
    st.markdown('### '+plan['topic'])
    edits=[]
    for i,sec in enumerate(plan['sections']):
        with st.expander(f'{i+1}. {sec["title"]}',expanded=i==0):
            edits.append(st.text_area('可编辑内容','\n'.join(sec['bullets']),
                height=125,key=f'edit_{plan["topic"]}_{i}',label_visibility='collapsed'))
    cols=st.columns(2)
    from io import BytesIO
    # Use teacher changes in exported slide bullet points and Markdown.
    sections=[dict(title=sec['title'],bullets=[p.strip().lstrip('•- ') for p in edits[i].splitlines() if p.strip()])
              for i,sec in enumerate(plan['sections'])]
    edited_plan={**plan,'sections':sections}
    cols[0].download_button('下载备课大纲（Markdown）',plan_markdown(edited_plan).encode('utf-8'),
                            file_name='BioHPS_教师备课大纲.md',mime='text/markdown',use_container_width=True)
    try:
        deck=pptx_bytes(edited_plan)
        cols[1].download_button('下载可编辑PPT（7页）',deck,file_name='BioHPS_课堂备课初稿.pptx',
                                mime='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                                use_container_width=True)
    except ImportError:
        cols[1].warning('安装 python-pptx 后即可导出PPTX。')
    with st.expander('在线AI连接检查（教师）'):
        from service import config_status
        state=config_status()
        if state['ready']:
            st.success('在线AI已配置。可以在下方使用AI优化备课，也可回到学生端多轮提问。')
        else:
            st.info('本地尚未完成在线AI设置：'+ '、'.join(state['missing_labels']))
            st.write('可以使用项目中的“配置AI_安全迁移.ps1”，从旧版已配置项目复制本地Secrets；或者按使用说明手动配置。密钥不会上传或显示在这里。')
        if st.button('发送一次安全的连接测试',key='test_teacher_ai_connection',disabled=not state['ready']):
            tested=call_ai([{'role':'user','content':'请只回复：连接成功'}])
            if tested.get('ok'):
                st.success('模型回应：'+tested['text'][:80])
            else:
                st.error('连接失败：'+tested.get('error','未知原因'))
    with st.expander('使用在线模型进一步优化讲解与活动'):
        
        if st.button('让AI优化备课方案',key='ai_rewrite'):
            with st.spinner('正在整理备课建议…'):
                result=call_ai(ai_rewrite_messages(edited_plan))
            if result.get('ok'):
                st.session_state['ai_plan_text']=result['text']
            else:
                st.warning('AI尚未生成建议：'+result.get('error','未知错误'))
        if 'ai_plan_text' in st.session_state:
            st.markdown(st.session_state['ai_plan_text'])
            st.download_button('下载AI补充建议',st.session_state['ai_plan_text'].encode('utf-8'),
                               file_name='BioHPS_AI备课补充.md',mime='text/markdown')


# ----------------------------------------------------
# BioHPS V10.8: persistent teacher/student navigation and desktop top toolbar.
# Keep all existing functions and role records; no fictitious learner stats.
# ----------------------------------------------------
def set_teacher_page(page):
    st.session_state['teacher_page']=page


def switch_demo_role(target):
    """Switch explicitly to any of the four learners or the teacher.

    '返回学生端' is the only action that restores the last learner.
    """
    students = ('学生A','学生B','学生C','学生D')
    selected = st.session_state.get('demo_actor', '学生A')
    if target == '返回学生端':
        target = st.session_state.get('last_student_label', '学生A')
    if target not in students + ('教师',):
        target = '学生A'
    if target == '教师' and selected in students:
        st.session_state['last_student_label'] = selected
    if target != '教师':
        st.session_state['last_student_label'] = target
    st.session_state['demo_actor'] = target
    st.session_state['db_toolbar_actor'] = target
    if target == '教师':
        st.session_state['teacher_page'] = '班级学情'
    else:
        st.session_state['student_page'] = '首页'


def toolbar_role_changed():
    """All five demo identities remain accessible even with a collapsed sidebar."""
    switch_demo_role(st.session_state.get('db_toolbar_actor', '学生A'))


# Visible, one-click route buttons replace the old "跳转页面…" selectbox.
# All routes are real Streamlit controls (not decorative HTML links).
STUDENT_ROUTES=('首页','课程学习','AI学习助手','章节练习','科学探究','学习档案')
TEACHER_ROUTES=('班级学情','课后问题与任务','备课与PPT')
ROUTE_LABELS={
    '首页':'⌂  首页','课程学习':'▣  课程学习','AI学习助手':'◈  AI学习助手',
    '章节练习':'✓  章节练习','科学探究':'⚗  科学探究','学习档案':'▤  学习档案',
    '班级学情':'▦  班级学情','课后问题与任务':'✎  学生问题与任务',
    '备课与PPT':'▣  AI备课与PPT',
}


def direct_page_jump(target, teacher=False):
    permitted=TEACHER_ROUTES if teacher else STUDENT_ROUTES
    if target not in permitted:
        return
    st.session_state['teacher_page' if teacher else 'student_page']=target


# Full curriculum: two stages share one interface, accounts, knowledge and AI.
# Streamlit mounts sidebar widgets only while expanded, so mirror the stage in
# the ALWAYS-VISIBLE desktop toolbar. Callbacks run before widgets are rendered.
def toolbar_stage_changed():
    selected=st.session_state.get('db_toolbar_grade','初中')
    if selected in ('初中','高中'):
        st.session_state['student_grade']=selected


def open_stage_course(target):
    """Go to either complete stage directory without changing learner identity."""
    if target not in ('初中','高中'):
        return
    st.session_state['student_grade']=target
    st.session_state['db_toolbar_grade']=target
    st.session_state['student_page']='课程学习'


if st.session_state.get('student_grade') not in ('初中','高中'):
    st.session_state['student_grade']='初中'
if st.session_state.get('db_toolbar_grade') not in ('初中','高中'):
    st.session_state['db_toolbar_grade']=st.session_state['student_grade']



# V10.11: All navigation belongs in the visibly rendered LEFT workspace rail.
# Do not put a second nav strip in the content header, and do not depend on the
# collapsible Streamlit native sidebar: on some desktop zoom levels it vanished.
if st.session_state.get('demo_actor') not in ACTORS:
    st.session_state['demo_actor']='学生A'
actor_label=st.session_state['demo_actor']
actor=ACTORS[actor_label]
stage=st.session_state.get('student_grade','初中') if actor!='teacher' else '高中'
if stage not in ('初中','高中'):
    stage='初中'
    st.session_state['student_grade']=stage
if actor!='teacher':
    if st.session_state.get('student_page') not in STUDENT_ROUTES:
        st.session_state['student_page']='首页'
else:
    if st.session_state.get('teacher_page') not in TEACHER_ROUTES:
        st.session_state['teacher_page']='班级学情'
if st.session_state.get('db_toolbar_actor')!=actor_label:
    st.session_state['db_toolbar_actor']=actor_label

nav_col,content_col=st.columns([1.10,5.65],gap='medium',vertical_alignment='top')
with nav_col:
    # Marker also scopes the CSS to this one rail, never to normal course columns.
    st.markdown('<div class="db-workspace-nav-marker"></div>',unsafe_allow_html=True)
    st.markdown('''<div class="db-logo"><div class="db-logo-mark">✳</div>
      <div><div class="db-logo-title">探知 · BioHPS</div>
      <div class="db-logo-sub">AI生物学习与师生协同</div></div></div>''',unsafe_allow_html=True)
    st.markdown('<div class="db-side-rule"></div><div class="db-side-caption">'
      + ('教师工作区' if actor=='teacher' else '学习与教学导航')
      + '</div>',unsafe_allow_html=True)
    nav_is_teacher=(actor=='teacher')
    nav_routes=TEACHER_ROUTES if nav_is_teacher else STUDENT_ROUTES
    active_route=st.session_state.get('teacher_page' if nav_is_teacher else 'student_page')
    for idx,nav_target in enumerate(nav_routes):
        st.button(ROUTE_LABELS[nav_target],
                  key=f'db_left_route_{"teacher" if nav_is_teacher else "student"}_{idx}',
                  type='primary' if nav_target==active_route else 'secondary',
                  on_click=direct_page_jump,args=(nav_target,nav_is_teacher),
                  use_container_width=True)
    st.markdown('<div class="db-side-rule"></div>',unsafe_allow_html=True)
    if actor!='teacher':
        st.markdown('<div class="db-side-caption">当前学习</div>'
          f'<div class="db-side-person">◉ {esc(actor_label)} · {esc(stage)}生物</div>',
          unsafe_allow_html=True)
        if st.session_state.get('student_page')=='AI学习助手':
            st.caption('学生提问记录会自动保存到自己的学习档案。')
    else:
        st.markdown('<div class="db-side-person">▣ 演示班级 · 教师工作台</div>',
                    unsafe_allow_html=True)
        with st.expander('演示记录管理'):
            confirm=st.checkbox('确认清空演示记录',key='db_reset_confirm')
            if st.button('清空并重新演示',key='db_reset_demo',disabled=not confirm):
                reset_demo(confirmed=True)
                st.success('已清空演示活动记录。')
                st.rerun()
    st.markdown('<div class="db-sidebar-foot">从这里直接进入学习或教学功能。'
                '顶部可以切换初中、高中和四名演示学生。</div>',unsafe_allow_html=True)

with content_col:
    # Toolbar holds ONLY utilities. Navigation lives exclusively in the left rail.
    with st.container(border=True):
        header=st.columns([1.40,1.1,2.25,.60,1.15,1.25],gap='small',vertical_alignment='center')
        with header[0]:
            st.markdown('<div class="db-toplabel">探知 · BioHPS / '
                        +('教师' if actor=='teacher' else '学生')
                        +'</div><div class="db-topname">'
                        +esc(st.session_state.get('teacher_page','班级学情') if actor=='teacher'
                             else st.session_state.get('student_page','首页'))
                        +'</div>',unsafe_allow_html=True)
        with header[1]:
            if actor!='teacher':
                st.segmented_control('选择学段',['初中','高中'],key='db_toolbar_grade',
                                     on_change=toolbar_stage_changed,label_visibility='collapsed')
            else:
                st.markdown('<span class="db-all-stage">初中 · 高中</span>',unsafe_allow_html=True)
        with header[2]:
            if actor!='teacher':
                query=st.text_input('快速搜索课程',key='db_top_search',
                    placeholder='🔍 搜索课程、知识点、科学家…',label_visibility='collapsed')
                if query.strip() and query!=st.session_state.get('db_last_search'):
                    st.session_state['db_last_search']=query
                    st.session_state[f'knowledge_search_{actor}_{stage}']=query
                    st.session_state['student_page']='课程学习'
                    st.rerun()
            else:
                st.markdown('<div class="db-tophelper">班级分析 · AI备课 · 学习任务</div>',
                            unsafe_allow_html=True)
        with header[3]:
            today=local_today()
            st.markdown(f'<div class="db-topdate">{today.month}月{today.day}日</div>',
                        unsafe_allow_html=True)
        with header[4]:
            st.selectbox('切换学生或教师',list(ACTORS),key='db_toolbar_actor',
                         on_change=toolbar_role_changed,label_visibility='collapsed')
        with header[5]:
            st.button('👩‍🏫 教师端' if actor!='teacher' else '🎓 返回学生端',
                type='secondary',key='db_role_switch',
                on_click=switch_demo_role,args=('教师' if actor!='teacher' else '返回学生端',),
                use_container_width=True)

    if actor=='teacher':
        page=st.session_state['teacher_page']
        if page=='班级学情':teacher_dashboard()
        elif page=='课后问题与任务':teacher_questions()
        else:teacher_prepare()
    else:
        page=st.session_state['student_page']
        if page=='首页':student_landing(actor,stage)
        elif page=='课程学习':student_course(stage,actor)
        elif page=='AI学习助手':student_ask(actor,stage)
        elif page=='章节练习':student_quiz(actor,stage)
        elif page=='科学探究':student_hps(actor,stage)
        else:student_record(actor)
