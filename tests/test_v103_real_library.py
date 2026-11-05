"""Quality-gate for 5,000 materialized learning records and source-to-UI integration."""
from collections import Counter
from pathlib import Path
import ast
import json
from resource_library import records,by_selected_term,by_junior_card,search,summary,indices
from course_catalog import load_plan

ROOT=Path(__file__).resolve().parents[1]
PLAN=load_plan()

def test_materialized_5000():
    p=ROOT/'knowledge'/'learning_resources_5000.jsonl'
    assert p.is_file() and p.stat().st_size>5_000_000
    rs=records()
    assert len(rs)==5000
    assert len({r['id'] for r in rs})==5000
    assert len({r['content'] for r in rs})==5000
    assert min(len(r['content']) for r in rs)>=90
    assert all(r['term'] and r['content'] and r['thinking_question'] for r in rs)

def test_exact_scope_quota():
    assert dict(Counter(x['scope'] for x in records()))==PLAN['targets']
    assert dict(Counter(x['category'] for x in records()))==PLAN['categories']

def test_all_nodes_have_core_explanation():
    group=indices()[0]
    assert len(group)==854+153
    assert all(any(r['category']=='概念与机制' for r in cards) for cards in group.values())
    assert set(x['section_id'] for x in records() if x['stage']=='高中')=={s['section_id'] for s in PLAN['sections']}
    assert len({x['knowledge_id'] for x in records() if x['stage']=='高中'})==854

def test_concept_examples_and_stage():
    for sid,term in [('B1-S01','细胞学说主要内容'),('B2-S01','测交验证假说'),('B2-S03','四分体'),('X3-S08','目的基因获取')]:
        items=by_selected_term(sid,term)
        assert items and any(r['category']=='概念与机制' for r in items)
        assert all(r['stage']=='高中' for r in items)
    assert by_junior_card('BIO-007')
    assert any(r['term']=='四分体' for r in search('四分体怎么形成？','高中'))
    assert all(r['stage']=='初中' for r in search('动物类群','初中'))

def test_private_metadata_not_rendered():
    src=(ROOT/'app.py').read_text('utf8')
    ast.parse(src)
    assert "item['content']" in src
    assert "item['editorial_status']" not in src
    assert "item['source_basis']" not in src
    assert 'by_selected_term' in src and 'search_resources' in src
    assert 'st.chat_input' in src and '学生' in src
