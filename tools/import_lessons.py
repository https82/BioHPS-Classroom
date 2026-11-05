"""Append teacher-reviewed curriculum notes from a UTF-8 CSV.

Usage: python tools/import_lessons.py knowledge/custom_notes_template.csv
This is local-only and performs no model requests.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from curriculum import THEMES, load_cards

REQUIRED=['theme','title','summary','keywords','misconception','guide_question','source_title']


def import_csv(path,root=ROOT):
    path=Path(path)
    if not path.exists():raise ValueError('未找到课程CSV文件')
    cards=load_cards(root)
    existing={(x['theme'],x['title']) for x in cards}
    new=[]
    with path.open(encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle)
        if not reader.fieldnames or any(c not in reader.fieldnames for c in REQUIRED):
            raise ValueError('CSV表头不完整：'+','.join(REQUIRED))
        for n,row in enumerate(reader,2):
            if not any((v or '').strip() for v in row.values()):continue
            data={k:(row.get(k) or '').strip() for k in REQUIRED}
            if data['theme'] not in THEMES:
                raise ValueError(f'第{n}行主题错误：{data["theme"]}')
            if not (2<=len(data['title'])<=70 and 25<=len(data['summary'])<=2500):
                raise ValueError(f'第{n}行标题或摘要长度不符合要求')
            pair=(data['theme'],data['title'])
            if pair in existing:
                continue
            existing.add(pair)
            new.append({**data,'id':f'CUSTOM-{len(cards)+len(new)+1:04d}',
                        'keywords':[x.strip() for x in data['keywords'].split('|') if x.strip()],
                        'grade':'初中','curriculum_reference':'https://www.moe.gov.cn/srcsite/A26/s8001/202204/W020220420582359998122.pdf'})
    target=Path(root)/'knowledge'/'custom_notes.jsonl'
    with target.open('a',encoding='utf-8') as handle:
        for note in new:
            handle.write(json.dumps(note,ensure_ascii=False)+'\n')
    return len(new)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('csv_path',help='UTF-8 编码的课程知识卡CSV路径')
    args=parser.parse_args()
    try:
        count=import_csv(args.csv_path)
        print(f'已导入 {count} 张课程知识卡；原卡片未被覆盖。请重新启动Streamlit并对内容进行人工审核。')
    except (ValueError,OSError,csv.Error) as error:
        print('导入失败：'+str(error))
        raise SystemExit(1)
