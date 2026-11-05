from pathlib import Path
import shutil, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.import_lessons import import_csv
from curriculum import load_cards

def test_import_template(tmp_path):
    sample=Path(__file__).resolve().parents[1]
    (tmp_path/'knowledge').mkdir()
    shutil.copy2(sample/'knowledge'/'curriculum_cards.json',tmp_path/'knowledge'/'curriculum_cards.json')
    csv_file=sample/'knowledge'/'custom_notes_template.csv'
    assert import_csv(csv_file,root=tmp_path)==1
    assert any(x['title']=='观察洋葱表皮细胞' for x in load_cards(tmp_path))
    assert import_csv(csv_file,root=tmp_path)==0
