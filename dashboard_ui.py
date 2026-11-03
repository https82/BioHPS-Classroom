"""Student/teacher dashboard presentation helpers for the BioHPS demo.

No fictional usage stats: all values derive from recorded demo actions.
The reusable render helpers are HTML escaped and have no external assets.
"""
from collections import Counter
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import calendar
import html

TZ = ZoneInfo('Asia/Shanghai')


def local_today(now=None):
    return (now or datetime.now(TZ)).astimezone(TZ).date()


def date_of(value):
    try:
        d = datetime.fromisoformat(str(value).replace('Z','+00:00'))
        if d.tzinfo is None:
            d = d.replace(tzinfo=TZ)
        return d.astimezone(TZ).date()
    except (ValueError, TypeError):
        return None


def weekly_activity(questions, attempts, labs=(), hps=(), stories=(), today=None):
    today = today or local_today()
    values = {today - timedelta(days=i): 0 for i in range(7)}
    for group in (questions, attempts, labs, hps, stories):
        for row in group:
            day = date_of(row.get('created_at'))
            if day in values: values[day] += 1
    return [{'date': day, 'label': f'{day.month}/{day.day}', 'count': values[day]}
            for day in sorted(values)]


def student_numbers(summary):
    answered=int(summary.get('answered',0))
    correct=int(summary.get('correct',0))
    pending=sum(summary.get('needs_review',{}).values())
    return {'answered':answered,'correct':correct,'wrong':answered-correct,
            'accuracy': round(100*correct/answered) if answered else None,
            'questions':len(summary.get('questions',[])), 'review':pending}


def teacher_numbers(report):
    attempted=int(report.get('attempts',0))
    correct=int(report.get('correct',0))
    return {'participants':int(report.get('participants',0)),
            'questions':int(report.get('questions',0)),
            'attempts':attempted,'wrong':int(report.get('wrong',0)),
            'accuracy':round(100*correct/attempted) if attempted else None}


def esc(text):
    return html.escape(str(text), quote=True)


def metric_html(label, value, detail='', emblem='◉'):
    """Subtle semantic card palettes, never fake metric colors/values."""
    themes = {
        '本次学习时间': 'sky', '已完成练习': 'teal',
        '答题正确率': 'violet', '待复习知识点': 'amber',
        '参与学习': 'sky', '学生提问': 'violet',
        '练习完成': 'teal', '需要订正': 'rose',
    }
    theme = themes.get(label, 'sky')
    return (f'<div class="db-stat db-stat-{theme}"><div class="db-stat-icon">{esc(emblem)}</div>'
            f'<div class="db-stat-label">{esc(label)}</div>'
            f'<div class="db-stat-number">{esc(value)}</div>'
            f'<div class="db-stat-note">{esc(detail)}</div></div>')


def hero_html(kicker, heading, subline, teacher=False):
    extra=' db-hero-teacher' if teacher else ''
    return (f'<section class="db-hero{extra}"><div class="db-kicker">{esc(kicker)}</div>'
            f'<h1>{esc(heading)}</h1><p>{esc(subline)}</p>'
            '<span class="db-hero-watermark" aria-hidden="true">✦</span></section>')


def month_calendar(today=None):
    today=today or local_today()
    weekdays=('一','二','三','四','五','六','日')
    cal=calendar.Calendar(firstweekday=0).monthdayscalendar(today.year,today.month)
    cells=''.join(f'<span class="db-cal-weekday">{d}</span>' for d in weekdays)
    for week in cal:
        for n in week:
            if not n:cells+='<span class="db-cal-day db-cal-muted"></span>'
            else:
                current=' db-cal-current' if n==today.day else ''
                cells+=f'<span class="db-cal-day{current}">{n}</span>'
    return (f'<div class="db-panel db-calendar"><div class="db-panel-title">📅 今日日期</div>'
            f'<div class="db-calendar-month">{today.year}年{today.month}月 <span>星期{weekdays[today.weekday()]}</span></div>'
            f'<div class="db-calendar-grid">{cells}</div></div>')


def activity_html(rows):
    mx=max((r['count'] for r in rows),default=0)
    cols=[]
    for r in rows:
        # Keep real zero as an empty baseline instead of inventing a bar.
        ht=round(r['count'] / mx * 100) if mx else 0
        cols.append(f'<div class="db-activity-col"><span class="db-activity-value">{r["count"]}</span>'
                    f'<div class="db-activity-track"><div class="db-activity-fill" style="height:{ht}%"></div></div>'
                    f'<span class="db-activity-day">{esc(r["label"])}</span></div>')
    return ('<section class="db-panel db-panel-activity"><div class="db-panel-title">📈 最近七天的学习活动</div>'
            '<div class="db-panel-desc">根据真实的提问、练习和探究记录统计</div>'
            f'<div class="db-activity-chart">{"".join(cols)}</div></section>')


def accuracy_html(percentage, description='基于已完成的章节练习'):
    if percentage is None:
        percent=0
        text='—'
        label='完成练习后显示'
    else:
        percent=max(0,min(100,int(percentage)))
        text=f'{percent}%'
        label='答题正确率'
    return (f'<section class="db-panel db-panel-performance"><div class="db-panel-title">🎯 学习表现</div>'
            f'<div class="db-gauge" style="--progress:{percent}%"><div class="db-gauge-center">'
            f'<strong>{esc(text)}</strong><span>{esc(label)}</span></div></div>'
            f'<p class="db-gauge-note">{esc(description)}</p></section>')


def progress_line(label, done, total, subtitle=''):
    total=max(0,int(total));done=max(0,int(done))
    pct=round(100*done/total) if total else 0
    return (f'<div class="db-progress-line"><div class="db-progress-top">'
            f'<span>{esc(label)}</span><b>{done}/{total}</b></div>'
            f'<div class="db-progress-track"><div class="db-progress-fill" style="width:{pct}%"></div></div>'
            f'<div class="db-progress-hint">{esc(subtitle)}</div></div>')


def issue_html(items):
    """Grounded topic counts, never invented class performance data."""
    if not items:
        return '<div class="db-empty">学生完成练习后，这里会自动出现需要重点讲解的内容。</div>'
    selected=items[:5]
    mx=max(max(int(v) for _,v in selected),1)
    out=[]
    for topic,count in selected:
        width=round(100*int(count)/mx)
        out.append(f'<div class="db-issue"><div class="db-issue-head"><span>{esc(topic)}</span><b>{count}次</b></div>'
                   f'<div class="db-progress-track"><div class="db-progress-fill" style="width:{width}%"></div></div></div>')
    return ''.join(out)
