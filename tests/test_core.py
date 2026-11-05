import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from engine import (CASES, CASE_OBJECTIVES, STAGES, stage_gate,
                    misconception_blockers, assess_transition, parse_model_output,
                    validate_concepts_strict, CONCEPTS, make_competition_messages)

WRONG = '我认为鹅颈瓶中的肉汤没有出现微生物，是因为空气完全无法进入瓶内。'
CORRECT_CONCEPT = '我明白了，鹅颈瓶允许空气进入，但弯曲的瓶颈可以截留空气中的尘埃和微生物。'
GOOD_PREDICTION = '如果倾斜鹅颈瓶，让肉汤接触瓶颈积尘，那么肉汤可能出现微生物生长、变得浑浊；保持直立的瓶中肉汤则可能保持澄清。'


def model_result(text, achieved=True):
    return {'achieved':achieved,'confidence':'high','evidence':text[3:35],
            'diagnosis':'样例诊断','feedback':'示例引导','concepts':[]}


def test_clear_false_air_claim_blocks_stage_0():
    assert misconception_blockers('鹅颈瓶实验', WRONG)
    assert not stage_gate(0,'鹅颈瓶实验', WRONG)[0]


def test_corrected_concept_is_not_yet_predicted_outcome():
    assert not misconception_blockers('鹅颈瓶实验',CORRECT_CONCEPT)
    ok, reasons=stage_gate(0,'鹅颈瓶实验',CORRECT_CONCEPT)
    assert not ok and reasons


def test_valid_prediction_satisfies_rule_gate():
    assert stage_gate(0,'鹅颈瓶实验',GOOD_PREDICTION)[0]


def test_model_cannot_force_incorrect_student_answer_to_pass():
    evaluation=assess_transition(model_result(WRONG),'鹅颈瓶实验',0,WRONG)
    assert evaluation['model_claimed'] and not evaluation['accepted']
    assert not evaluation['rule_passed']


def test_model_and_guard_both_needed():
    assert assess_transition(model_result(GOOD_PREDICTION), '鹅颈瓶实验',0, GOOD_PREDICTION)['accepted']
    assert not assess_transition(model_result(GOOD_PREDICTION,False), '鹅颈瓶实验',0, GOOD_PREDICTION)['accepted']


def test_student_evidence_must_be_verbatim():
    result=model_result(GOOD_PREDICTION)
    result['evidence']='学生从未写过的句子'
    assert not assess_transition(result,'鹅颈瓶实验',0,GOOD_PREDICTION)['accepted']


def test_incomplete_json_has_visible_feedback_without_grading():
    raw=json.dumps({'feedback':'请先观察瓶口是否完全密封。','diagnosis':'尚未完成'},ensure_ascii=False)
    text, structured, format_tag=parse_model_output(raw)
    assert text=='请先观察瓶口是否完全密封。'
    assert structured is None
    assert format_tag=='partial_json_feedback_only'
    assert '"feedback"' not in text


def test_complete_json_is_parsed():
    raw=json.dumps({'feedback':'先观察瓶口。','diagnosis':'概念错误','evidence':WRONG[3:30],
                    'achieved':False,'confidence':'high','concepts':[]},ensure_ascii=False)
    feedback,structured,tag=parse_model_output(raw)
    assert feedback=='先观察瓶口。' and structured and tag=='validated_json'


def test_wrong_concept_cannot_be_labelled_correct():
    c=CONCEPTS['鹅颈瓶实验'][0]
    r={'concepts':[{'concept':c,'status':'表现出正确理解','evidence':'空气完全无法进入瓶内'}]}
    assert validate_concepts_strict(r,'鹅颈瓶实验',WRONG)==[]


def test_valid_concept_correction_can_be_tracked():
    c=CONCEPTS['鹅颈瓶实验'][0]
    r={'concepts':[{'concept':c,'status':'表现出正确理解','evidence':'鹅颈瓶允许空气进入'}]}
    assert validate_concepts_strict(r,'鹅颈瓶实验',CORRECT_CONCEPT)


def test_stage_one_requires_variable_and_measurement_and_control():
    s='自变量是倾斜与否，因变量是肉汤是否浑浊，控制变量是肉汤体积、煮沸时间和观察温度保持相同。'
    assert stage_gate(1,'鹅颈瓶实验',s)[0]
    assert not stage_gate(1,'鹅颈瓶实验','自变量是倾斜与否。')[0]


def test_stage_two_requires_control_comparison():
    s='实验组倾斜鹅颈瓶让肉汤接触积尘，对照组保持直立，其余煮沸条件和观察时间相同。'
    assert stage_gate(2,'鹅颈瓶实验',s)[0]
    assert not stage_gate(2,'鹅颈瓶实验','把瓶子倾斜然后看看肉汤。')[0]


def test_stage_three_needs_evidence_and_limit():
    s='观察到倾斜组肉汤浑浊而直立组澄清，说明积尘可能带入微生物，但还需重复试验排除操作污染。'
    assert stage_gate(3,'鹅颈瓶实验',s)[0]
    assert not stage_gate(3,'鹅颈瓶实验','实验完全证明一切生命来自生命。')[0]


def test_three_cases_have_three_prompts():
    assert set(CASES)==set(CASE_OBJECTIVES)
    assert len(STAGES)==4
    for case in CASES:
        assert len(CASE_OBJECTIVES[case]['samples'])==3


def test_model_message_contains_clear_boundaries():
    messages=make_competition_messages([('user',WRONG)],'鹅颈瓶实验',0,[False]*4,{})
    assert messages[0]['role']=='system'
    assert '不要判定当前阶段完成' in messages[0]['content']
    assert messages[-1]['content']==WRONG


def test_library_has_references_but_no_claim_of_rag():
    lib=json.loads((Path(__file__).resolve().parents[1]/'knowledge'/'library.json').read_text(encoding='utf-8'))
    for key in CASES:
        assert lib[key]['references']
        assert all(x['url'].startswith('https://') for x in lib[key]['references'])

# V4.0 product presentation and auditing tests.
from presentation import DEMO_STORY, LIVE_EXAMPLES, clean_model_history, PRODUCT_VALUES


def test_demo_is_marked_as_developer_simulated():
    assert len(DEMO_STORY) == 4
    assert all(item['who'].startswith(('模拟学生', 'BioHPS')) for item in DEMO_STORY)
    assert len(PRODUCT_VALUES) == 5
    assert set(LIVE_EXAMPLES) == set(CASES)


def test_demo_prompts_exist_in_each_scene():
    for name in CASES:
        assert len(LIVE_EXAMPLES[name]) == 3
        assert all(label and text for label,text in LIVE_EXAMPLES[name])


def test_api_failures_are_not_added_to_model_history():
    past=[
        {'status':'调用失败 · HTTP 429','student':'失败问题','reply':'服务暂不可用'},
        {'status':'成功 · validated_json','student':'正确问题','reply':'一个教学问题'},
        {'status':'未调用 · 关闭','student':'没调用的问题','reply':'AI已关闭'},
    ]
    history=clean_model_history(past,'这次的新问题')
    assert history==[('user','正确问题'),('assistant','一个教学问题'),('user','这次的新问题')]


def test_empty_model_history_keeps_current_student_query():
    assert clean_model_history([],'开始测试')==[('user','开始测试')]
