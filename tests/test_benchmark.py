from tools.compare_models import load_cases, build_messages
from tools.summarize_review import summarize


def test_dataset_has_30_unique_ids_and_three_cases():
    cases=load_cases()
    assert len(cases)==30
    assert {v['case'] for v in cases}=={'鹅颈瓶实验','光合作用','种子萌发'}
    assert set(c['case_id'] for c in cases)=={f'B{i:02d}' for i in range(1,31)}


def test_pair_uses_same_input_and_distinct_prompts():
    test=load_cases()[0]
    a=build_messages(test,'普通教学基线')
    b=build_messages(test,'BioHPS')
    assert a[-1]['content']==b[-1]['content']==test['student_input']
    assert a[0]['content']!=b[0]['content']
    assert all(m['role'] in ('system','user','assistant') for m in a+b)


def test_dry_run_does_not_call_model(capsys):
    from tools.compare_models import main
    assert main(['--limit','3'])==0
    out=capsys.readouterr().out
    assert '预期API请求: 6' in out
    assert 'dry-run' in out


def test_unrated_results_cannot_generate_scores(tmp_path,capsys):
    import csv
    f=tmp_path/'unrated.csv'
    with f.open('w',encoding='utf-8-sig',newline='') as out:
        w=csv.writer(out);w.writerow(['case_id','system','status','科学准确性_0至2','错误识别_0至2','引导适切性_0至2','依据一致性_0至2'])
        w.writerow(['B01','BioHPS','成功','','','','']);w.writerow(['B01','普通教学基线','成功','','','',''])
    summarize(f)
    assert '暂无有效的已评配对' in capsys.readouterr().out


def test_mocked_live_run_writes_six_requests_without_real_api(tmp_path, monkeypatch):
    """Mock-only CI verification; no provider key, costs, or real measured scores."""
    import csv
    import service
    from tools import compare_models

    monkeypatch.setattr(compare_models,'RESULT_DIR',tmp_path)
    def fake_call(messages):
        return {'ok':True,'error':'','model':'fake-unit-test-model',
                'text':'请观察两个实验组的差异。','tokens':{'prompt_tokens':10,'completion_tokens':12}}
    monkeypatch.setattr(service,'call_ai',fake_call)
    assert compare_models.main(['--limit','3','--live','--pause','0'])==0
    raw=list(tmp_path.glob('raw_*.csv'))
    review=list(tmp_path.glob('教师待评_*.csv'))
    assert len(raw)==len(review)==1
    with raw[0].open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==6
    assert len({r['case_id'] for r in rows})==3
    assert {r['system'] for r in rows}=={'BioHPS','普通教学基线'}
    assert all(r['model']=='fake-unit-test-model' for r in rows)
    with review[0].open(encoding='utf-8-sig',newline='') as f:scored=list(csv.DictReader(f))
    assert all(not r['科学准确性_0至2'] for r in scored)
