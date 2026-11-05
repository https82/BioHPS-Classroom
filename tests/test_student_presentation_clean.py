from pathlib import Path
from curriculum import format_context,make_course_messages

ROOT=Path(__file__).resolve().parents[1]

def test_student_interface_does_not_surface_internal_review_state():
    app=(ROOT/'app.py').read_text(encoding='utf8')
    assert "with st.expander('内容与使用说明')" not in app
    assert '尚待补齐和学科审核' not in app
    assert '（当前显示的是已有课程资料' not in app
    assert "st.write('**各演示学生的学习情况**')" not in app

def test_ai_never_receives_the_card_review_metadata():
    card={'id':'BIO-998','theme':'遗传与进化','title':'孟德尔分离定律','summary':'等位基因随配子形成而分离',
         'misconception':'表型相同未必基因型相同','guide_question':'为什么要测交？',
         'review_status':'待教师审核','source_title':'后台来源标签'}
    value=format_context([card])
    assert '待教师审核' not in value and '后台来源标签' not in value
    msg=make_course_messages('怎么理解分离定律？',[card])
    serialized=' '.join(x['content'] for x in msg)
    assert '待教师审核' not in serialized and '后台来源标签' not in serialized


def test_course_content_connected_across_all_five_books():
    from course_catalog import load_plan
    from section_lessons import SECTION_CORE
    from junior_theme_lessons import THEME_INTRO
    from curriculum import THEMES
    plan=load_plan()
    expected={x['section_id'] for x in plan['sections']}
    assert expected==set(SECTION_CORE)
    assert len(expected)==82
    assert len(THEME_INTRO)==len(THEMES)==7
    assert sum(len(SECTION_CORE[x])>70 for x in SECTION_CORE)==82
    assert all(len(THEME_INTRO[t])>100 for t in THEMES)
    app=(ROOT/'app.py').read_text(encoding='utf8')
    assert 'get_section_core(sid)' in app
    assert 'st.write(THEME_INTRO[theme])' in app
