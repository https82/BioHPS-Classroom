"""BioHPS V6.2 – full-curriculum AI biology classroom with HPS inquiry specialty.

Important: all assessments are provisional, and example dialogues are developer-simulated.
"""
import hmac
import json
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

from engine import (
    CASES, CONCEPTS, RUBRIC, STAGES, STAGE_CRITERIA, CASE_OBJECTIVES,
    scaffold, make_competition_messages, parse_model_output,
    assess_transition, validate_concepts_strict, update_concept_state,
)
from presentation import PUBLIC_NAME, ONE_LINE, PRODUCT_VALUES, DEMO_STORY, CASE_PITCH, LIVE_EXAMPLES, clean_model_history
from service import call_ai, read_config
from curriculum import THEMES, MODES, OFFICIAL_CURRICULUM, load_cards, get_theme_cards, retrieve, resolve_course_context, make_course_messages, sanitize_course_answer

st.set_page_config(page_title='探知 BioHPS | AI生物智慧课堂', page_icon='🌱', layout='wide', initial_sidebar_state='expanded')

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700;800&display=swap');
:root {--pine:#153c32;--moss:#287c5c;--line:#e1eae4;--ink:#18352d;--muted:#688276;--cream:#f7faf6}
html,body,[class*="css"],.stApp {font-family:'Noto Sans SC','Microsoft YaHei',sans-serif}
.block-container{max-width:1400px;padding-top:1.5rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#f1f6f2;border-right:1px solid #e2eae4}
[data-testid="stSidebar"] *{color:#1e4137}
.hero{position:relative;background:linear-gradient(110deg,#133b30 0%,#216d50 100%);border-radius:20px;padding:31px 38px;margin:2px 0 24px;color:white;overflow:hidden}
.hero::after{content:"";position:absolute;right:-95px;top:-120px;border-radius:50%;width:345px;height:345px;border:55px solid rgba(237,255,241,.08)}
.hero h1{font-size:34px;font-weight:800;line-height:1.4;color:#fff;margin:7px 0 11px;letter-spacing:.5px}
.hero p{font-size:15px;line-height:1.9;color:#e4f3e7;margin:0;max-width:790px}
.eyebrow{color:#bcebd6;letter-spacing:2px;font-size:12px;font-weight:800}
.kicker{font-size:12px;letter-spacing:1.2px;font-weight:800;color:#388066;margin:10px 0 9px}
.section-head{font-size:23px;font-weight:750;color:#193e33;margin:12px 0 6px}
.subtitle{color:#617b6f;font-size:14px;line-height:1.8;margin:0 0 16px}
.value-card{border:1px solid #dce9e0;border-radius:17px;background:#fbfdfa;padding:18px 19px;min-height:130px}
.value-card .t{font-weight:750;font-size:17px;color:#1a4939;margin-bottom:8px}
.value-card .d{color:#597668;font-size:13px;line-height:1.75}
.story-card{border:1px solid #e2ebe5;border-radius:14px;background:#fff;padding:16px 18px;min-height:155px}
.story-card .tag{font-size:11px;font-weight:700;color:#37775b;letter-spacing:.5px;margin-bottom:6px}
.story-card .step-title{font-size:16px;font-weight:800;color:#204538;margin-bottom:7px}
.story-card .quote{font-size:14px;line-height:1.75;color:#2a4135}
.story-card .why{font-size:12px;color:#698576;margin-top:10px}
.disclaimer{font-size:12px;color:#607b6b;background:#f3f7f2;border:1px solid #e0ece0;border-radius:12px;padding:11px 14px;margin:10px 0 16px}
.story-divider{font-size:19px;color:#7fa38e;text-align:center;margin:4px}
[data-testid="stMetric"]{background:#f6faf7;border:1px solid #e1eae4;border-radius:13px;padding:12px}
[data-testid="stMetricValue"]{font-size:22px}
div[data-testid="stChatMessage"]{border-radius:13px;border:1px solid #e8efe9;padding:11px 14px}
div[data-testid="stChatMessage"] p{line-height:1.85}
[data-testid="stRadio"]{padding-bottom:8px}
@media(max-width:800px){.hero{padding:24px}.hero h1{font-size:26px}.block-container{padding-left:1rem;padding-right:1rem}}
</style>''',unsafe_allow_html=True)

ROOT=Path(__file__).resolve().parent
try:
    LIBRARY=json.loads((ROOT/'knowledge'/'library.json').read_text(encoding='utf-8'))
    CURRICULUM_CARDS=load_cards(ROOT)
except (FileNotFoundError, ValueError) as exc:
    st.error('知识库文件缺失或格式无效，软件暂时无法启动课程教学。请确认已复制完整的 knowledge 文件夹。')
    st.code('必须包含：knowledge/library.json 及 knowledge/curriculum_cards.json')
    st.caption('可以重新从升级压缩包中复制整个 knowledge 文件夹。')
    st.stop()

NAV=['🏠 智慧课堂首页','🧪 HPS实验探究','📊 学习诊断档案','📚 知识与科学史','🎬 项目与评委指南','💬 全课程AI课堂']
NAV_ORDER=[NAV[0],NAV[5],NAV[2],NAV[1],NAV[3],NAV[4]]


def reset():
    for key in ('history','stage','mastery','records','concept_state','last_model','last_status','usage','pending_prompt','api_calls'):
        st.session_state.pop(key,None)


def go(target, prompt=None, sample_label=None):
    st.session_state['navigation']=target
    if prompt is not None:
        st.session_state['pending_prompt']=(prompt,sample_label or '预设模拟输入')


def go_course(question='', mode='知识理解'):
    """Navigation callback: prefill question without triggering a paid API call."""
    st.session_state['navigation']=NAV[5]
    st.session_state['course_mode']=mode
    st.session_state['course_theme']='自动识别'
    st.session_state['course_topic']='根据问题检索'
    st.session_state['course_question']=question


def headline(title, subtitle=''):
    st.markdown(f'<div class="section-head">{escape(title)}</div>',unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="subtitle">{escape(subtitle)}</div>',unsafe_allow_html=True)


def card(title, content):
    st.markdown('<div class="value-card"><div class="t">'+escape(title)+'</div><div class="d">'+escape(content)+'</div></div>',unsafe_allow_html=True)


def _metric_items():
    return [
        ('实验场景','3个','实际配置'),
        ('探究阶段','4步','由规则+模型暂定评价'),
        ('概念理解',f'{len(st.session_state.concept_state)}/{len(CONCEPTS[case])}','记录而非正式分数'),
        ('本次AI请求',str(st.session_state.api_calls),'仅计当前浏览器会话'),
    ]


def _public_demo():
    headline('30秒看懂：学生如何从错误认识走向可检验预测',
             '以下内容来自开发阶段的模拟输入测试，是教学功能展示，不是真实学生实验或效果证明。')
    r1=st.columns(2,gap='medium')
    r2=st.columns(2,gap='medium')
    for col,item in zip([*r1,*r2],DEMO_STORY):
        with col:
            st.markdown('''<div class="story-card"><div class="tag">'''+escape(item['who'])+'</div><div class="step-title">'+escape(item['title'])+'</div><div class="quote">“'+escape(item['body'])+'”</div><div class="why">'+escape(item['meaning'])+'</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="disclaimer">开发者预置演示场景 · 非现场学生测评 · 未计入任何实验统计。正式效果需通过相同模型的对照测试与教师复核验证。</div>',unsafe_allow_html=True)


# Optional access PIN for a public judge-facing deployment. This is not full user authentication.
access_pin=str(read_config('BIOHPS_DEMO_PIN','') or '').strip()
if access_pin:
    st.markdown('<div class="hero"><div class="eyebrow">BIOHPS · PRIVATE JURY PREVIEW</div><h1>探知 · BioHPS</h1><p>此链接为受控评委体验入口。</p></div>',unsafe_allow_html=True)
    with st.form('access_form'):
        candidate=st.text_input('请输入评委体验码',type='password')
        entered=st.form_submit_button('进入体验')
    if entered and hmac.compare_digest(candidate,access_pin):
        st.session_state['pin_authorized']=True
    if not st.session_state.get('pin_authorized',False):
        st.info('如您是评委，请使用作品提交材料中的测试凭据进入。')
        st.stop()

with st.sidebar:
    st.markdown('### 🌱 探知 BioHPS')
    st.caption('AI BIOLOGY CLASSROOM')
    st.divider()
    st.markdown('**全课程AI学习是主线**')
    st.caption('跨章节自由问答 · 互动练习 · 错误诊断 · 教师备课')
    st.markdown('**特色：HPS科学探究**')
    st.caption('科学史与证据推理 · 三个深度实验案例')
    st.divider()
    if 'selected_case' not in st.session_state:
        st.session_state['selected_case']=list(CASES)[0]
    if st.session_state.get('navigation') in (NAV[1],NAV[2],NAV[3]):
        st.selectbox('当前实验场景',list(CASES),format_func=lambda name:{
            '鹅颈瓶实验':'01　巴斯德鹅颈瓶实验',
            '光合作用':'02　光照与光合作用',
            '种子萌发':'03　种子萌发条件探究'}[name],key='selected_case')
    case=st.session_state['selected_case']
    use_ai=st.toggle('开启实时AI',value=True,help='发起真实请求后按模型API价格计费。')
    if st.session_state.get('navigation') in (NAV[1],NAV[2]):
        if st.button('↻ 重置HPS实验',use_container_width=True):
            reset();st.rerun()
    st.divider()
    st.caption('配置模型：'+(read_config('BIOHPS_MODEL') or '未配置'))
    st.caption('课程问答仅在点击“发送给AI”后计费；不要输入学生个人隐私。')
    st.caption('BioHPS V6.2 · AI生物智慧课堂')
    st.caption('课程资料与AI反馈未经逐条学科教师审核。')

if st.session_state.get('old_case')!=case:
    reset();st.session_state['old_case']=case
for key,default in (
    ('history',[]),('stage',0),('mastery',[False]*4),('records',[]),('concept_state',{}),
    ('last_model','未调用'),('last_status','等待开始'),('usage',[]),('pending_prompt',None),('api_calls',0),
    ('navigation',NAV[0]),
):
    if key not in st.session_state:
        st.session_state[key]=default

objective=CASE_OBJECTIVES[case]
card_info=LIBRARY[case]

st.markdown('<div class="hero"><div class="eyebrow">BIOHPS · AI BIOLOGY CLASSROOM</div>'
            '<h1>探知·BioHPS ｜ 你的AI生物学习伙伴</h1>'
            '<p>从细胞到生态，从人体到遗传：随问随学、启发思考、互动练习、智能纠错。'
            '<br>全课程AI学习是主线，HPS科学探究是特色。</p>'
            '</div>',unsafe_allow_html=True)

st.radio('主导航',NAV_ORDER,key='navigation',horizontal=True,label_visibility='collapsed')
st.divider()
page=st.session_state.navigation

if page==NAV[0]:
    headline('生物有疑问？现在就问AI',
             '从“鲸鱼为什么不是鱼”到“DNA和染色体有什么关系”，先解决学习问题，再通过追问、练习和诊断巩固理解。')
    st.markdown('<div class="kicker">选一个问题，立即体验全课程AI课堂</div>',unsafe_allow_html=True)
    quick=[
        ('🐋 鲸鱼为什么不是鱼？','为什么鲸虽然生活在水中，却属于哺乳动物？'),
        ('🫁 肺泡如何交换气体？','肺泡的哪些结构特点有利于气体交换？'),
        ('🧬 DNA、基因与染色体','DNA、基因与染色体之间是什么关系？'),
    ]
    for col,(label,question) in zip(st.columns(3,gap='medium'),quick):
        with col:
            st.button(label,key='quick_'+label,use_container_width=True,
                      on_click=go_course,args=(question,))
    learn, teach = st.columns([1.7,1],gap='medium')
    with learn:
        st.button('🚀 立即向AI提问 · 自由输入',type='primary',use_container_width=True,
                  on_click=go_course,args=('',))
    with teach:
        st.button('👩‍🏫 我是教师 · 辅助备课',use_container_width=True,
                  on_click=go_course,args=('请围绕食物链设计一节初中生物课堂活动。','教师备课'))
    st.caption('点击仅填入问题，不会自动产生模型费用；点击课堂中的“发送给AI”后才会实际调用。')

    headline('不止回答问题：一个平台，五种教学能力','围绕学生学习和教师课堂开展，而不是只围绕三个实验。')
    features=[
        ('💬 全课程问答','跨七大主题解释概念，结合知识卡给出清晰、生动的回答。'),
        ('🎯 分层引导','用适合不同学习层次的表达、类比和理解检查问题帮助学习。'),
        ('🧠 误解诊断','发现常见错误认识，提示错误所在及修正路径；结果仍需复核。'),
        ('📝 互动练习','先出题、等待回答，再分析思路，避免直接剧透答案。'),
        ('🔬 HPS科学探究','特色实验模块：从假设、控制变量到证据解释，保留分层诊断。'),
        ('👩‍🏫 教师备课','辅助整理教学目标、课堂导入、探究活动和评价建议。'),
    ]
    feature_cols=st.columns(3,gap='small')
    for i,(t,d) in enumerate(features):
        with feature_cols[i%3]: card(t,d)

    headline('评委30秒体验：用一个熟悉的问题感受AI教学','以“鲸鱼为什么属于哺乳动物”为例；以下是功能介绍，不是自动生成的实测成绩。')
    a,b,c=st.columns(3,gap='medium')
    with a:card('① 学生自由提问','为什么鲸鱼生活在水里，却不是鱼？')
    with b:card('② AI检索并讲解','匹配生物分类课程卡，解释肺呼吸、胎生、哺乳等依据。')
    with c:card('③ 追问巩固理解','引导学生比较鲸与鱼的特征，并给出理解检查问题。')
    st.button('▶ 亲自测试这个问题',use_container_width=True,
              on_click=go_course,args=('为什么鲸虽然生活在水中，却属于哺乳动物？',))

    headline('课程范围和特色模块','七大课程主题已配置基础知识卡；实验探究是特色，不是软件的全部。')
    st.markdown(f'**课程内容：** {len(THEMES)}个主题 · {len(CURRICULUM_CARDS)}张基础知识卡 · {len(MODES)}种教学模式')
    theme_cols=st.columns(2)
    for index,theme in enumerate(THEMES):
        with theme_cols[index%2]:
            st.markdown('• '+theme)
    c1,c2=st.columns(2,gap='medium')
    with c1:
        st.button('📚 查看课程知识依据',use_container_width=True,
                  on_click=go,args=(NAV[5],))
    with c2:
        st.button('🔬 探索HPS实验专题',use_container_width=True,
                  on_click=go,args=(NAV[1],))
    st.markdown('<div class="disclaimer">真实范围说明：153张原创课程概要卡用于覆盖主要主题，不等于全教材覆盖或经教师逐条审核的权威资源。'
                '课程模式使用第三方模型API；教学回答与诊断仍需复核。项目特色包括HPS探究，但不宣称已实现学习成效提升。</div>',
                unsafe_allow_html=True)

elif page==NAV[1]:
    headline('实时实验探究','这是可交互的软件功能。体验示例为预置模拟输入，真正的模型回复需联网并消耗你配置的API额度。')
    m1,m2,m3=st.columns(3)
    m1.metric('当前实验',CASES[case]['topic'])
    m2.metric('当前阶段',STAGES[st.session_state.stage])
    m3.metric('暂定已完成',f'{sum(st.session_state.mastery)}/4')
    st.progress(sum(st.session_state.mastery)/4,text='四阶段学习进度 · 仅是研发阶段的暂定判断')
    left,right=st.columns([2.3,1],gap='large')
    with left:
        st.info('**本轮任务：** '+objective['question']+'\n\n**学习目标：** '+objective['outcome'])
        st.markdown('<div class="kicker">选择一个演示输入（或自行提问）</div>',unsafe_allow_html=True)
        examples=st.columns(3)
        for col,(label,prompt) in zip(examples,LIVE_EXAMPLES[case]):
            with col:
                st.button(label,key=f'ex_{case}_{label}',use_container_width=True,
                          on_click=go,args=(NAV[1],prompt,'内置模拟：'+label))
        pending=st.session_state.get('pending_prompt')
        if pending:
            with st.form('pending_prompt_form',clear_on_submit=False):
                st.caption('当前为预设模拟输入，可以修改；不会自动计费。')
                editable=st.text_area('准备发送的问题',value=pending[0],height=95)
                send_sample=st.form_submit_button('发送给真实AI（可能产生费用）',type='primary')
                cancel_sample=st.form_submit_button('取消预置输入')
            if cancel_sample:
                st.session_state.pending_prompt=None
                st.rerun()
            prepared=(editable,pending[1]) if send_sample else None
        else:
            prepared=None
        st.markdown('<div class="kicker">与AI实验老师对话</div>',unsafe_allow_html=True)
        if not st.session_state.history:
            st.info('🌿 '+scaffold(st.session_state.stage,case))
        for role,body in st.session_state.history:
            with st.chat_message(role,avatar='🌱' if role=='assistant' else '🧑‍🎓'):
                st.write(body)
        typed=st.chat_input('写下假设、提出疑问、描述实验方案……',key='chat_v40')
        query=(prepared[0] if prepared else typed or '').strip()
        source=(prepared[1] if prepared else '自行输入（身份未核验）')
        if query:
            if len(query)>4000:
                st.warning('问题请控制在4000字以内。')
            else:
                st.session_state.pending_prompt=None
                stage=st.session_state.stage
                rec={
                    'time':datetime.now().isoformat(timespec='seconds'),
                    'stage':STAGES[stage], 'student':query,'source':source,
                    'model':'','status':'','reply':'','diagnosis':'','evidence':'',
                    'model_claimed_pass':False,'rule_passed':False,'advanced':False,
                    'gate_reasons':[],'concept_updates':[],'format':'',
                }
                if not use_ai:
                    answer='实时AI已关闭。本轮没有进行判断，请打开左侧的“开启实时AI引导”。'
                    rec['status']='未调用 · 模型开关关闭'
                elif st.session_state.api_calls>=20:
                    answer='已达到当前浏览器会话的演示请求上限。请联系管理员或稍后重试。'
                    rec['status']='达到本会话请求上限'
                else:
                    st.session_state.api_calls+=1
                    with st.spinner('AI正在核对实验事实并形成教学反馈…'):
                        # Failed calls are preserved in audit records but omitted from model's history.
                        clean_history=clean_model_history(st.session_state.records,query)
                        response=call_ai(make_competition_messages(
                            clean_history,case,stage,st.session_state.mastery,st.session_state.concept_state))
                    rec['model']=response.get('model') or '未知'
                    st.session_state.last_model=rec['model']
                    if response.get('tokens'):
                        st.session_state.usage.append(response['tokens'])
                    if not response.get('ok'):
                        rec['status']='调用失败 · '+response.get('error','未知错误')
                        answer='本轮没有取得有效的模型回答，也不会推进阶段。请在右侧查看失败原因。'
                    else:
                        answer,parsed,tag=parse_model_output(response['text'])
                        rec['format']=tag
                        rec['status']='成功 · '+tag
                        decision=assess_transition(parsed,case,stage,query)
                        rec['rule_passed']=decision['rule_passed']
                        rec['model_claimed_pass']=decision['model_claimed']
                        rec['gate_reasons']=decision['reasons']
                        rec['advanced']=decision['accepted']
                        if parsed:
                            rec['diagnosis']=parsed['diagnosis']
                            rec['evidence']=parsed['evidence']
                            concept_updates=validate_concepts_strict(parsed,case,query)
                            st.session_state.concept_state=update_concept_state(
                                st.session_state.concept_state,concept_updates)
                            rec['concept_updates']=concept_updates
                        else:
                            rec['diagnosis']='本轮缺少完整结构化评价，不能自动判定阶段通过'
                        if decision['accepted']:
                            st.session_state.mastery[stage]=True
                            st.session_state.stage=min(stage+1,3)
                            answer+='\n\n✅ **本阶段暂定达到要求。**'
                            if stage<3:answer+=' 下一步：'+scaffold(stage+1,case)
                            else:answer+=' 四阶段均为暂定完成，请教师复核。'
                    st.session_state.last_status=rec['status']
                rec['reply']=answer
                st.session_state.records.append(rec)
                st.session_state.history.extend([('user',query),('assistant',answer)])
                st.rerun()
        if st.session_state.history:
            transcript='\n\n'.join(('学生：' if role=='user' else 'BioHPS：')+message for role,message in st.session_state.history)
            st.download_button('↓ 下载本次对话纪要',transcript,file_name='BioHPS_探究对话.txt',mime='text/plain')
    with right:
        st.markdown('<div class="kicker">学习路线 · 4个阶段</div>',unsafe_allow_html=True)
        for index,title in enumerate(STAGES):
            symbol='✅' if st.session_state.mastery[index] else '🟢' if st.session_state.stage==index else '◯'
            st.markdown(f'**{symbol} {index+1:02d} · {title}**')
            st.caption(STAGE_CRITERIA[index])
        st.divider()
        st.markdown('<div class="kicker">本次服务状态</div>',unsafe_allow_html=True)
        st.caption('实际响应模型：'+st.session_state.last_model)
        st.caption('最后一次调用：'+st.session_state.last_status)
        st.caption('当前会话调用次数：'+str(st.session_state.api_calls))
        st.info('阶段判断是模型建议和启发式规则的交集，不是学生的正式成绩。')
        st.markdown('**学科学习提醒**')
        st.caption(objective['materials'])

elif page==NAV[2]:
    headline('让每次学习过程都有证据可查','分别观察“科学概念是否理解”与“是否会设计实验”。保留学生原话、判断依据以及模型与程序的不同意见。')
    m1,m2,m3=st.columns(3)
    m1.metric('记录轮次',str(len(st.session_state.records)))
    m2.metric('有记录的概念',f'{len(st.session_state.concept_state)}/{len(CONCEPTS[case])}')
    m3.metric('探究阶段完成',f'{sum(st.session_state.mastery)}/4')
    st.caption('这些是本浏览器会话的记录数量，不代表教学成绩或能力提升。')
    left,right=st.columns([1,1],gap='large')
    with left:
        st.subheader('① 科学概念理解')
        for concept in CONCEPTS[case]:
            item=st.session_state.concept_state.get(concept,{})
            status=item.get('status','尚未体现')
            st.markdown('**'+concept+'**')
            st.caption('状态：'+status+'　|　学生原话：'+item.get('evidence','暂无'))
    with right:
        st.subheader('② 科学探究能力')
        for index,name in enumerate(STAGES):
            status='✅ 暂定达到要求' if st.session_state.mastery[index] else '◯ 尚未得到足够证据'
            st.markdown(f'**{name}**　　{status}')
            st.caption(STAGE_CRITERIA[index])
    st.divider()
    st.subheader('③ 每轮记录与判断理由')
    if not st.session_state.records:
        st.info('还没有对话记录。可以到“实时探究”输入一个模拟问题，或先在“作品速览”查看预置开发测试故事。')
    for index,rec in enumerate(st.session_state.records,1):
        with st.expander(f'第{index}轮 · {rec["stage"]} · {"暂定满足" if rec["advanced"] else "未满足"}'):
            st.caption('输入来源：'+rec['source'])
            st.write('**本轮学生原话：** '+rec['student'])
            st.write('**教学反馈：** '+rec['reply'])
            st.write('**AI诊断：** '+(rec['diagnosis'] or '暂无完整诊断'))
            st.write('**被引用证据：** '+(rec['evidence'] or '暂无'))
            st.write('**程序判定：** '+('暂定通过' if rec['advanced'] else '不通过'))
            st.caption('模型建议通过：'+str(rec['model_claimed_pass'])+' | 规则满足：'+str(rec['rule_passed']))
            if rec['gate_reasons']:
                st.write('**仍需补充：** '+'；'.join(rec['gate_reasons']))
            st.caption('模型：'+rec['model']+'　|　API状态：'+rec['status'])
    if st.session_state.records:
        report={
            'project':'BioHPS 科学探究智能体','version':'6.0',
            'case':case,'created':datetime.now().isoformat(timespec='seconds'),
            'records':st.session_state.records,'concept_state':st.session_state.concept_state,
            'stages_provisionally_passed':st.session_state.mastery,
            'study_note':'本记录可能包含开发者模拟输入，仅用于功能演示与研究过程；所有学习判断须教师复核',
        }
        st.download_button('↓ 导出教师观察档案（JSON）',json.dumps(report,ensure_ascii=False,indent=2),
                           file_name='BioHPS_V6_HPS学习诊断.json',mime='application/json')
    st.warning('未经教师复核，暂不能把本系统的概念判断或阶段完成率称为真实学习效果。')

elif page==NAV[3]:
    headline('科学史让“为什么这样实验”有据可依','HPS：从科学史了解问题如何提出，从科学哲学理解证据与解释，从社会应用看科学方法的价值。')
    st.subheader(CASES[case]['topic'])
    st.info(card_info['history'])
    st.markdown('**HPS 教学视角**')
    st.write(card_info['hps'])
    l,r=st.columns(2,gap='large')
    with l:
        st.markdown('**本案例的关键概念**')
        for item in card_info['focus']:st.markdown('✓ '+item)
    with r:
        st.markdown('**常见错误认识**')
        for item in card_info['common_errors']:st.markdown('• '+item)
    st.markdown('**参考来源与核查线索**')
    for source in card_info.get('references',[]):
        st.markdown('• ['+source['name']+']('+source['url']+')')
    st.warning('当前为人工整理的知识卡和外部核查链接，尚未接入自动RAG向量检索，也未完成专业教师逐条审定。')

elif page==NAV[4]:
    headline('项目说明 · 评委快速体验指南',
             '探知·BioHPS 是面向初中生物的AI智慧学习与教学辅助软件；HPS是特色教学方法，而不是唯一功能。')
    for label,body in (
        ('第1步 · 随问随学','从鲸鱼为什么属于哺乳动物、肺泡如何交换气体等生活化问题开始，展示课程问答、知识依据和理解检查。'),
        ('第2步 · 展示个性化任务','在AI课堂切换“知识理解／随堂练习／错误诊断／教师备课”，让评委看到同一平台服务不同需求。'),
        ('第3步 · 展示特色实验','在HPS实验模块输入一个典型错误认识，观察概念诊断和探究阶段判断。'),
        ('第4步 · 查看诊断依据','到“学习诊断档案”查看学生原话、暂定判断、门槛规则、模型状态；开发演示不可冒充课堂实验。'),
    ):
        st.markdown('**'+label+'**')
        st.write(body)
    a,b=st.columns(2)
    with a:
        st.button('💬 进入AI生物课堂',type='primary',use_container_width=True,
                  on_click=go_course,args=('为什么鲸虽然生活在水中，却属于哺乳动物？',))
    with b:
        st.button('🔬 进入HPS特色探究',use_container_width=True,
                  on_click=go,args=(NAV[1],LIVE_EXAMPLES[case][0][1],'内置模拟：评委测试'))
    st.divider()
    headline('五大产品能力 · 不只是三个实验')
    for title,explanation in PRODUCT_VALUES:
        st.markdown('**'+title+'：** '+explanation)
    st.markdown('**技术边界：** 底层使用第三方模型API；自主开发的部分主要是课程检索、教学任务编排、交互界面、探究规则和可追溯记录。')
    st.markdown('**验证边界：** 已实现初步功能测试，但尚未完成全教材覆盖、教师盲评及正式学习效果研究。')
    st.info('正式比赛需提供评委可访问的网址、PPT和6分钟内演示视频；匿名评审材料不得出现学校和人员身份信息。')


else:
    headline('💬 全课程AI课堂 · 直接提问，自动识别',
             '无需选择章节！直接输入生物学问题。系统优先匹配课程知识卡，未收录的问题交由AI谨慎辅导。')
    st.caption('默认自动匹配 · 无需选择教材章节 · 知识库未覆盖时可用通用AI答疑（将明确标注）。153张知识卡仍待教师逐条审核。')
    st.markdown(f'**主题覆盖：** {len(THEMES)}个主题 · {len(CURRICULUM_CARDS)}张原创知识卡（待审核） · {len(MODES)}种课堂任务模式')
    with st.expander('📚 查看七大课程主题目录', expanded=False):
        for theme_name in THEMES:
            items=get_theme_cards(CURRICULUM_CARDS,theme_name)
            st.markdown(f'**{theme_name}**（{len(items)}张） · '+ '、'.join(x['title'] for x in items))
        st.markdown('主题框架参考：[教育部《义务教育生物学课程标准（2022年版）》]('+OFFICIAL_CURRICULUM+')（仅用于课程组织，不代表153张知识卡逐条获得官方核验）')

    mode=st.radio('选择本次学习方式',MODES,horizontal=True,key='course_mode')
    with st.expander('⚙️ 高级设置（非必选）· 想手动限定章节时再展开',expanded=False):
        c1,c2,c3=st.columns([1.15,1.6,1.05],gap='medium')
        with c1:
            selected_theme=st.selectbox('学习主题',['自动识别']+THEMES,key='course_theme')
        with c2:
            visible_cards=CURRICULUM_CARDS if selected_theme=='自动识别' else get_theme_cards(CURRICULUM_CARDS,selected_theme)
            title_to_id={f"{x['title']} · {x['id']}":x['id'] for x in visible_cards}
            topic_choice=st.selectbox('具体知识点',['根据问题检索']+list(title_to_id),key='course_topic')
            selected_id=title_to_id.get(topic_choice)
        with c3:
            level=st.selectbox('学习层次',['初中通用','七年级入门','八年级拓展'],key='course_level')
        st.caption('不同教材的章节排序可能有差异；课程主题与年级册次并非固定一一对应关系。')
    if selected_theme=='自动识别' and selected_id is None:
        st.caption('✅ 当前：自动识别主题与知识点，无需手动选择章节。')
    else:
        st.caption('ℹ️ 当前：手动限定了主题或知识点，仅在你需要时使用。')
        st.button('↻ 恢复自动识别',
                  on_click=lambda: st.session_state.update({
                      'course_theme':'自动识别','course_topic':'根据问题检索'}))
    if 'course_dialogues' not in st.session_state:
        st.session_state.course_dialogues={}
    if 'course_calls' not in st.session_state:
        st.session_state.course_calls=0
    course_key = '|'.join([selected_theme, str(selected_id or ''), mode, level])
    if course_key not in st.session_state.course_dialogues:
        st.session_state.course_dialogues[course_key]=[]
    records=st.session_state.course_dialogues[course_key]
    examples={
        '知识理解':'为什么鲸虽然生活在水中，却属于哺乳动物？',
        '探究引导':'怎样设计实验验证光照对植物生长的影响？',
        '随堂练习':'请就人体呼吸与气体交换出一道理解题，先不要告诉我答案。',
        '错误诊断':'同学认为动脉中流动的一定是含氧较多的血，这样说准确吗？',
        '教师备课':'请围绕食物链与食物网设计一节初中生物探究课。',
    }
    # Change examples using a callback, before constructing the bound text area.
    if 'course_question' not in st.session_state:
        st.session_state['course_question']=''
    st.button('✨ 填入本模式示例问题（不自动调用模型）',
              on_click=lambda: st.session_state.update({'course_question':examples[mode]}))
    with st.form('course_request',clear_on_submit=False):
        user_question=st.text_area('向BioHPS提问',key='course_question',height=95,
                                  placeholder='例如：肺泡为什么适合气体交换？或请帮我设计一节生物课。')
        run=st.form_submit_button('发送给AI（可能产生API费用）',type='primary')
    if run:
        question=(user_question or '').strip()
        if not question:
            st.warning('请先输入课程问题。')
        elif len(question)>3000:
            st.warning('请将问题控制在3000字以内。')
        elif not use_ai:
            st.warning('左侧的实时AI开关目前关闭。')
        elif st.session_state.course_calls>=18:
            st.warning('已达到此浏览器会话的课程问答演示调用上限。')
        else:
            ctx,how=resolve_course_context(
                question,CURRICULUM_CARDS,selected_id=selected_id,
                theme=None if selected_theme=='自动识别' else selected_theme,
                previous=next((r for r in reversed(records) if r.get('ok')),None))
            if not ctx:
                st.info('本地知识卡未收录这一提问；将使用通用AI生物辅导，不会假称引用教材。')
            st.session_state.course_calls+=1
            history=[]
            for old in records[-6:]:
                if old['ok']:
                    history.extend([('user',old['question']),('assistant',old['answer'])])
            messages=make_course_messages(question,ctx,mode,level,history)
            with st.spinner('正在自动识别知识主题并生成教学反馈…'):
                response=call_ai(messages)
            answer = sanitize_course_answer(response.get('text',''),ctx) if response['ok'] else ''
            rec={
                'timestamp':datetime.now().isoformat(timespec='seconds'),
                'mode':mode,'level':level,'question':question,
                'knowledge_ids':[c['id'] for c in ctx],
                'knowledge_titles':[c['title'] for c in ctx],
                'knowledge_match_scores':{c['id']:c.get('_score') for c in ctx},
                'grounded':bool(ctx),
                'retrieval':how,
                'model':response.get('model') or '未知','ok':bool(response['ok']),
                'answer':answer,
                'error':response.get('error','') if not response['ok'] else '',
            }
            records.append(rec)
            st.rerun()

    left,right=st.columns([2.1,1],gap='large')
    with left:
        st.markdown('#### 💬 本次课堂对话')
        if not records:
            st.info('无需选择任何章节，直接输入生物学问题即可。系统会自动匹配知识卡或进行通用AI辅导。')
        for rec in records:
            with st.chat_message('user',avatar='🧑‍🎓'):
                st.write(rec['question'])
            with st.chat_message('assistant',avatar='🌿'):
                if rec['ok']:
                    st.write(rec['answer'])
                else:
                    st.error('本轮请求失败：'+rec['error'])
        if records:
            st.download_button('↓ 导出本次课堂学习记录',
                json.dumps({'version':'6.2','data_source':'原创课程概要卡（待教师核验）','records':records},ensure_ascii=False,indent=2),
                file_name='BioHPS_全课程学习记录.json',mime='application/json')
    with right:
        st.markdown('#### 📚 本地知识依据')
        latest = records[-1] if records else None
        if latest:
            st.caption('本轮知识来源：'+latest['retrieval'])
            st.caption('实际响应模型：'+latest['model'])
            matched=[c for c in CURRICULUM_CARDS if c['id'] in latest['knowledge_ids']]
        elif selected_id:
            matched=[c for c in CURRICULUM_CARDS if c['id']==selected_id]
        else:
            matched=[]
        if not matched:
            if latest:
                st.warning('本轮未命中本地知识卡：回答来自通用AI知识，尚未进行教材依据核验。')
            else:
                st.info('直接提问后，这里将显示匹配的知识卡或标记为通用AI答疑。')
        for entry in matched:
            with st.expander(entry['id']+' · '+entry['title'],expanded=True):
                st.caption('所属主题：'+entry['theme'])
                st.write(entry['summary'])
                st.caption('易混淆：'+entry.get('misconception',''))
                st.caption('审核状态：'+entry.get('review_status','待教师审核'))
                st.caption('资料说明：'+entry.get('source_title','原创知识概要'))
                st.caption('课程标准链接只用于主题组织，不是该知识点的逐条事实引用。')
                if entry.get('curriculum_reference','').startswith('https://www.moe.gov.cn/'):
                    st.markdown('[查看课程标准官方文件]('+entry['curriculum_reference']+')')
                if latest and entry['id'] in latest.get('knowledge_match_scores',{}):
                    st.caption('检索相对匹配分：'+str(latest['knowledge_match_scores'][entry['id']])+'（不是准确率或置信度）')
        st.divider()
        st.caption('课程问答调用次数：'+str(st.session_state.course_calls)+' / 18（当前浏览器会话）')
        st.caption('优先采用专业词语、课程别名与离线TF-IDF相似度混合检索；未命中时自动由模型进行通用生物知识辅导，不使用外部向量模型，也不代表权威教材逐条核验。')
    st.markdown('**拓展说明：** 开发者可在 `knowledge/custom_notes.jsonl` 添加新的课程卡片，扩展至出版社教材或校本课程，但需自行核实来源、版权与科学准确性。')

st.divider()
st.caption('BioHPS V6.2 · 全课程AI生物智慧课堂 | HPS为特色模块。知识卡仍需审核，演示不代表真实教学效果。')
