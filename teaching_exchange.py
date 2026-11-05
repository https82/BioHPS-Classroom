"""Explicit teaching exchange for fictional demo roles; no remote upload or auth claims."""
import hashlib
import json
from collections import Counter
from datetime import datetime

import demo_store as store
from question_bank import BANK

COURSES = {
    'B2-S01': {'topic': '孟德尔分离定律', 'card_id': 'HS-028'},
    'B2-S03': {'topic': '减数分裂', 'card_id': 'HS-025'},
}
ALIASES = {'s1': 'demo-A', 's2': 'demo-B', 's3': 'demo-C', 's4': 'demo-D'}
CARD_ALIASES = {'BIO-HLP-MENDEL':'HS-028','BIO-HLP-MEIOSIS':'HS-025'}
SECTION_TITLES = ['学情与本课问题', '学习目标', '课前诊断与导入', '核心知识讲解',
                  'HPS科学探究活动', '练习与针对性反馈', '课堂小结与复测']


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def learning_card_id(card_id):
    return CARD_ALIASES.get(card_id,card_id)


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()[:20]


def _course(course_id):
    if not isinstance(course_id,str) or course_id not in COURSES:
        raise ValueError('请选择孟德尔或减数分裂专题')
    return COURSES[course_id]


def _date(value):
    if not value:
        return ''
    try:
        return datetime.fromisoformat(str(value)[:10]).date().isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError('日期无效') from exc


def build_evidence(course_id, student_id=None, since='', until=''):
    """Read an exact bounded course/date scope; student export cannot select classmates."""
    course = _course(course_id)
    if student_id is not None and student_id not in ALIASES:
        raise ValueError('无效演示身份')
    since, until = _date(since), _date(until)
    if since and until and since > until:
        raise ValueError('开始日期不能晚于结束日期')
    def included(row):
        day = str(row['created_at'])[:10]  # SQLite timestamps are UTC; labelled below.
        return (not since or day >= since) and (not until or day <= until)
    with store.database() as con:
        args = [course['card_id']]
        own = ' AND student_id=?' if student_id else ''
        if student_id:
            args.append(student_id)
        attempts = [dict(r) for r in con.execute(
            'SELECT * FROM attempts WHERE card_id=?'+own+' ORDER BY id', args)]
        question_cards=[course['card_id']]+[k for k,v in CARD_ALIASES.items() if v==course['card_id']]
        placeholders=','.join('?' for _ in question_cards)
        questions = [dict(r) for r in con.execute(
            f'SELECT * FROM student_questions WHERE card_id IN ({placeholders})'+own+' ORDER BY id',
            question_cards+([student_id] if student_id else []))]
        events = [dict(r) for r in con.execute(
            'SELECT * FROM hps_events WHERE course_id=?'+own+' ORDER BY id',
            [course_id]+([student_id] if student_id else []))]
    evidence = []
    for row in attempts:
        if not included(row):
            continue
        q = BANK.get(row['question_id'])
        if q is None or not 0 <= row['answer_idx'] < len(q['options']):
            raise ValueError('存在无法核对的题目记录，请先核对题库')
        evidence.append(dict(evidence_id=f'A-{row["id"]}', kind='attempt',
            learner_alias=ALIASES[row['student_id']], created_at=row['created_at'],
            question_id=q['id'], question=q['question'], options=q['options'],
            selected_answer=q['options'][row['answer_idx']], reference_answer=q['options'][q['answer']],
            correct=bool(row['correct']), error_hint=q['error_tag']))
    for row in questions:
        if included(row):
            evidence.append(dict(evidence_id=f'Q-{row["id"]}', kind='question',
                learner_alias=ALIASES[row['student_id']], created_at=row['created_at'],
                text=row['text'], answer_source=row['answer_source']))
    for row in events:
        if included(row):
            evidence.append(dict(evidence_id=f'H-{row["id"]}', kind='hps_event',
                learner_alias=ALIASES[row['student_id']], created_at=row['created_at'],
                event_type=row['event_type'], data=json.loads(row['payload'])))
    packet = dict(schema_version='biohps-learning-evidence-1',
        data_origin='website_demo_operations',
        data_label='网站预设演示身份的实际操作记录，非真实课堂效果数据',
        course_id=course_id, topic=course['topic'],
        scope=dict(role='student' if student_id else 'mentor',
                   learner_alias=ALIASES.get(student_id), since=since, until=until,
                   timezone='UTC', truncated=False), evidence=evidence,
        summary=dict(participants=len({e['learner_alias'] for e in evidence}),
                     attempts=sum(e['kind']=='attempt' for e in evidence),
                     incorrect_attempts=sum(e['kind']=='attempt' and not e['correct'] for e in evidence),
                     questions=sum(e['kind']=='question' for e in evidence),
                     hps_events=sum(e['kind']=='hps_event' for e in evidence)))
    packet['packet_id'] = _digest(packet)
    return packet


def evidence_markdown(packet):
    lines = [f'# {packet["topic"]} · 学情交接', '', packet['data_label'],
             f'数据版本：{packet["packet_id"]}',
             f'范围：{packet["scope"]}', f'统计：{packet["summary"]}', '']
    for e in packet['evidence']:
        lines += [f'## {e["evidence_id"]} · {e["learner_alias"]}', json_text(e), '']
    return '\n'.join(lines)


def parse_json(raw):
    if isinstance(raw, bytes):
        if len(raw)>250_000:
            raise ValueError('文件超过250KB')
        raw=raw.decode('utf-8-sig')
    if not isinstance(raw,str) or len(raw)>250_000:
        raise ValueError('内容应为不超过250KB的JSON')
    raw=raw.strip()
    if raw.startswith('```') and raw.endswith('```'):
        raw=raw[raw.index('\n')+1:-3].strip()
    try:
        data=json.loads(raw)
    except (ValueError,TypeError) as exc:
        raise ValueError('内容不是有效JSON，请使用导师端的结构化备课输出') from exc
    if not isinstance(data,dict):
        raise ValueError('JSON最外层应为对象')
    return data


def _strings(values, minimum, maximum, chars):
    return (isinstance(values,list) and minimum<=len(values)<=maximum
            and all(isinstance(s,str) and 0<len(s.strip())<=chars for s in values))


def validate_plan(raw, packet):
    data=parse_json(raw)
    if data.get('schema_version')!='biohps-mentor-plan-1':
        raise ValueError('不是BioHPS导师备课格式')
    if data.get('course_id')!=packet['course_id'] or data.get('evidence_packet_id')!=packet['packet_id']:
        raise ValueError('备课与当前导出的课程或数据版本不一致，请选择对应范围重新导出')
    if data.get('topic')!=packet['topic']:
        raise ValueError('备课主题不一致')
    ids=data.get('evidence_ids')
    if not isinstance(ids,list) or any(not isinstance(i,str) for i in ids):
        raise ValueError('缺少证据编号列表')
    known={e['evidence_id'] for e in packet['evidence']}
    if not set(ids)<=known or (known and not ids):
        raise ValueError('引用了不存在的证据或未引用已有证据')
    sections=data.get('sections')
    if not isinstance(sections,list) or len(sections)!=7:
        raise ValueError('备课必须包含七个章节')
    for i,s in enumerate(sections):
        if not isinstance(s,dict) or not isinstance(s.get('title'),str) or not 1<=len(s['title'])<=60:
            raise ValueError('章节标题无效')
        if s['title']!=SECTION_TITLES[i]:
            raise ValueError('请保留备课格式的七个章节名称与顺序')
        if not _strings(s.get('bullets'),1,6,80):
            raise ValueError('每页应有1至6条要点，每条不超过80字')
    qs=data.get('recommended_question_ids')
    if not _strings(qs,1,8,80) or len(set(qs))!=len(qs):
        raise ValueError('请推荐1至8道不同练习')
    for qid in qs:
        if qid not in BANK or BANK[qid]['card_id']!=COURSES[packet['course_id']]['card_id']:
            raise ValueError('推荐题号不存在或不属于本课程')
    # Explicit allow-list: ignore model-supplied counts, HTML, paths and unexpected fields.
    return {k:data[k] for k in ('schema_version','course_id','topic','evidence_packet_id',
                                'evidence_ids','sections','recommended_question_ids')}


def plan_template(packet):
    qids=[qid for qid,q in BANK.items() if q['card_id']==COURSES[packet['course_id']]['card_id']]
    return dict(schema_version='biohps-mentor-plan-1',course_id=packet['course_id'],
        topic=packet['topic'], evidence_packet_id=packet['packet_id'],
        evidence_ids=[e['evidence_id'] for e in packet['evidence']],
        sections=[dict(title=t,bullets=['请导师结合证据填写本页教学要点']) for t in SECTION_TITLES],
        recommended_question_ids=qids[:2])


def as_lesson(plan,packet):
    return dict(topic=plan['topic'],sections=plan['sections'],source_report=packet['summary'],
        status='导师审核编辑的备课初稿',
        disclaimer='依据网站演示身份记录整理，不能作为真实课堂效果证明。')


def task_card(plan, instructions):
    if not isinstance(instructions,str) or not 1<=len(instructions.strip())<=500:
        raise ValueError('请填写不超过500字的学习任务')
    card=dict(schema_version='biohps-learning-task-1',course_id=plan['course_id'],
              topic=plan['topic'],instructions=instructions.strip(),
              question_ids=plan['recommended_question_ids'])
    card['task_id']=_digest(card)
    return card


def validate_task(raw):
    card=parse_json(raw)
    if card.get('schema_version')!='biohps-learning-task-1':
        raise ValueError('请选择导师导出的学习任务卡')
    course=_course(card.get('course_id'))
    if card.get('topic')!=course['topic']:
        raise ValueError('任务主题不一致')
    ids=card.get('question_ids')
    if not _strings(ids,1,8,80) or len(set(ids))!=len(ids):
        raise ValueError('任务题号无效')
    if any(i not in BANK or BANK[i]['card_id']!=course['card_id'] for i in ids):
        raise ValueError('任务包含不属于本专题的题目')
    expected=task_card(dict(course_id=card['course_id'],topic=card['topic'],
                           recommended_question_ids=ids),card.get('instructions'))
    if card.get('task_id')!=expected['task_id']:
        raise ValueError('任务卡内容与编号不一致，请从导师端重新导出')
    return expected
