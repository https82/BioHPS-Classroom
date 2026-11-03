"""Local cross-role records for a small, non-authenticated contest DEMO.

This is deliberately NOT a production student-data store or an authentication system.
Users must only enter fictional demo questions/identities. DB is not included in release ZIPs.
"""
import os
import sqlite3
from contextlib import contextmanager
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DEMO_STUDENTS={
 's1': {'label':'演示学生A','profile':'概念辨析需要支持'},
 's2': {'label':'演示学生B','profile':'喜欢科学史探究'},
 's3': {'label':'演示学生C','profile':'实验控制变量需巩固'},
 's4': {'label':'演示学生D','profile':'尝试综合拓展'},
}


def db_path():
    raw=os.environ.get('BIOHPS_DEMO_DB','').strip()
    return Path(raw).expanduser() if raw else ROOT/'demo_data'/'class_demo.sqlite'


def connect(path=None):
    path=Path(path) if path is not None else db_path()
    path.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(str(path),timeout=10)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=10000')
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


@contextmanager
def database(path=None):
    con=connect(path)
    try:
        with con:
            yield con
    finally:
        con.close()


def initialize(path=None):
    with database(path) as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS student_questions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          stage TEXT NOT NULL,
          text TEXT NOT NULL,
          topic TEXT NOT NULL,
          card_id TEXT,
          answer_source TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS attempts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          question_id TEXT NOT NULL,
          card_id TEXT NOT NULL,
          stage TEXT NOT NULL,
          topic TEXT NOT NULL,
          answer_idx INTEGER NOT NULL,
          correct INTEGER NOT NULL CHECK (correct IN (0,1)),
          error_tag TEXT NOT NULL,
          question_type TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS experiment_trials (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          kind TEXT NOT NULL,
          controlled INTEGER NOT NULL CHECK(controlled IN (0,1)),
          changed_count INTEGER NOT NULL,
          changed_fields TEXT NOT NULL,
          details TEXT
        );
        CREATE TABLE IF NOT EXISTS hps_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          course_id TEXT NOT NULL,
          event_type TEXT NOT NULL,
          payload TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_hps_student ON hps_events(student_id);
        CREATE TABLE IF NOT EXISTS story_attempts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          story_id TEXT NOT NULL,
          title TEXT NOT NULL,
          selected TEXT NOT NULL,
          correct INTEGER NOT NULL CHECK (correct IN (0,1))
        );
        CREATE INDEX IF NOT EXISTS idx_story_student ON story_attempts(student_id);
        CREATE INDEX IF NOT EXISTS idx_hps_course ON hps_events(course_id);
        CREATE TABLE IF NOT EXISTS assignments (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          stage TEXT NOT NULL,
          chapter TEXT NOT NULL,
          note TEXT NOT NULL,
          active INTEGER NOT NULL DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_questions_student ON student_questions(student_id);
        CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id);
        ''')

    # Existing local V9/V10 databases may predate the details field.
    with database(path) as con:
        names={r[1] for r in con.execute('PRAGMA table_info(experiment_trials)')}
        if 'details' not in names:
            con.execute('ALTER TABLE experiment_trials ADD COLUMN details TEXT')


def _now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _student_ok(student_id):
    if student_id not in DEMO_STUDENTS:
        raise ValueError('仅允许四个预设演示学生身份')


def add_question(student_id,text,stage,topic,card_id='',answer_source='离线参考'):
    _student_ok(student_id)
    text=str(text).strip()
    if not 2<=len(text)<=500:raise ValueError('提问需为2—500字')
    with database() as con:
        cur=con.execute('''INSERT INTO student_questions
          (student_id,created_at,stage,text,topic,card_id,answer_source)
          VALUES (?,?,?,?,?,?,?)''',
          (student_id,_now(),str(stage)[:16],text,str(topic)[:100],str(card_id)[:32],str(answer_source)[:32]))
        return cur.lastrowid


def add_attempt(student_id,question,answer_idx):
    _student_ok(student_id)
    if type(answer_idx) is not int or not 0<=answer_idx<len(question['options']):
        raise ValueError('无效选项')
    ok=answer_idx==question['answer']
    with database() as con:
        cur=con.execute('''INSERT INTO attempts
          (student_id,created_at,question_id,card_id,stage,topic,answer_idx,correct,error_tag,question_type)
          VALUES (?,?,?,?,?,?,?,?,?,?)''',
          (student_id,_now(),question['id'],question['card_id'],question['grade'],question['topic'],
           answer_idx,int(ok),str(question['error_tag'])[:150],question['type']))
        return {'id':cur.lastrowid,'correct':ok,'right_idx':question['answer']}


def student_questions(student_id,limit=40):
    _student_ok(student_id)
    with database() as con:
        return [dict(r) for r in con.execute(
            'SELECT * FROM student_questions WHERE student_id=? ORDER BY id DESC LIMIT ?', (student_id,limit))]


def student_attempts(student_id,limit=120):
    _student_ok(student_id)
    with database() as con:
        return [dict(r) for r in con.execute(
            'SELECT * FROM attempts WHERE student_id=? ORDER BY id DESC LIMIT ?', (student_id,limit))]


def recent_questions(limit=100):
    with database() as con:
        return [dict(r) for r in con.execute('SELECT * FROM student_questions ORDER BY id DESC LIMIT ?', (limit,))]


def all_attempts(limit=2000):
    with database() as con:
        return [dict(r) for r in con.execute('SELECT * FROM attempts ORDER BY id DESC LIMIT ?', (limit,))]


def report():
    """Return only data derived from actual saved activities, with no seeded achievements."""
    questions=recent_questions()
    attempts=all_attempts()
    participants={r['student_id'] for r in questions+attempts}
    participation_hps=hps_events()
    story_actions=story_attempts()
    participants.update(r['student_id'] for r in participation_hps)
    participants.update(r['student_id'] for r in story_actions)
    question_topics=Counter(r['topic'] for r in questions)
    wrong_topics=Counter(r['topic'] for r in attempts if not r['correct'])
    attempts_topics=Counter(r['topic'] for r in attempts)
    correct_topics=Counter(r['topic'] for r in attempts if r['correct'])
    errors=Counter(r['error_tag'] for r in attempts if not r['correct'])
    ranking=sorted(set(question_topics)|set(attempts_topics),key=lambda t:(-2*wrong_topics[t]-question_topics[t],t))
    focus=[{
       'topic':t,'questions':question_topics[t], 'attempts':attempts_topics[t],
       'correct':correct_topics[t], 'wrong':wrong_topics[t],
       'accuracy':round(correct_topics[t]/attempts_topics[t]*100,1) if attempts_topics[t] else None,
    } for t in ranking]
    students=[]
    for sid,info in DEMO_STUDENTS.items():
        acts=[r for r in attempts if r['student_id']==sid]
        qs=[r for r in questions if r['student_id']==sid]
        students.append({'id':sid,'name':info['label'],'questions':len(qs),'attempts':len(acts),
                         'hps_events':sum(r['student_id']==sid for r in participation_hps)+sum(r['student_id']==sid for r in story_actions),
                         'wrong':sum(not r['correct'] for r in acts),
                         'correct':sum(bool(r['correct']) for r in acts)})
    experiments=all_experiments()
    participants.update(r['student_id'] for r in experiments)
    return {
        'experiments':len(experiments),
        'experiment_control_errors':sum(not r['controlled'] for r in experiments),
        'participants':len(participants),'questions':len(questions),
        'attempts':len(attempts),'correct':sum(bool(r['correct']) for r in attempts),
        'wrong':sum(not r['correct'] for r in attempts),
        'hps_attempts':sum(r['question_type']=='HPS科学探究' for r in attempts),
        'story_attempts':len(story_actions),
        'story_wrong':sum(not r['correct'] for r in story_actions),
        'question_topics':dict(question_topics),'error_tags':dict(errors),
        'focus':focus,'students':students,'recent_questions':questions[:30],
        'sample_only':True,
    }


def student_summary(student_id):
    answers=student_attempts(student_id)
    questions=student_questions(student_id)
    latest_by_question={}
    for r in answers:
        latest_by_question.setdefault(r['question_id'],r)
    needs=Counter(r['topic'] for r in latest_by_question.values() if not r['correct'])
    return {'questions':questions,'attempts':answers,'latest':list(latest_by_question.values()),
            'needs_review':needs,'answered':len(answers),
            'correct':sum(r['correct'] for r in answers)}


def reset_demo(confirmed=False):
    if not confirmed:raise ValueError('需要明确确认后才能清空演示记录')
    with database() as con:
        con.execute('DELETE FROM attempts')
        con.execute('DELETE FROM student_questions')
        con.execute('DELETE FROM assignments')
        con.execute('DELETE FROM experiment_trials')
        con.execute('DELETE FROM hps_events')
        con.execute('DELETE FROM story_attempts')


def post_assignment(stage,chapter,note):
    note=str(note).strip()[:300]
    if not chapter or not note:raise ValueError('任务主题和说明不能为空')
    with database() as con:
        cur=con.execute('INSERT INTO assignments(created_at,stage,chapter,note) VALUES (?,?,?,?)',
                        (_now(),str(stage)[:16],str(chapter)[:100],note))
        return cur.lastrowid


def active_assignments(limit=10):
    with database() as con:
        return [dict(r) for r in con.execute('SELECT * FROM assignments WHERE active=1 ORDER BY id DESC LIMIT ?', (limit,))]


def close_assignment(assignment_id):
    with database() as con:
        con.execute('UPDATE assignments SET active=0 WHERE id=?',(int(assignment_id),))


def add_experiment(student_id,kind,comparison,first=None,second=None):
    import json
    _student_ok(student_id)
    controlled=bool(comparison['controlled'])
    names=comparison.get('changed_labels',[])
    payload={'comparison':comparison}
    if first and second:
        from virtual_lab import explain_observation
        payload['first']=first['config']
        payload['second']=second['config']
        payload['observation']=explain_observation(kind,first,second,comparison)
    details=json.dumps(payload,ensure_ascii=False)[:4000]
    with database() as con:
        return con.execute('''INSERT INTO experiment_trials
          (student_id,created_at,kind,controlled,changed_count,changed_fields,details)
          VALUES (?,?,?,?,?,?,?)''',
          (student_id,_now(),str(kind)[:80],int(controlled),len(names),'、'.join(names)[:120],details)).lastrowid


def all_experiments(limit=500):
    with database() as con:
        return [dict(r) for r in con.execute('SELECT * FROM experiment_trials ORDER BY id DESC LIMIT ?', (limit,))]


def student_experiments(student_id,limit=50):
    _student_ok(student_id)
    with database() as con:
        return [dict(r) for r in con.execute('''SELECT * FROM experiment_trials WHERE student_id=?
             ORDER BY id DESC LIMIT ?''',(student_id,limit))]


# V10: actual student HPS choices and model observations shared with teacher.
def add_hps_event(student_id,course_id,event_type,payload):
    import json
    _student_ok(student_id)
    if course_id not in ('B2-S01','B2-S03'):
        raise ValueError('无效课程')
    if event_type not in ('pollination','prediction','f2_trial','testcross','conclusion','meiosis_step'):
        raise ValueError('无效活动类型')
    if not isinstance(payload,dict):raise ValueError('记录结构无效')
    serialized=json.dumps(payload,ensure_ascii=False,sort_keys=True)
    if len(serialized)>3500:raise ValueError('学习记录过长')
    with database() as con:
        cur=con.execute('INSERT INTO hps_events(student_id,created_at,course_id,event_type,payload) VALUES (?,?,?,?,?)',
                       (student_id,_now(),course_id,event_type,serialized))
        return cur.lastrowid


def hps_events(student_id=None,course_id=None,limit=1000):
    if student_id is not None:_student_ok(student_id)
    if course_id is not None and course_id not in ('B2-S01','B2-S03'):raise ValueError('无效课程')
    import json
    wheres=[];args=[]
    if student_id is not None:wheres.append('student_id=?');args.append(student_id)
    if course_id is not None:wheres.append('course_id=?');args.append(course_id)
    where=' WHERE '+' AND '.join(wheres) if wheres else ''
    with database() as con:
        rows=con.execute('SELECT * FROM hps_events'+where+' ORDER BY id DESC LIMIT ?',(*args,limit))
        return [{**dict(r),'data':json.loads(r['payload'])} for r in rows]


def hps_report():
    events=hps_events()
    by_type=Counter((r['course_id'],r['event_type']) for r in events)
    errors=Counter()
    for r in events:
        d=r['data']
        if r['event_type']=='meiosis_step' and not d.get('correct'):
            errors['减数分裂：'+d.get('stage','阶段错误')]+=1
        elif r['event_type']=='pollination' and not d.get('correct'):
            errors['豌豆杂交操作顺序']+=1
        elif r['event_type']=='prediction' and not d.get('sound'):
            errors['孟德尔：遗传因子假说与F₂预测']+=1
        elif r['event_type']=='testcross' and not d.get('prediction_correct'):
            errors['孟德尔：测交比例预测']+=1
        elif r['event_type']=='conclusion' and not d.get('sound'):
            errors['遗传证据推理']+=1
    people=len({r['student_id'] for r in events})
    return {'events':len(events),'participants':people,'by_type':dict(by_type),
            'errors':dict(errors),'recent':events[:40]}


# Lightweight HPS history inquiry: five fictional students only, no registration.
def add_story_attempt(student_id,story_id,title,correct,selected):
    _student_ok(student_id)
    if len(str(story_id))>60 or not str(story_id):raise ValueError('无效的科学史课程')
    with database() as con:
        return con.execute(
            'INSERT INTO story_attempts (student_id,created_at,story_id,title,selected,correct) VALUES (?,?,?,?,?,?)',
            (student_id,_now(),str(story_id),str(title)[:100],str(selected)[:200],int(bool(correct)))
        ).lastrowid

def story_attempts(student_id=None,limit=300):
    if student_id is not None:_student_ok(student_id)
    with database() as con:
        if student_id is not None:
            rows=con.execute('SELECT * FROM story_attempts WHERE student_id=? ORDER BY id DESC LIMIT ?',
                             (student_id,limit))
        else:
            rows=con.execute('SELECT * FROM story_attempts ORDER BY id DESC LIMIT ?',(limit,))
        return [dict(r) for r in rows]
