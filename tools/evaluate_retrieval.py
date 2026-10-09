"""40+ curated offline routing examples. Metrics are DEV tests, not a teacher study.
Usage: python tools/evaluate_retrieval.py
"""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from curriculum import load_cards,retrieve

def run():
    cards=load_cards(ROOT)
    tests=json.loads((ROOT/'knowledge'/'retrieval_smoke_cases.json').read_text(encoding='utf-8'))
    top1=top3=miss=0; wrong=[]
    for x in tests:
        hits,_=retrieve(x['question'],cards)
        ids=[z['id'] for z in hits]
        expected=x['expected']
        if expected is None:
            success=not ids
            miss+=success
        else:
            success=expected in ids
            top3+=success
            top1+=(ids[:1]==[expected])
        if not success:wrong.append({'question':x['question'],'expected':expected,'returned':ids})
    total_pos=sum(t['expected'] is not None for t in tests)
    total_neg=len(tests)-total_pos
    print(f'题目数：{len(tests)}（覆盖题{total_pos}，未收录/非生物题{total_neg}）')
    print(f'Top-1命中：{top1}/{total_pos}；Top-3命中：{top3}/{total_pos}；拒绝无关匹配：{miss}/{total_neg}')
    if wrong:
        print('未通过明细：'+json.dumps(wrong,ensure_ascii=False,indent=2))
    print('上述结果为开发者人工编写样例的离线检索测试，不是模型回答正确率或教学效果。')
    return 0 if not wrong else 1

if __name__=='__main__':raise SystemExit(run())
