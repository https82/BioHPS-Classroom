"""Summarize manually scored paired probes; never fabricate missing scores."""
import argparse,csv,statistics,sys
from collections import defaultdict
from pathlib import Path

SCORES=['科学准确性_0至2','错误识别_0至2','引导适切性_0至2','依据一致性_0至2']

def summarize(path):
    with Path(path).open('r',encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    samples=defaultdict(dict)
    for r in rows:samples[r['case_id']][r['system']]=r
    print('配对题数',len(samples),'| 完整配对题数',sum(len(group)==2 for group in samples.values()))
    for metric in SCORES:
        pairs=[]
        for item in samples.values():
            a=item.get('BioHPS'); b=item.get('普通教学基线')
            if not a or not b or a['status']!='成功' or b['status']!='成功':continue
            s1=a.get(metric,'').strip();s2=b.get(metric,'').strip()
            if not s1 or not s2:continue
            try:x,y=float(s1),float(s2)
            except ValueError:raise ValueError(f'非法评分，指标={metric}；仅允许0、1、2或空白')
            if x not in (0,1,2) or y not in (0,1,2):raise ValueError(f'超出0～2的评分: {metric}')
            pairs.append((x,y))
        if pairs:
            print(f'{metric}: 有效配对={len(pairs)} BioHPS均分={statistics.mean(x for x,y in pairs):.2f} '
                  f'基线均分={statistics.mean(y for x,y in pairs):.2f} '
                  f'均值差={statistics.mean(x-y for x,y in pairs):+.2f}')
        else:print(f'{metric}: 暂无有效的已评配对')
    print('提醒：小样本仅为探索性开发测试，不代表统计显著、课堂学习效果或赛事获奖概率。')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('教师待评_csv');args=p.parse_args()
    summarize(args.教师待评_csv)
