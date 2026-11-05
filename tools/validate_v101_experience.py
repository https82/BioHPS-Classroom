"""Auditable, no-network product gate for V10.1. Does not pretend to be real-browser QA."""
from pathlib import Path
import ast
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from course_catalog import load_plan,books,chapters,sections,terms,deep_teaching_question,quality_state
from curriculum import load_all_cards,make_course_messages
from deep_lessons import LESSONS
p=load_plan()
q=quality_state(p)
assert q['books']==5 and q['sections']==82 and q['candidate_concepts']==854 and q['target_cards']==5000
assert all(chapters(p,b) for b,_ in books(p))
assert all(terms(p,s['section_id']) for s in p['sections'])
cards=load_all_cards(root)
assert len(cards)==265, len(cards)
assert len(LESSONS)==2
prompt=deep_teaching_question('高中','遗传与进化','孟德尔的豌豆杂交实验','分离定律')
assert '完整' in prompt and '不泄露答案' in prompt
msgs=make_course_messages('为什么',cards[:1],history=[('user','这是关于鲸的问题'),('assistant','鲸是哺乳动物')])
assert msgs[-1]['content']=='为什么' and any(x['role']=='assistant' for x in msgs)
source=(root/'app.py').read_text(encoding='utf-8')
ast.parse(source)
for required in ['首页','AI学习助手','课程学习','教师工作台','student_ask','student_course','st.chat_input','st.chat_message','load_plan','render_flagship']:
    assert required in source, required
assert "['首页','课程学习','AI学习助手','章节练习','科学探究','学习档案']" in source
print('PASS: V10.1 content truth, navigation, AI history, chapter map and source parse')
print('Current content: 265 seed summaries; 2 deep courses; 5000 future target')
