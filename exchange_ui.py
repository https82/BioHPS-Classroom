"""Independent student and mentor work areas, joined only by explicit demo evidence/tasks."""
import streamlit as st
from question_bank import BANK
import demo_store as store
from lesson_planner import plan_markdown,pptx_bytes
from teaching_exchange import (COURSES,build_evidence,json_text,evidence_markdown,
    validate_plan,plan_template,as_lesson,task_card,validate_task)
from collaboration_store import (student_tasks,submit_task_answer,publish_task,task_progress,reserve_request)
from service import config_status,provider_name


def _selection(prefix):
    return st.selectbox('选择专题',list(COURSES),format_func=lambda x:COURSES[x]['topic'],key=prefix+'_course')


def render_student_exchange(student):
    tasks=student_tasks(student)
    st.markdown('### 导师给我的学习任务')
    if not tasks:st.caption('暂时没有导师发布的专题任务，你可以独立问AI、练习或科学探究。')
    for task in tasks:
        card=task['card']
        done=len(task['answers']);total=len(card['question_ids'])
        with st.expander(f'{card["topic"]} · 已完成 {done}/{total}',expanded=done<total):
            st.write(card['instructions'])
            for qid in card['question_ids']:
                q=BANK[qid];key=f'published_task_{student}_{task["id"]}_{qid}'
                result=task['answers'].get(qid)
                st.write(q['question'])
                if result is None:
                    with st.form(key):
                        answer=st.radio('选择答案',range(len(q['options'])),format_func=lambda i,q=q:q['options'][i],
                                        index=None,key=key+'_choice')
                        submitted=st.form_submit_button('提交本题')
                    if submitted:
                        if answer is None:st.info('请先选择答案')
                        else:
                            submit_task_answer(student,task['id'],qid,answer)
                            st.rerun()
                else:
                    st.caption('我的选择：'+q['options'][result['answer_idx']])
                    (st.success if result['correct'] else st.info)('回答正确' if result['correct'] else '请对照解析订正')
                    st.write(q['explanation'])
            st.caption('任务作答自动保存在自己的学习记录中，导师刷新后可查看。')
    with st.expander('导师任务与我的学情交接',expanded=False):
        st.caption('这里仅显示当前演示身份的学习记录。问AI、章节练习与科学探究仍可独立使用。')
        course=_selection('student_exchange_'+student)
        packet=build_evidence(course,student_id=student)
        st.write(f'本专题：{packet["summary"]["attempts"]}次作答，{packet["summary"]["questions"]}次提问。')
        st.download_button('导出我的专题学情',json_text(packet),file_name='BioHPS_我的学情.json',
            mime='application/json',key='own_evidence_'+student)
        upload=st.file_uploader('导入导师学习任务卡',type=['json'],key='student_task_'+student)
        if upload is None:return
        try:
            card=validate_task(upload.getvalue())
        except (ValueError,UnicodeError) as exc:
            st.warning(str(exc));return
        st.markdown('**'+card['topic']+' · 导师任务**')
        st.write(card['instructions'])
        for qid in card['question_ids']:
            q=BANK[qid];key=f'mentor_task_{student}_{card["task_id"]}_{qid}'
            with st.form(key):
                st.write(q['question'])
                answer=st.radio('选择答案',range(len(q['options'])),format_func=lambda i,q=q:q['options'][i],
                                index=None,key=key+'_choice')
                submitted=st.form_submit_button('提交本题')
            if submitted:
                if answer is None:st.info('请先选择答案')
                else:st.session_state[key+'_result']=store.add_attempt(student,q,answer)
            if key+'_result' in st.session_state:
                result=st.session_state[key+'_result']
                (st.success if result['correct'] else st.info)('回答正确' if result['correct'] else '本题需要订正')
                st.write(q['explanation'])
                st.caption('作答已进入当前演示身份的学习记录，导师可重新导出查看。')


def render_mentor_exchange():
    with st.expander('师生协同：学情分析、导师备课与课件',expanded=True):
        st.caption('在当前工作区直接使用'+provider_name()+'分析专题记录。生成后由导师审核、编辑和发布任务。')
        course=_selection('mentor_exchange')
        limits=st.checkbox('限定记录日期（UTC）',key='mentor_exchange_dates')
        since=until=''
        if limits:
            cols=st.columns(2)
            since=cols[0].date_input('开始日期',key='mentor_exchange_since').isoformat()
            until=cols[1].date_input('结束日期',key='mentor_exchange_until').isoformat()
        try:packet=build_evidence(course,since=since,until=until)
        except ValueError as exc:st.warning(str(exc));return
        counts=packet['summary']
        st.write(f'演示身份 {counts["participants"]} 个 · 作答 {counts["attempts"]} 次 · 错误 {counts["incorrect_attempts"]} 次 · 探究 {counts["hps_events"]} 次')
        st.caption('仅统计当前专题和所选日期，提问、作答和探究记录自动进入分析范围。请只使用演示资料。')
        with st.expander('查看本次分析依据'):
            st.json(packet)
        with st.expander('导出学情与备课格式'):
            cols=st.columns(3)
            cols[0].download_button('下载专题学情JSON',json_text(packet),file_name='BioHPS_专题学情.json',mime='application/json')
            cols[1].download_button('下载学情说明',evidence_markdown(packet),file_name='BioHPS_专题学情.md')
            cols[2].download_button('下载备课JSON格式',json_text(plan_template(packet)),
                file_name='BioHPS_导师备课格式.json',mime='application/json')
        mode=st.radio('备课方式',['网页内生成','选择JSON文件','粘贴JSON内容'],horizontal=True,key='mentor_exchange_mode')
        raw=None
        if mode=='网页内生成':
            if not config_status()['ready']:st.info('管理员配置在线模型后，即可在这里直接生成。')
            if st.button('依据当前学情生成备课',key='mentor_generate_plan',type='primary',disabled=not config_status()['ready']):
                if not reserve_request('teacher','mentor_plan'):st.warning('本小时备课额度已用完，请稍后再试。')
                else:
                    from mentor_agent import generate_plan
                    with st.spinner('正在核对证据并生成教学建议…'):
                        result=generate_plan(packet)
                    if result.get('ok'):
                        st.session_state['mentor_generated_'+course]={'packet_id':packet['packet_id'],
                            'raw':json_text(result['plan']),'model':result.get('model',''),
                            'provider':result.get('provider',''),'response_id':result.get('response_id','')}
                    else:st.warning('本次备课未完成：'+result.get('error','请稍后重试'))
            generated=st.session_state.get('mentor_generated_'+course)
            if generated:
                if generated['packet_id']==packet['packet_id']:
                    raw=generated['raw']
                    st.caption('实际来源：'+generated['provider']+' · '+generated['model'])
                    with st.expander('本次AI调用记录'):st.write(generated['response_id'])
                else:st.info('专题记录已变化，请依据最新学情重新生成备课。')
        elif mode=='选择JSON文件':
            f=st.file_uploader('选择导师端返回的备课JSON',type=['json'],key='mentor_plan_upload')
            if f is not None:raw=f.getvalue()
        elif mode=='粘贴JSON内容':
            text=st.text_area('粘贴完整备课JSON',key='mentor_plan_paste',height=140)
            if text.strip():raw=text
        if raw is None:return
        try:plan=validate_plan(raw,packet)
        except (ValueError,UnicodeError) as exc:st.warning('导入未通过：'+str(exc));return
        st.success('课程、证据编号、数据版本与题号已核对。请审核并编辑教学内容。')
        # Key includes both evidence and imported content: no accidental stale mentor/student edits.
        import hashlib
        revision=hashlib.sha256(json_text(plan).encode()).hexdigest()[:12]
        sections=[]
        for i,sec in enumerate(plan['sections']):
            text=st.text_area(sec['title'],'\n'.join(sec['bullets']),height=110,
                key=f'mentor_edit_{packet["packet_id"]}_{revision}_{i}')
            bullets=[line.strip().lstrip('-• ') for line in text.splitlines() if line.strip()]
            if not bullets or len(bullets)>6 or any(len(b)>80 for b in bullets):
                st.warning('每页请填写1至6条要点，每条不超过80字。');return
            sections.append(dict(title=sec['title'],bullets=bullets))
        edited={**plan,'sections':sections}
        lesson=as_lesson(edited,packet)
        cols=st.columns(2)
        cols[0].download_button('下载审核后的备课大纲',plan_markdown(lesson),file_name='BioHPS_导师备课大纲.md')
        try:
            cols[1].download_button('下载同内容可编辑课件',pptx_bytes(lesson),
                file_name='BioHPS_导师备课课件.pptx',mime='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        except ImportError:cols[1].info('安装项目依赖后可导出课件')
        instructions=st.text_area('给学生的学习任务',
            '回顾本专题，说明预测与证据的关系，再完成导师推荐的练习。',key='task_note_'+revision)
        reviewed=st.checkbox('我已审核教学内容与推荐题目',key='task_review_'+revision)
        if reviewed:
            try:card=task_card(edited,instructions)
            except ValueError as exc:st.warning(str(exc));return
            st.download_button('导出给学生的学习任务卡',json_text(card),
                file_name='BioHPS_导师学习任务卡.json',mime='application/json')
            recipients=st.multiselect('发布给哪些学生',list(store.DEMO_STUDENTS),
                default=list(store.DEMO_STUDENTS),format_func=lambda s:store.DEMO_STUDENTS[s]['label'],key='task_recipients_'+revision)
            if st.button('发布到学生工作区',type='primary',key='publish_task_'+revision):
                try:
                    added=publish_task(card,recipients)
                    st.success(f'已发布到{added}个学生工作区。学生在学习档案中可直接看到并作答。' if added else '相同任务已发布，无需重复发布。')
                except ValueError as exc:st.warning(str(exc))
            st.caption('学生任务不带班级原始记录或参考答案。新作答会自动进入导师学情。')
        progress=task_progress()
        if progress:
            st.markdown('**已发布任务进度**')
            st.dataframe([{'学生':store.DEMO_STUDENTS[t['student_id']]['label'],'专题':t['topic'],
                '已作答':t['answered'],'任务题数':t['total']} for t in progress],hide_index=True)
