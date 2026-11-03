"""Flagship classroom UI: authentic interactions, explanatory content and saved evidence.

Single Streamlit app, no extra server. This module never auto-invents student activities.
"""

import streamlit as st
from deep_lessons import LESSONS
from hps_models import MEIOSIS_STAGES, simulate_cross, offspring_distribution, meiosis_step
from demo_store import add_hps_event,hps_events
from question_bank import BANK
from demo_store import add_attempt


def genotype_square(mother, father):
    """Two-by-two gamete combinations for explicitly selected genotypes."""
    from hps_models import gametes
    p=gametes(mother);q=gametes(father)
    def pair(a,b):return ''.join(sorted((a,b),key=lambda x:(x=='a',x)))
    st.table({'父本 '+q[0]:[pair(a,q[0]) for a in p],
              '父本 '+q[1]:[pair(a,q[1]) for a in p]})


def visual_stems():
    # Simple original schematic; generated locally rather than third-party diagrams.
    content='''<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="180" viewBox="0 0 680 180" role="img" aria-label="高茎和矮茎豌豆杂交示意">
 <rect x="4" y="5" width="672" height="168" rx="16" fill="#f3f9f5" stroke="#d6e7db"/>
 <g stroke="#267951" stroke-linecap="round"><path d="M118 142V48" stroke-width="5"/><path d="M118 97Q80 73 72 87" stroke-width="3" fill="none"/><path d="M118 77Q157 54 170 72" stroke-width="3" fill="none"/><path d="M421 142V96" stroke-width="5"/><path d="M421 123Q398 109 386 120" stroke-width="3" fill="none"/></g>
 <g fill="#57a873"><ellipse cx="69" cy="85" rx="18" ry="10" transform="rotate(25 69 85)"/><ellipse cx="169" cy="68" rx="19" ry="10" transform="rotate(-22 169 68)"/><ellipse cx="386" cy="120" rx="14" ry="8" transform="rotate(16 386 120)"/></g>
 <g fill="#278654"><circle cx="118" cy="47" r="7"/><circle cx="421" cy="94" r="7"/></g>
 <g font-family="Arial,'Microsoft Yahei',sans-serif" font-size="17" fill="#1d4c3b"><text x="95" y="163">高茎 AA</text><text x="294" y="100" font-size="30">×</text><text x="394" y="163">矮茎 aa</text><text x="537" y="94" font-size="18">F₁: Aa</text></g>
 <g stroke="#8faa96" stroke-width="3"><path d="M512 100h25"/></g>
 </svg>'''
    st.components.v1.html(content,height=194)


def chromosome_visual(stage):
    """Original SVG: pairs, homolog segregation and sister separation are distinct."""
    sid=stage['id']
    is_x=sid in ('S','PAIR','MI','END1')
    n_cells=4 if sid=='GAMETES' else 2 if sid in ('END1','MII') else 1
    cells=[]
    for ci in range(n_cells):
        cx=(ci+.5)*(700/n_cells);cy=104
        rx=72 if n_cells==4 else 86 if n_cells==2 else 113
        cells.append(f'<ellipse cx="{cx:.1f}" cy="{cy}" rx="{rx}" ry="78" fill="#f5faf8" stroke="#a8cbb5" stroke-width="2.4"/>')
        count=stage['count'][0]
        offsets=([-60,-26,26,60] if n_cells==1 and count==4 else
                 [-39,-13,13,39] if count==4 else [-18,18])
        if sid=='MI':offsets=[-72,-43,43,72]
        for i in range(count):
            xp=cx+offsets[i]
            # Two homologous pairs share size, but distinguish paternal/maternal copies.
            long=(i in (0,2)) if sid=='MI' else (i<2) if n_cells==1 and count==4 else i%2==0
            height=68 if long else 43
            top=103-height/2
            if sid=='MI' and i in (1,2):top+=13  # separated towards respective poles
            color=(['#d96557','#3477b7','#3477b7','#d96557'][i] if sid=='MI'
                  else ['#d96557','#3477b7','#d96557','#3477b7'][i] if n_cells==1
                  else ('#d96557' if (ci+i)%2==0 else '#3477b7'))
            if is_x:
                cells.append(f'<path d="M{xp-7:.1f},{top:.1f} L{xp+7:.1f},{top+height:.1f} M{xp+7:.1f},{top:.1f} L{xp-7:.1f},{top+height:.1f}" stroke="{color}" stroke-width="7" stroke-linecap="round" fill="none"/>')
            else:
                cells.append(f'<path d="M{xp:.1f},{top:.1f} L{xp:.1f},{top+height:.1f}" stroke="{color}" stroke-width="8" stroke-linecap="round"/>')
        if sid=='PAIR':
            for xx,w in ((cx-43,68),(cx+43,68)):
                cells.append(f'<rect x="{xx-w/2:.1f}" y="54" width="{w}" height="101" rx="8" fill="none" stroke="#e9aa3c" stroke-width="2" stroke-dasharray="5,4"/>')
        if sid=='MI':
            cells.append(f'<path d="M{cx-10:.1f},103 H{cx-28:.1f} M{cx-18:.1f},96 L{cx-28:.1f},103 L{cx-18:.1f},110 M{cx+10:.1f},103 H{cx+28:.1f} M{cx+18:.1f},96 L{cx+28:.1f},103 L{cx+18:.1f},110" stroke="#669a7c" fill="none" stroke-width="2.5"/>')
        tag=f'Gamete {ci+1}' if sid=='GAMETES' else f'Cell {ci+1}' if n_cells>=2 else 'Cell'
        cells.append(f'<text x="{cx:.1f}" y="204" fill="#315f4e" text-anchor="middle" font-family="Arial,sans-serif" font-size="13">{tag}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 215" width="100%" height="215" role="img" aria-label="Simplified chromosome stage">'
            '<rect width="700" height="215" fill="#ffffff"/>' + ''.join(cells)+'</svg>')


def change_lesson_step(key, delta, length):
    """Advance from a button callback before Streamlit creates the widget."""
    value=int(st.session_state.get(key,0))
    st.session_state[key]=max(0,min(length-1,value+delta))


def show_lesson_text(lesson):
    """Read one substantial lesson section at a time, not a two-sentence note."""
    st.markdown('### 本节课要解决什么问题？')
    st.info(lesson['problem'])
    with st.expander('学习目标与必要的前置知识'):
        for goal in lesson['goals']:
            st.markdown('• '+goal)
        st.write('**学习前最好知道：** '+lesson['prereq'])
    key='reading_progress_'+lesson['id']
    headings=[v[0] for v in lesson['sections']]
    step=st.selectbox('课程内容',range(len(headings)),format_func=lambda x:headings[x],key=key)
    st.progress((step+1)/len(headings),text=f'正在学习第 {step+1} / {len(headings)} 个知识环节')
    title,body=lesson['sections'][step]
    st.markdown('## '+title)
    st.markdown(body)
    if lesson['id']=='B2-S01' and step in (0,1,2):
        visual_stems()
    if step==len(headings)-1:
        st.markdown('### 结合科学史，再想一想')
        st.write(lesson['history'][0])
        st.info(lesson['history'][1])
        with st.expander('检验理解：本课容易混淆什么？',expanded=True):
            for x in lesson['misconceptions']:
                st.markdown('• '+x)
        st.write('**继续学习：** '+lesson['next'])
    prev,next_=st.columns(2)
    with prev:
        st.button('上一知识环节',disabled=step==0,key='reading_back_'+lesson['id'],
                  on_click=change_lesson_step,args=(key,-1,len(headings)),use_container_width=True)
    with next_:
        st.button('继续下一知识环节',disabled=step==len(headings)-1,key='reading_next_'+lesson['id'],
                  on_click=change_lesson_step,args=(key,1,len(headings)),use_container_width=True,type='primary')


def mendel_lab(student):
    course='B2-S01';prefix=f'mendel_{student}'
    st.markdown('#### 虚拟实验 · 豌豆杂交与测交')
    st.write('选择亲本、完成授粉操作，**先预测，再取样观察**。你可以重做实验，比较不同样本量的结果。')
    with st.expander('亲本选择和人工授粉',expanded=True):
        with st.form(prefix+'_pollination'):
            a,b=st.columns(2)
            with a:female=st.selectbox('母本基因型',['AA','aa','Aa'],key=prefix+'_female')
            with b:male=st.selectbox('父本基因型',['aa','AA','Aa'],key=prefix+'_male')
            procedure=st.radio('人工杂交的合理操作顺序',[
                '去雄（花药成熟前）→套袋→授粉→再套袋、标记',
                '授粉→去雄→套袋→标记',
                '套袋→观察→去雄→不再授粉'],key=prefix+'_procedure')
            submitted=st.form_submit_button('完成亲本选择和操作',type='primary')
        if submitted:
            good=(female,male) in (('AA','aa'),('aa','AA')) and procedure.startswith('去雄')
            add_hps_event(student,course,'pollination',{'female':female,'male':male,'procedure':procedure,'correct':good})
            st.session_state[prefix+'_pollination_ok']=good
            st.session_state[prefix+'_f1_done']=False
            if good:st.success('操作正确：纯合亲本的杂交可以开始。')
            else:st.warning('检查：两个亲本应为相反性状的纯合体，并在花药成熟前去雄，套袋隔离、再人工授粉。')
    if not st.session_state.get(prefix+'_pollination_ok'):
        st.info('先完成上面的亲本选择与人工授粉。');return
    st.markdown('#### 观察F₁并提出假设')
    st.write('AA×aa → F₁全为Aa，表现高茎。为什么矮茎没有表现？')
    with st.form(prefix+'_predict'):
        hypothesis=st.radio('关于F₁的合理假说',[
            'a仍存在于Aa中，但在完全显性条件下未表现',
            'a在F₁已经消失','F₁没有遗传因子'],key=prefix+'_hypothesis')
        predicted=st.radio('Aa自交后，F₂高茎:矮茎的理论预测是？',['3:1','1:1','全部高茎'],key=prefix+'_expected')
        do=st.form_submit_button('保存我的预测')
    if do:
        sound=(hypothesis.startswith('a仍') and predicted=='3:1')
        add_hps_event(student,course,'prediction',{'hypothesis':hypothesis,'predicted':predicted,'sound':sound})
        st.session_state[prefix+'_f1_done']=True
        st.session_state[prefix+'_predicted']=predicted
        st.success('预测已经保存，可以运行F₂实验。') if sound else st.warning('预测已保存。先观察结果，再对照配子组合检查自己的解释。')
    if not st.session_state.get(prefix+'_f1_done'):return
    st.markdown('#### F₁自交：从配子到后代')
    genotype_square('Aa','Aa')
    with st.form(prefix+'_cross'):
        n=st.select_slider('观察多少株F₂？',[16,64,256,1024],value=64,key=prefix+'_n')
        seed=st.number_input('重复试验编号',min_value=1,max_value=1000000,value=43,step=1,key=prefix+'_seed')
        run=st.form_submit_button('运行F₁自交并记录观察',type='primary')
    if run:
        result=simulate_cross('Aa','Aa',int(n),int(seed))
        add_hps_event(student,course,'f2_trial',{'n':result['n'],'seed':result['seed'],
          'high':result['phenotypes']['高茎'],'short':result['phenotypes']['矮茎'],
          'prediction':st.session_state.get(prefix+'_predicted','未提交')})
        st.session_state[prefix+'_f2']=result
    f2=st.session_state.get(prefix+'_f2')
    if f2:
        a,b,c=st.columns(3)
        a.metric('高茎观察数',f2['phenotypes']['高茎']);b.metric('矮茎观察数',f2['phenotypes']['矮茎']);c.metric('高茎观察比例',f'{f2["phenotypes"]["高茎"]/f2["n"]:.1%}')
        import pandas as pd
        chart=pd.DataFrame({'观察数量':[f2['phenotypes']['高茎'],f2['phenotypes']['矮茎']],
                      '理论期望':[f2['n']*.75,f2['n']*.25]},index=['高茎','矮茎'])
        st.bar_chart(chart,height=220)
        st.write(f'理论预测高:矮=3:1，观察到 {f2["phenotypes"]["高茎"]}:{f2["phenotypes"]["矮茎"]}。有限样本不必精确符合理论比。')
    st.divider()
    st.markdown('#### 设计测交，检验配子假说')
    with st.form(prefix+'_testcross'):
        target=st.selectbox('F₁ Aa应该与谁测交？',['aa','Aa','AA'],key=prefix+'_target')
        prediction=st.radio('你预期的测交表现型比例是？',['1:1','3:1','全部高茎'],key=prefix+'_testprediction')
        n=st.select_slider('测交后代数',[16,64,256,1024],value=64,key=prefix+'_test_n')
        seed=st.number_input('测交试验编号',min_value=1,max_value=1000000,value=55,step=1,key=prefix+'_testseed')
        run=st.form_submit_button('运行测交并保存证据',type='primary')
    if run:
        good=(target=='aa' and prediction=='1:1')
        if target!='aa':
            st.warning('所选亲本不是隐性纯合体；这次不能当作检验Aa配子比例的标准测交。请重新选择。')
        else:
            result=simulate_cross('Aa',target,int(n),int(seed))
            add_hps_event(student,course,'testcross',{'target':target,'prediction':prediction,
             'n':result['n'],'seed':result['seed'],'high':result['phenotypes']['高茎'],
             'short':result['phenotypes']['矮茎'],'prediction_correct':good})
            st.session_state[prefix+'_testresult']=result
            st.info('预测正确。现在比较观察与理论。' if good else '已保存预测。回看Aa×aa的配子组合，找出预测与理论差异。')
    trial=st.session_state.get(prefix+'_testresult')
    if trial:
        st.write(f'测交本轮观察：高茎{trial["phenotypes"]["高茎"]}、矮茎{trial["phenotypes"]["矮茎"]}；理论比1:1。')
        with st.form(prefix+'_conclude'):
            reasoning=st.radio('观察到42:38一类略偏离1:1的情况，最合理的判断是？',[
                '有限样本可能出现随机波动，应结合样本量和重复试验评价',
                '只要不精确1:1，就说明分离定律完全错误',
                '用一株后代即可确定所有遗传规律'],key=prefix+'_reason')
            note=st.text_area('我的证据小结（观察到什么、怎样解释、还有什么局限）',max_chars=500,key=prefix+'_note')
            confirm=st.form_submit_button('提交科学探究报告',type='primary')
        if confirm:
            sound=reasoning.startswith('有限样本')
            add_hps_event(student,course,'conclusion',{'sound':sound,'reasoning':reasoning,'note':note.strip()[:500]})
            if sound:st.success('已记录你的证据推理，继续尝试调整样本量或完成章节练习。')
            else:st.warning('已记录你的判断。建议先比较16株与256株的观察波动，再重新解释。')
    with st.expander('虚拟实验的依据与适用范围'):
        st.write('这是单基因完全显性教学模型，结果来自随机模拟，不是实地植物测量。已保存亲本、样本数和重复试验编号，便于复现。')


def meiosis_lab(student):
    prefix=f'meiosis_{student}';course='B2-S03'
    st.markdown('#### 染色体操作台')
    st.write('从一个**2n=4的简化细胞**开始，逐步判断染色体发生了什么变化。选错时会告诉你原因；正确完成后进入下一阶段。')
    progress=st.session_state.get(prefix+'_progress',0)
    if progress>=len(MEIOSIS_STAGES):
        st.success('你已完成从DNA复制到受精的全过程！')
        if st.button('重新操作一次',key=prefix+'_again'):
            st.session_state[prefix+'_progress']=0;st.rerun()
        return
    stage=MEIOSIS_STAGES[progress]
    st.progress(min(1,(progress+1)/len(MEIOSIS_STAGES)),text=f'{progress+1}/{len(MEIOSIS_STAGES)} · {stage["title"]}')
    st.components.v1.html(chromosome_visual(stage),height=225)
    a,b,c=st.columns(3)
    a.metric('每细胞染色体',stage['count'][0]);b.metric('每细胞DNA分子',stage['count'][1]);c.metric('连接状态的姐妹染色单体',stage['count'][2])
    with st.form(prefix+'_phase_'+stage['id']):
        st.write('**操作任务：** '+stage['action'])
        choices=stage['wrong'][:1]+[stage['right']]+stage['wrong'][1:]
        choice=st.radio('你认为正确的操作或判断是',choices,index=None,key=prefix+'_choice_'+stage['id'])
        do=st.form_submit_button('提交我的判断',type='primary')
    if do:
        if not choice:st.warning('请先选择，再提交。')
        else:
            result=meiosis_step(stage['id'],choice)
            add_hps_event(student,course,'meiosis_step',{'stage':stage['id'],'correct':result['correct'],
              'choice':choice,'chromosomes':result['chromosomes'],'dna':result['dna']})
            st.session_state[prefix+'_feedback']=result
            if result['correct']:
                st.session_state[prefix+'_passed_'+stage['id']]=True
            st.rerun()
    feedback=st.session_state.get(prefix+'_feedback')
    if feedback and feedback['stage']==stage['id']:
        st.success('判断正确。') if feedback['correct'] else st.warning('再看看同源染色体与姐妹染色单体的区别。')
        st.write(feedback['explanation'])
    if st.session_state.get(prefix+'_passed_'+stage['id']):
        if st.button('进入下一阶段',type='primary',key=prefix+'_forward_'+stage['id']):
            st.session_state[prefix+'_progress']=progress+1
            st.session_state[prefix+'_feedback']=None
            st.rerun()
    with st.expander('模型说明'):
        st.write('示意图仅表示简化的染色体数量和复制状态，不能替代真实显微图像或全部纺锤体运动。计数以屏幕所示单个细胞为单位，染色单体按中学常用计数约定。')


def flagship_quiz(student,slug):
    from flagship_questions import QUESTIONS
    slugprefix='M' if slug=='mendel' else 'J'
    pool=[q for q in QUESTIONS.values() if q['id'].startswith('V10-'+slugprefix)]
    st.markdown('### 本课巩固检测')
    st.write('每道题都可以反复练习。选择后请阅读为什么正确或错误，并查看自己的学习记录。')
    selected=st.selectbox('选择练习题',pool,format_func=lambda x:f'{x["id"].split("-")[-1]} · {x["question"][:28]}…',key='flag_quiz_'+student+'_'+slug)
    q=selected
    st.markdown('**'+q['question']+'**')
    with st.form('flag_form_'+student+'_'+q['id']):
        opts=['请选择']+q['options']
        answer=st.radio('我的答案',opts,key='flag_option_'+student+'_'+q['id'])
        submit=st.form_submit_button('提交并保存答题',type='primary')
    if submit:
        if answer=='请选择':st.warning('请选择一个答案。')
        else:
            result=add_attempt(student,q,opts.index(answer)-1)
            st.session_state['flag_feedback_'+student+'_'+q['id']]=result
            st.rerun()
    if 'flag_feedback_'+student+'_'+q['id'] in st.session_state:
        result=st.session_state['flag_feedback_'+student+'_'+q['id']]
        st.success('答对了！') if result['correct'] else st.warning('这道题还需要复习。')
        st.markdown('**参考解析：** '+q['explanation'])


def flagship_report(student,slug):
    lesson=LESSONS[slug]
    from demo_store import student_attempts
    rows=hps_events(student_id=student,course_id=lesson['id'])
    quiz=[q for q in student_attempts(student) if q['question_id'].startswith('V10-'+('M' if slug=='mendel' else 'J'))]
    a,b,c=st.columns(3)
    a.metric('探究记录',len(rows));b.metric('练习次数',len(quiz));c.metric('需要复习的题次',sum(not x['correct'] for x in quiz))
    if not rows and not quiz:st.info('本课还没有记录，先完成实验操作或练习。')
    else:
        for r in rows[:8]:
            msg={'pollination':'完成亲本选择和授粉','prediction':'提交F₂预测','f2_trial':'观察F₂后代','testcross':'完成测交','conclusion':'提交证据总结','meiosis_step':'完成减数分裂阶段判断'}.get(r['event_type'],r['event_type'])
            st.write(f'• {msg} · {r["created_at"][:16].replace("T"," ")}')
        if quiz and any(not x['correct'] for x in quiz):
            st.info('复习建议：先回看本课相应知识讲解，再做另一道检测题验证理解。')
    st.write('这些记录也将出现在教师端的本课学习反馈中。')


def render_flagship(student):
    selections={'mendel':'孟德尔：豌豆杂交与分离定律','meiosis':'减数分裂：染色体推演'}
    slug=st.selectbox('选择课程样板',list(selections),format_func=lambda x:selections[x],key='flag_course_'+student)
    lesson=LESSONS[slug]
    st.header(lesson['title'])
    st.caption(lesson['chapter']+' · '+lesson['subtitle'])
    page=st.radio('学习步骤',['系统讲解','动手探究','章节检测','我的学习报告'],horizontal=True,key='flag_page_'+student)
    st.divider()
    if page=='系统讲解':show_lesson_text(lesson)
    elif page=='动手探究':mendel_lab(student) if slug=='mendel' else meiosis_lab(student)
    elif page=='章节检测':flagship_quiz(student,slug)
    else:flagship_report(student,slug)
