"""Direct tests for the self-authored, transparent practice decision rules."""
import json
from learning_loop import BANK, new_session, current_question, submit_answer, start_recheck, progress_summary
from curriculum import load_cards,THEMES
import pytest


def test_bank_valid_and_covers_all_7_themes():
    cards={c['id']:c for c in load_cards()}
    assert len(BANK)==21
    assert {cards[i]['theme'] for i in BANK}==set(THEMES)
    for ident, item in BANK.items():
        assert ident in cards
        assert item['misconception'] and item['remedy']
        for part in ['initial','recheck']:
            question,options,right=item[part]
            assert question and len(options)==3 and len(set(options))==3
            assert type(right) is int and 0<=right<3
            assert len(options[right])>=1


def test_wrong_answer_never_passes_and_recheck_correction_is_recorded():
    s=new_session('BIO-007','为什么鲸不是鱼？')
    q=current_question(s)
    wrong=(q['right']+1)%3
    s, ev=submit_answer(s,wrong,when='test-clock')
    assert s['phase']=='remediate' and s['initial_correct'] is False
    assert not ev['correct'] and ev['selected'] in q['options']
    assert progress_summary([s])['provisionally_passed']==0
    s=start_recheck(s)
    assert current_question(s)['question'] != q['question']
    s, ev2=submit_answer(s,current_question(s)['right'],when='test-clock')
    assert s['phase']=='passed' and s['recheck_correct'] is True
    assert s['events'][0]['correct'] is False and s['events'][1]['correct'] is True
    assert progress_summary([s])['corrected_after_remedy']==1
    assert json.loads(json.dumps(s,ensure_ascii=False))==s


def test_wrong_recheck_does_not_pass_or_allow_unlimited_guessing():
    s=new_session('BIO-095')
    q=current_question(s)
    s,_=submit_answer(s,(q['right']+1)%3)
    s=start_recheck(s)
    q=current_question(s)
    s,_=submit_answer(s,(q['right']+1)%3)
    assert s['phase']=='remediate' and s['recheck_correct'] is False
    with pytest.raises(ValueError):
        submit_answer(s,q['right'])
    with pytest.raises(ValueError):
        start_recheck(s)


def test_first_try_correct_and_invalid_guardrails():
    s=new_session('BIO-021')
    with pytest.raises(ValueError): submit_answer(s,True)
    with pytest.raises(ValueError): submit_answer(s,99)
    with pytest.raises(ValueError): start_recheck(s)
    s,_=submit_answer(s,current_question(s)['right'])
    assert s['phase']=='passed' and s['mastery'].startswith('初测')
    with pytest.raises(ValueError): start_recheck(s)
    with pytest.raises(ValueError): submit_answer(s,0)
    with pytest.raises(ValueError): new_session('BIO-999')


@pytest.mark.parametrize('ident',list(BANK))
def test_every_card_correct_answer_passes(ident):
    s=new_session(ident)
    s,_=submit_answer(s,current_question(s)['right'])
    assert s['phase']=='passed'

@pytest.mark.parametrize('ident',list(BANK))
def test_every_card_wrong_answer_does_not_pass(ident):
    s=new_session(ident)
    q=current_question(s)
    s,_=submit_answer(s,(q['right']+1)%3)
    assert s['phase']=='remediate' and s['mastery']!='初测答对（暂定）'
