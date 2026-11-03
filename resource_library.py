"""Read-only on-disk learning-resource catalogue used by student and teacher screens.

Internal provenance/status metadata is intentionally NOT exposed by any student UI.
Never use 5000 records as a prompt context all at once; select a few by topic.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from collections import defaultdict, Counter
import json,re

ROOT=Path(__file__).resolve().parent
PATH=ROOT/'knowledge'/'learning_resources_5000.jsonl'
CATEGORY_ORDER=['概念与机制','易错辨析','HPS科学史与证据','实验与建模','衔接与先修','应用伦理']

@lru_cache(maxsize=1)
def records():
    return tuple(json.loads(line) for line in PATH.read_text('utf-8').splitlines() if line.strip())

@lru_cache(maxsize=1)
def indices():
    by_node=defaultdict(list);by_section=defaultdict(list);by_term=defaultdict(list)
    for r in records():
        by_node[r['knowledge_id']].append(r)
        if r['section_id']:by_section[r['section_id']].append(r)
        by_term[(r['stage'],r['term'])].append(r)
    for seq in (*by_node.values(),*by_section.values(),*by_term.values()):
        seq.sort(key=lambda x:(CATEGORY_ORDER.index(x['category']),x['id']))
    return by_node,by_section,by_term


def by_knowledge(node_id,category=None,limit=15):
    items=indices()[0].get(node_id,())
    return [r for r in items if not category or r['category']==category][:limit]


def by_selected_term(section_id,term,limit=18):
    res=[r for r in indices()[1].get(section_id,()) if r['term']==term]
    return res[:limit]


def by_junior_card(seed_id,limit=20):
    return by_knowledge(seed_id,limit=limit)


def search(query,stage=None,limit=3):
    """Strong title anchors only, to avoid false matches from section prose.

    Indexed over unique nodes (not five thousand repeated documents); deterministic
    and suitable for the small public competition demonstration.
    """
    q=''.join(re.findall(r'[\u4e00-\u9fffA-Za-z0-9]+',str(query))).lower()
    if len(q)<2:return []
    by_node=indices()[0]
    results=[]
    for group in by_node.values():
        r=group[0]
        if stage in ('初中','高中') and r['stage']!=stage:continue
        key=''.join(re.findall(r'[\u4e00-\u9fffA-Za-z0-9]+',r['term'])).lower()
        if len(key)<2:continue
        if key in q:score=20+min(len(key),15)
        elif q in key and len(q)>=4:score=8+len(q)
        else:continue
        # Favor a factual explanation over an activity card.
        winner=next((c for c in group if c['category']=='概念与机制'),group[0])
        results.append((score,winner))
    results.sort(key=lambda x:(-x[0],x[1]['id']))
    return [r for _,r in results[:limit]]


def summary():
    all_records=records()
    return {'total':len(all_records), 'scope':dict(Counter(r['scope'] for r in all_records)),
            'knowledge_nodes':len(indices()[0]),'sections':len({r['section_id'] for r in all_records if r['stage']=='高中'})}
