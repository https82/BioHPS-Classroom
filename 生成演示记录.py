"""Create a new, clearly labelled demo DB. Never overwrite an existing DB."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
target = ROOT / 'demo_data' / 'contest_sample.sqlite'
if target.exists():
    raise SystemExit('演示文件已存在，保留现有记录：' + str(target))
packet = json.loads((ROOT / 'contest_examples' / '专题学情_程序演示.json').read_text(encoding='utf-8'))
os.environ['BIOHPS_DEMO_DB'] = str(target)
import demo_store as ds
from question_bank import BANK
from teaching_exchange import build_evidence

ds.initialize()
aliases = {'demo-A': 's1', 'demo-B': 's2', 'demo-C': 's3', 'demo-D': 's4'}
for e in packet['evidence']:
    student = aliases[e['learner_alias']]
    if e['kind'] == 'attempt':
        q = BANK[e['question_id']]
        answer = q['options'].index(e['selected_answer'])
        ident = ds.add_attempt(student, q, answer)['id']
        table = 'attempts'
    elif e['kind'] == 'question':
        ident = ds.add_question(student, e['text'], '高中', packet['topic'],
                                'HS-028' if packet['course_id'] == 'B2-S01' else 'HS-025',
                                e['answer_source'])
        table = 'student_questions'
    else:
        raise SystemExit('当前演示包仅支持提问与作答样例')
    if str(ident) != e['evidence_id'].split('-')[1]:
        raise SystemExit('演示编号不一致，请核对样例')
    with ds.database() as con:
        con.execute(f'UPDATE {table} SET created_at=? WHERE id=?', (e['created_at'], ident))
actual = build_evidence(packet['course_id'])
if actual['packet_id'] != packet['packet_id']:
    raise SystemExit('演示数据版本不一致，请核对样例；未改动已有其他数据库')
print('已创建预设演示身份的程序样例，不是真实课堂数据：' + str(target))
