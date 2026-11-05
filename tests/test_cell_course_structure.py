import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_cell_theory_course_has_study_and_quiz_assets():
    code=ast.parse((ROOT/'cell_theory_course.py').read_text(encoding='utf8'))
    assigns={}
    for node in code.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in ('LESSON_STEPS','CHECKS'):
                    assigns[target.id]=ast.literal_eval(node.value)
    assert len(assigns['LESSON_STEPS'])==8
    assert len(assigns['CHECKS'])==6
    assert all(len(text)>160 for _,text in assigns['LESSON_STEPS'])
    assert all(len(set(x[1]))==4 and 0<=x[2]<4 for x in assigns['CHECKS'])
    app=(ROOT/'app.py').read_text(encoding='utf8')
    assert "render_cell_lesson(student)" in app
