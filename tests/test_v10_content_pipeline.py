import copy
import pytest
from content_registry import read_plan,load_reviewed_resources,validate_resource_card


def a_card():
    return dict(card_id='B2-S01-CON-001',section_id='B2-S01',node_ids=['B2-S01-K01'],kind='概念与机制',
      title='豌豆适合遗传学研究的原因',
      explanation=('科学实验的材料选择必须服务于可检验的问题。豌豆既能自花传粉，在一定条件下维持相对稳定的纯种材料，又有易于区分的相对性状。研究者能够有意识地控制人工授粉过程，并用后代的性状比例来检验不同遗传假说。教材中常以高茎和矮茎为例，分别讨论亲本、子一代以及子二代的表型，并让学生解释为什么子一代没有出现的性状可以在子二代重现。与只观察一株豌豆相比，统计足够后代有助于区分随机波动与系统性的规律。'),
      misconception='不能因为F1都表现显性性状，就认为隐性遗传因子已经消失。',
      example='纯合高茎和纯合矮茎杂交得到Aa，子代显性表型不意味着纯合。',
      limits='仅表示一对等位基因且完全显性的教学模型，不涵盖复杂性状。',
      source_urls=['https://www.pep.com.cn'],approval='待审核',reviewer='',revision=1)


def test_course_plan_loaded():
    p=read_plan()
    assert len(p['sections'])==82
    assert len(p['atoms'])==854
    assert len(p['hps'])==42
    assert load_reviewed_resources()==[]


def test_review_gate_requires_substantial_original_content():
    c=a_card();assert validate_resource_card(c)
    c2=copy.deepcopy(c);c2['explanation']='概念简介。'
    with pytest.raises(ValueError):validate_resource_card(c2)
    c2=copy.deepcopy(c);c2['approval']='已审核'
    with pytest.raises(ValueError):validate_resource_card(c2)
    c2=copy.deepcopy(c);c2['node_ids']=['B1-S01-K01']
    with pytest.raises(ValueError):validate_resource_card(c2)
