"""A reproducible, low-budget paired probe runner for BioHPS vs same-model general tutor.

No automatic 'win' claims: expert raters must label exported responses separately.
Default invocation is a no-cost dry run. Explicit --live is needed for API calls.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import make_competition_messages, parse_model_output, assess_transition

BASELINE_SYSTEM = (
    '你是一名认真负责的初中生物辅导教师。'
    '请根据学生本轮输入，给出科学准确、对初中生易懂且有帮助的教学反馈。'
    '尽量使用引导性方式，每次最多追问一个关键问题。'
    '不要捏造实验证据、研究数据或教材出处。用中文回答。'
)
CASES_PATH=ROOT/'evaluation'/'bench_cases.csv'
RESULT_DIR=ROOT/'evaluation'/'results'
FIELDS=['run_id','utc_time','case_id','case','stage','category','expert_check_hint','student_input',
        'system','status','model','latency_s','prompt_tokens','completion_tokens',
        'response','format_tag','model_claimed_pass','rule_passed','stage_accepted','gate_reasons']
RATING_FIELDS=['run_id','case_id','case','category','student_input','system','status','response',
               '科学准确性_0至2','错误识别_0至2','引导适切性_0至2','依据一致性_0至2',
               '是否直接泄露完整答案_是或否','评阅者','评阅日期','评阅备注']


def load_cases(path=CASES_PATH):
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        cases=list(csv.DictReader(f))
    assert len(cases)==30 and len({x['case_id'] for x in cases})==30, '题目数量或编号异常'
    assert all(x['case'] in {'鹅颈瓶实验','光合作用','种子萌发'} and x['stage'] in {'0','1','2','3'} for x in cases)
    return cases


def build_messages(item, system):
    inp=item['student_input']
    if system=='普通教学基线':
        return [{'role':'system','content':BASELINE_SYSTEM},{'role':'user','content':inp}]
    stage=int(item['stage'])
    # Each question is a fresh independent probe. Prior stages are only stage context,
    # not fabricated conversation turns or claimed student mastery.
    return make_competition_messages([('user',inp)],item['case'],stage,[False]*4,{})


def write_rows(rows,path,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)


def main(args=None):
    p=argparse.ArgumentParser(description='同底层模型独立题目配对评测；默认不产生API费用。')
    p.add_argument('--live',action='store_true',help='实际发起API请求（可能计费）')
    p.add_argument('--limit',type=int,default=3,help='抽取前N题，默认3道（实际6次模型调用）')
    p.add_argument('--confirm-full',action='store_true',help='明确确认超过10题的调用成本')
    p.add_argument('--pause',type=float,default=1.0,help='请求间隔秒，默认1秒')
    parsed=p.parse_args(args)
    if not 1<=parsed.limit<=30:p.error('--limit 范围必须为1～30')
    if parsed.live and parsed.limit>10 and not parsed.confirm_full:
        p.error('为避免意外费用，超过10题需要添加 --confirm-full')
    all_cases=load_cases()
    # Small pilots cover all three experiments, rather than the first case only.
    groups={name:[x for x in all_cases if x['case']==name] for name in ('鹅颈瓶实验','光合作用','种子萌发')}
    interleaved=[groups[name][i] for i in range(10) for name in groups]
    selected=interleaved[:parsed.limit]
    print(f'选定题目: {len(selected)}，预期API请求: {len(selected)*2}，模型: 两组使用同一份BIOHPS_MODEL配置。')
    print('说明：输出未经过教师评分；程序不会自动宣称哪种系统更优。')
    if not parsed.live:
        for item in selected:print(f"  {item['case_id']} · {item['case']} · {item['category']}: {item['student_input']}")
        print('当前为 dry-run（未调用API、未产生模型费用）。若要运行，添加 --live。')
        return 0
    from service import call_ai
    RESULT_DIR.mkdir(exist_ok=True,parents=True)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    rows=[]
    for i,item in enumerate(selected):
        # Alternate the order per item to reduce a systematic first/second call advantage.
        names=['普通教学基线','BioHPS'] if i%2==0 else ['BioHPS','普通教学基线']
        for system in names:
            messages=build_messages(item,system)
            start=time.perf_counter()
            result=call_ai(messages)
            elapsed=round(time.perf_counter()-start,3)
            usage=result.get('tokens') if isinstance(result.get('tokens'),dict) else {}
            row={
                'run_id':run_id,'utc_time':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                **item,'system':system,'status':'成功' if result.get('ok') else '失败: '+result.get('error',''),
                'model':result.get('model') or '未获取','latency_s':elapsed,
                'prompt_tokens':usage.get('prompt_tokens',''),'completion_tokens':usage.get('completion_tokens',''),
                'response':'','format_tag':'','model_claimed_pass':'','rule_passed':'','stage_accepted':'','gate_reasons':'',
            }
            if result.get('ok'):
                if system=='BioHPS':
                    feedback,parsed_json,tag=parse_model_output(result.get('text',''))
                    decision=assess_transition(parsed_json,item['case'],int(item['stage']),item['student_input'])
                    row.update(response=feedback,format_tag=tag,model_claimed_pass=decision['model_claimed'],
                               rule_passed=decision['rule_passed'],stage_accepted=decision['accepted'],
                               gate_reasons='；'.join(decision['reasons']))
                else:
                    row['response']=result.get('text','')
            rows.append(row)
            print(f"{item['case_id']} {system}: {row['status']} ({elapsed:.2f}s)",flush=True)
            # Write checkpoints after every API request so interrupts don't lose previous calls.
            write_rows(rows,RESULT_DIR/f'raw_{run_id}.csv',FIELDS)
            if parsed.pause>0:time.sleep(parsed.pause)
    review=[{key:r.get(key,'') for key in RATING_FIELDS} for r in rows]
    review_path=RESULT_DIR/f'教师待评_{run_id}.csv'
    write_rows(review,review_path,RATING_FIELDS)
    print('原始记录：',RESULT_DIR/f'raw_{run_id}.csv')
    print('待评记录：',review_path)
    print('请将教师评分填入“教师待评”文件。任何空白评分都不应当作0或自动补分。')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
