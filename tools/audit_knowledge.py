"""Local schema/coverage audit; not a scientific fact-check or teacher review.
Usage: python tools/audit_knowledge.py
"""
import json
from collections import Counter
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from curriculum import load_cards,THEMES

def run():
    cards=load_cards(ROOT)
    errors=[];seen=set();titles=set()
    for i,c in enumerate(cards,1):
        for field in ('id','title','theme','summary','misconception','guide_question','keywords','review_status'):
            if not c.get(field):errors.append(f'卡片{i}缺少{field}')
        if c.get('theme') not in THEMES:errors.append('主题异常:'+str(c.get('id')))
        if c.get('id') in seen:errors.append('ID重复:'+str(c.get('id')))
        seen.add(c.get('id'))
        unique=(c.get('theme'),c.get('title'))
        if unique in titles:errors.append('主题+标题重复:'+str(unique))
        titles.add(unique)
        if len(c.get('summary',''))<25:errors.append('摘要过短:'+str(c.get('id')))
        if not isinstance(c.get('keywords'),list):errors.append('关键词类型错误:'+str(c.get('id')))
        url=str(c.get('curriculum_reference',''))
        if url and not url.startswith('https://www.moe.gov.cn/'):
            errors.append('课程标准来源不在预设域名:'+str(c.get('id')))
    status=Counter(c.get('review_status','未注明') for c in cards)
    report={'total':len(cards),'themes':dict(Counter(c['theme'] for c in cards)),
            'review_status':dict(status),'errors':errors,
            'scope':'程序化结构审查；不等于逐条事实核验或教师审定'}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if not errors else 1

if __name__=='__main__':raise SystemExit(run())
