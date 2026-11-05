"""Test natural-language routing, optional categories and safe no-card fallback."""
from curriculum import (load_cards, rank_cards, retrieve, resolve_course_context,
                        make_course_messages, sanitize_course_answer)
import pytest

CARDS=load_cards()

@pytest.mark.parametrize('question,target',[
    ('鲸鱼为什么不是鱼？','BIO-007'),
    ('为什么鲸不是鱼','BIO-007'),
    ('鲸为什么是哺乳动物？','BIO-007'),
    ('海豚和鱼有什么区别','BIO-007'),
    ('鱼怎么呼吸？','BIO-007'),
    ('为什么鲸虽然生活在水里，却属于哺乳动物','BIO-007'),
    ('肺泡为什么能交换气体','BIO-021'),
    ('DNA和染色体的关系是什么？','BIO-027'),
    ('光合作用和呼吸作用有什么区别','BIO-016'),
    ('怎么做种子发芽实验','BIO-014'),
    ('食物链如何形成','BIO-011'),
    ('人体为什么会产生免疫反应','BIO-025'),
    ('显微镜为什么会看到倒像','BIO-002'),
    ('朝着太阳长的植物是什么原因','BIO-013'),
    ('什么是细胞？','BIO-001'),
])
def test_natural_language_auto_route(question,target):
    cards,label=retrieve(question,CARDS)
    assert cards and target in [c['id'] for c in cards[:3]],(question,[(x['id'],x['_score']) for x in cards])
    assert '自动匹配' in label

@pytest.mark.parametrize('question',[
    '为什么生物钟会影响睡眠？',
    '为什么火箭要使用多级推进？',
])
def test_unknown_cards_fall_back_without_chapter_selection(question):
    cards,label=retrieve(question,CARDS)
    assert cards==[]
    messages=make_course_messages(question,cards)
    assert '知识库未匹配到' in messages[0]['content']
    assert '不得输出任何' in messages[0]['content']
    assert messages[-1]['content']==question
    assert '不引用知识卡' in label

def test_reference_sanitization():
    assert sanitize_course_answer('解释参考资料卡：[BIO-999]',[])=='解释'
    assert sanitize_course_answer('解释\n参考资料卡：[BIO-999]',[])=='解释'
    assert 'BIO-999' not in sanitize_course_answer('解释\n参考资料卡：[BIO-999]',[CARDS[0]])
    assert 'BIO-001' in sanitize_course_answer('解释\n参考资料卡：[BIO-001]',[CARDS[0]])

def test_followup_uses_previous_card_without_manual_chapter():
    ctx,_=resolve_course_context('鲸为什么不是鱼',CARDS)
    prior={'knowledge_ids':[ctx[0]['id']]}
    next_ctx,how=resolve_course_context('那这个为什么呢',CARDS,previous=prior)
    assert next_ctx and next_ctx[0]['id']=='BIO-007'
    assert '上一轮' in how
    independent,_=resolve_course_context('火箭的喷嘴为什么是圆形',CARDS,previous=prior)
    assert independent==[]

def test_optional_manual_selection_still_supported():
    cards,label=retrieve('它是什么',CARDS,selected_id='BIO-027')
    assert cards[0]['id']=='BIO-027'
    assert '可选' in label
