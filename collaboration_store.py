"""Persistent reviewed learning tasks; learners can submit only their own tasks."""
import json
from datetime import datetime,timezone,timedelta
import demo_store as ds
from question_bank import BANK
from teaching_exchange import validate_task,json_text


def initialize():
    with ds.database() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS learning_tasks (
          id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
          student_id TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL,
          UNIQUE(task_id,student_id));
        CREATE TABLE IF NOT EXISTS learning_task_answers (
          task_row_id INTEGER NOT NULL, question_id TEXT NOT NULL, attempt_id INTEGER NOT NULL,
          PRIMARY KEY(task_row_id,question_id));
        CREATE TABLE IF NOT EXISTS model_requests (
          id INTEGER PRIMARY KEY AUTOINCREMENT, actor TEXT NOT NULL, scene TEXT NOT NULL,
          created_at TEXT NOT NULL);
        ''')


def reserve_request(actor,scene):
    """Bound cost per demo identity, including failed upstream calls; no key in DB."""
    initialize()
    if actor not in (*ds.DEMO_STUDENTS,'teacher'):raise ValueError('无效工作区')
    cutoff=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(timespec='seconds')
    limit=12 if actor=='teacher' else 30
    with ds.database() as con:
        con.execute('BEGIN IMMEDIATE')
        count=con.execute('SELECT count(*) FROM model_requests WHERE actor=? AND created_at>=?',(actor,cutoff)).fetchone()[0]
        if count>=limit:return False
        con.execute('INSERT INTO model_requests(actor,scene,created_at) VALUES (?,?,?)',(actor,scene,ds._now()))
    return True


def publish_task(card,recipients):
    initialize();card=validate_task(json_text(card))
    if not recipients or any(s not in ds.DEMO_STUDENTS for s in recipients):raise ValueError('请选择有效接收学生')
    with ds.database() as con:
        before=con.total_changes
        for student in dict.fromkeys(recipients):
            con.execute('INSERT OR IGNORE INTO learning_tasks(task_id,student_id,created_at,payload) VALUES (?,?,?,?)',
                (card['task_id'],student,ds._now(),json_text(card)))
        return con.total_changes-before


def student_tasks(student):
    ds._student_ok(student);initialize()
    with ds.database() as con:
        rows=[dict(r) for r in con.execute('SELECT * FROM learning_tasks WHERE student_id=? ORDER BY id DESC',(student,))]
        for row in rows:
            row['card']=validate_task(row.pop('payload'))
            row['answers']={r['question_id']:dict(r) for r in con.execute('''SELECT t.question_id,a.answer_idx,a.correct
                FROM learning_task_answers t JOIN attempts a ON a.id=t.attempt_id WHERE t.task_row_id=?''',(row['id'],))}
    return rows


def submit_task_answer(student,task_row_id,question_id,answer_idx):
    ds._student_ok(student);initialize()
    with ds.database() as con:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute('SELECT * FROM learning_tasks WHERE id=? AND student_id=?',(int(task_row_id),student)).fetchone()
        if row is None:raise ValueError('该学习任务不属于当前学生')
        card=validate_task(row['payload'])
        if question_id not in card['question_ids']:raise ValueError('题目不属于本任务')
        existing=con.execute('''SELECT a.id,a.correct FROM learning_task_answers t JOIN attempts a ON a.id=t.attempt_id
            WHERE t.task_row_id=? AND t.question_id=?''',(int(task_row_id),question_id)).fetchone()
        if existing:return dict(existing)
        q=BANK[question_id]
        if type(answer_idx) is not int or not 0<=answer_idx<len(q['options']):raise ValueError('请选择有效选项')
        correct=answer_idx==q['answer']
        cur=con.execute('''INSERT INTO attempts(student_id,created_at,question_id,card_id,stage,topic,
            answer_idx,correct,error_tag,question_type) VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (student,ds._now(),q['id'],q['card_id'],q['grade'],q['topic'],answer_idx,int(correct),q['error_tag'],q['type']))
        con.execute('INSERT INTO learning_task_answers(task_row_id,question_id,attempt_id) VALUES (?,?,?)',
            (int(task_row_id),question_id,cur.lastrowid))
        return {'id':cur.lastrowid,'correct':correct}


def task_progress():
    initialize()
    with ds.database() as con:
        rows=[dict(r) for r in con.execute('''SELECT t.*,count(a.question_id) answered FROM learning_tasks t
            LEFT JOIN learning_task_answers a ON a.task_row_id=t.id GROUP BY t.id ORDER BY t.id DESC''')]
    for row in rows:
        card=validate_task(row.pop('payload'));row['topic']=card['topic'];row['total']=len(card['question_ids'])
    return rows
