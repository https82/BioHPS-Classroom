"""Audit the planned high-school outline; no fake content-completion claims."""
from pathlib import Path
import json
x=json.loads((Path(__file__).resolve().parents[1]/'knowledge/course_construction_plan.json').read_text(encoding='utf8'))
print('规划章节',len(x['sections']),'候选知识节点',len(x['atoms']),'HPS候选',len(x['hps']))
print('高中规划配额',sum(s['quota'] for s in x['sections']))
print('初高中总配额',sum(x['targets'].values()))
print('说明：这些是课程目录与拟建设指标，均不等于已经制作或教师审核的成品。')
