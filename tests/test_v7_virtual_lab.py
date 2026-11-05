"""Verify deterministic results, unconfounded comparisons, and safety labels."""
import json
import pytest
from virtual_lab import EXPERIMENTS,make_trial,simulate,compare_trials,validate_config

PHOTO_A={'light':20,'temperature':25,'co2':'充足','water':'充足'}
PHOTO_B={'light':80,'temperature':25,'co2':'充足','water':'充足'}
SEED_A={'moisture':'适量','temperature':25,'oxygen':'充足'}
SEED_B={'moisture':'干燥','temperature':25,'oxygen':'充足'}

@pytest.mark.parametrize('kind,a,b', [('光合作用',PHOTO_A,PHOTO_B),('种子萌发',SEED_A,SEED_B)])
def test_single_factor_control(kind,a,b):
    first=make_trial(kind,a,'我预测会有差别','A')
    second=make_trial(kind,b,'我预测会有差别','B')
    outcome=compare_trials(first,second)
    assert outcome['controlled'] and len(outcome['changed_fields'])==1
    assert '不构成真实生物实验' in outcome['caution']
    assert '非真实实验观测' in first['source']
    assert json.loads(json.dumps([first,second],ensure_ascii=False))==[first,second]


def test_multivariable_confounds_prevent_attribution():
    a=make_trial('光合作用',PHOTO_A)
    b=make_trial('光合作用',{**PHOTO_B,'temperature':39})
    result=compare_trials(a,b)
    assert not result['controlled'] and set(result['changed_fields'])=={'light','temperature'}
    assert '变量混杂' in result['verdict']


def test_same_conditions_provide_no_variable_evidence():
    a=make_trial('种子萌发',SEED_A)
    b=make_trial('种子萌发',SEED_A)
    res=compare_trials(a,b)
    assert res['changed_fields']==[] and not res['controlled']


def test_results_are_ordinal_not_calibrated_measurement():
    for kind,config in [('光合作用',PHOTO_B),('种子萌发',SEED_A)]:
        output=simulate(kind,config)
        assert type(output['ordinal_level']) is int
        assert output['ordinal_level'] in (0,1,2,3)
        assert '真实' in output['disclaimer']
        assert output==simulate(kind,config)


def test_invalid_configs_rejected():
    with pytest.raises(ValueError): simulate('不存在',PHOTO_A)
    with pytest.raises(ValueError): simulate('光合作用',{**PHOTO_A,'light':True})
    with pytest.raises(ValueError): simulate('光合作用',{**PHOTO_A,'light':150})
    with pytest.raises(ValueError): simulate('种子萌发',{**SEED_A,'moisture':'不是选项'})
    with pytest.raises(ValueError): simulate('种子萌发',{**SEED_A,'unknown':'x'})
    with pytest.raises(ValueError): compare_trials(make_trial('光合作用',PHOTO_A),make_trial('种子萌发',SEED_A))
