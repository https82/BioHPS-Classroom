"""Run from repository root: python tools/v7_preflight.py (offline, zero API cost)."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from learning_loop import BANK,new_session,current_question,submit_answer,start_recheck
from virtual_lab import EXPERIMENTS,make_trial,compare_trials
from curriculum import load_cards,THEMES,retrieve

REQUIRED=('app.py','curriculum.py','retrieval_index.py','engine.py','service.py',
          'presentation.py','learning_loop.py','virtual_lab.py','requirements.txt',
          'knowledge/library.json','knowledge/curriculum_cards.json')
missing=[f for f in REQUIRED if not (ROOT/f).is_file()]
assert not missing,'缺少文件：'+', '.join(missing)
assert not (ROOT/'.streamlit/secrets.toml').exists(), '检测到本地Secret：禁止上传这个目录到公开GitHub'

cards=load_cards(ROOT)
assert len(cards)>=153, '知识库张数比V6.2少，检查是否完整复制'
assert len(set(c['id'] for c in cards))==len(cards),'知识卡ID有重复'
assert set(THEMES).issubset({c['theme'] for c in cards})

for cid in BANK:
    assert cid in {c['id'] for c in cards},cid
    session=new_session(cid)
    current=current_question(session)
    session,_=submit_answer(session,(current['right']+1)%len(current['options']))
    assert session['phase']=='remediate'
    session=start_recheck(session)
    session,_=submit_answer(session,current_question(session)['right'])
    assert session['phase']=='passed'

cases=[('鲸鱼为什么不是鱼？','BIO-007'),('肺泡为什么适合气体交换？','BIO-021'),('叶子秋天为什么变黄？','BIO-105')]
for query, expected in cases:
    hits,_=retrieve(query,cards)
    assert expected in [item['id'] for item in hits[:3]],f'{query} 未在前三匹配到 {expected}'

light_a={'light':20,'temperature':25,'co2':'充足','water':'充足'}
light_b={'light':80,'temperature':25,'co2':'充足','water':'充足'}
light_c={**light_b,'temperature':39}
assert compare_trials(make_trial('光合作用',light_a),make_trial('光合作用',light_b))['controlled']
assert not compare_trials(make_trial('光合作用',light_a),make_trial('光合作用',light_c))['controlled']
print('PASS：代码依赖文件完整，未包含Secrets')
print('PASS：课程知识卡',len(cards),'张、主题',len(THEMES),'个')
print('PASS：精选学习闭环',len(BANK),'知识点，均可执行答错→纠错→复测')
print('PASS：课程自动检索3道冒烟题')
print('PASS：虚拟实验',len(EXPERIMENTS),'种、单变量与变量混杂检查')
print('此检查离线完成，不调用模型，不证明真实教学效果或公网可访问。')
