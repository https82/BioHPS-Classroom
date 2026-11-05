"""Content and state-machine QA. No invented student data are seeded."""
import json
import os
import pytest
from hps_models import offspring_distribution,simulate_cross,meiosis_step,MEIOSIS_STAGES
from deep_lessons import LESSONS
from flagship_questions import QUESTIONS
from question_bank import BANK
import demo_store as ds

@pytest.fixture(autouse=True)
def fresh_data(monkeypatch,tmp_path):
    monkeypatch.setenv('BIOHPS_DEMO_DB',str(tmp_path/'classroom.sqlite'))
    ds.initialize()

@pytest.mark.parametrize('mother,father,probs',[
    ('AA','aa',{'AA':0,'Aa':1,'aa':0}),
    ('Aa','Aa',{'AA':.25,'Aa':.5,'aa':.25}),
    ('Aa','aa',{'AA':0,'Aa':.5,'aa':.5}),
    ('aa','Aa',{'AA':0,'Aa':.5,'aa':.5}),
])
def test_genetics_probabilities(mother,father,probs):
    assert offspring_distribution(mother,father)==probs

@pytest.mark.parametrize('n', [16,64,256,1024])
def test_reproducible_samples_not_fixed_to_ratio(n):
    a=simulate_cross('Aa','Aa',n,seed=31)
    b=simulate_cross('Aa','Aa',n,seed=31)
    assert a==b and sum(a['genotypes'].values())==n
    assert a['phenotypes']['高茎']+a['phenotypes']['矮茎']==n

@pytest.mark.parametrize('value', [0,2001,'64'])
def test_invalid_sample_sizes(value):
    with pytest.raises(ValueError):simulate_cross('Aa','Aa',value)

@pytest.mark.parametrize('stage',MEIOSIS_STAGES)
def test_meiosis_phase_counts_and_choices(stage):
    result=meiosis_step(stage['id'],stage['right'])
    assert result['correct'] and result['chromosomes']==stage['count'][0]
    assert result['dna']==stage['count'][1]
    assert result['cells']==stage['cells']
    bad=meiosis_step(stage['id'],stage['wrong'][0])
    assert not bad['correct']

@pytest.mark.parametrize('slug', ['mendel','meiosis'])
def test_flagship_lessons_have_explanations_and_history(slug):
    item=LESSONS[slug]
    assert len(item['sections'])>=6 and len(item['goals'])>=4
    assert sum(len(x[1]) for x in item['sections'])>1000
    assert item['history'][0] and item['misconceptions']

@pytest.mark.parametrize('question',list(QUESTIONS.values()),ids=list(QUESTIONS))
def test_flagship_bank_grounded(question):
    assert question['id'] in BANK
    assert len(set(question['options']))==len(question['options'])
    assert question['answer'] in range(len(question['options']))
    assert len(question['explanation'])>=12


def test_real_cross_role_events_and_reset():
    assert ds.hps_report()['events']==0
    ds.add_hps_event('s1','B2-S01','pollination',{'correct':False,'female':'AA'})
    ds.add_hps_event('s1','B2-S01','f2_trial',{'n':64,'seed':10,'high':51,'short':13})
    ds.add_hps_event('s2','B2-S03','meiosis_step',{'correct':False,'stage':'MI'})
    assert ds.hps_report()['participants']==2
    assert ds.report()['participants']==2
    assert len(ds.hps_events('s1'))==2 and len(ds.hps_events('s2'))==1
    assert ds.hps_report()['errors']['豌豆杂交操作顺序']==1
    assert ds.hps_report()['errors']['减数分裂：MI']==1
    ds.reset_demo(True)
    assert ds.hps_report()['events']==0


def test_invalid_event_types_and_private_data_rejected():
    with pytest.raises(ValueError):ds.add_hps_event('notstudent','B2-S01','prediction',{})
    with pytest.raises(ValueError):ds.add_hps_event('s1','X','prediction',{})
    with pytest.raises(ValueError):ds.add_hps_event('s1','B2-S01','hacked',{})
    with pytest.raises(ValueError):ds.add_hps_event('s1','B2-S01','prediction',{'text':'X'*4000})


def test_full_planned_curriculum_is_plan_not_filled_cards():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    x=json.loads((root/'knowledge'/'course_construction_plan.json').read_text(encoding='utf8'))
    assert len(x['sections'])==82 and len(x['atoms'])==854 and len(x['hps'])==42
    assert sum(s['quota'] for s in x['sections'])==3400
    assert sum(x['targets'].values())==5000
    assert len({s['section_id'] for s in x['sections']})==82
    assert len({a['node_id'] for a in x['atoms']})==854
