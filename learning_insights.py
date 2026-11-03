"""Convert internal study events into readable evidence for the demo teacher."""
from datetime import datetime, timedelta, timezone
from hps_models import MEIOSIS_STAGES

STAGES={x['id']:x['title'] for x in MEIOSIS_STAGES}
EVENT_TITLES={
 'pollination':'选择豌豆亲本与人工授粉', 'prediction':'提出遗传因子假说并预测',
 'f2_trial':'观察F₂后代并统计比例', 'testcross':'设计测交并验证预测',
 'conclusion':'分析实验数据形成结论', 'meiosis_step':'判断减数分裂阶段',
}


def human_issue(name):
    """Keep data keys internal; show meaningful biology concepts to the teacher."""
    if name.startswith('减数分裂：'):
        return '减数分裂：'+STAGES.get(name.partition('：')[2],'染色体变化与计数')
    return name


def friendly_time(value):
    try:
        dt=datetime.fromisoformat(value)
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone(timedelta(hours=8))).strftime('%m月%d日 %H:%M')
    except (ValueError,TypeError):return ''


def describe_event(record):
    d=record['data']; typ=record['event_type']; label=EVENT_TITLES.get(typ,'科学探究')
    if typ=='pollination':
        good=bool(d.get('correct'))
        return label,('操作顺序正确' if good else '亲本选择或授粉顺序需要调整'),good
    if typ=='prediction':
        good=bool(d.get('sound'))
        return label, ('预测合理' if good else '显隐性或F₂比例预测需要复习'), good
    if typ=='f2_trial':
        return label, f'观察{d.get("n",0)}株后代：高茎{d.get("high",0)}，矮茎{d.get("short",0)}；注意抽样波动', True
    if typ=='testcross':
        good=bool(d.get('prediction_correct'))
        return label, ('测交条件及比例预测合理' if good else '测交比例预测需要复习'),good
    if typ=='conclusion':
        good=bool(d.get('sound'))
        return label, ('能合理解释有限样本的随机波动' if good else '需要区分理论比例与抽样波动'),good
    if typ=='meiosis_step':
        phase=STAGES.get(d.get('stage'),'当前阶段')
        good=bool(d.get('correct'))
        return label,phase+('：判断正确' if good else '：染色体分离或计数判断需要复习'),good
    return label,'已完成探究操作',True


def teacher_story_summary(records):
    if not records:return []
    total={}
    for r in records:
        row=total.setdefault(r['title'],{'title':r['title'],'attempts':0,'wrong':0})
        row['attempts']+=1
        row['wrong']+=not bool(r['correct'])
    return sorted(total.values(),key=lambda x:(-x['wrong'],-x['attempts']))
