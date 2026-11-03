"""Evidence-based lesson outline and editable PowerPoint generation for demo class.

Offline plans are deterministic editorial templates grounded in real demo activity.
Online AI rewording is optional and never silently invoked or called a verified report.
"""
from io import BytesIO

HPS_CASES=[
    ('孟德尔','孟德尔的豌豆杂交：观察F₂性状分离→提出遗传因子假说→设计测交→判断证据强度。'),
    ('测交','让学生从待测基因型出发预测测交结果，再讨论为什么小样本不能完全证明假说。'),
    ('光合','比较经典光合作用实验中的变量与证据，设计只改变光照的实验，识别温度混杂。'),
    ('细胞','重现细胞学说的发展：观察证据如何支持共同结构，讨论病毒例外和理论边界。'),
    ('DNA','利用X射线衍射与碱基配对证据拼接DNA双链模型，讨论科学合作。'),
    ('激素','分析促胰液素研究中如何区分神经途径与体液调节的不同解释。'),
    ('PCR','围绕DNA扩增设置阴性、阳性对照，讨论污染与阴性结果解释的局限。'),
    ('生态','分析种群变化案例，先预测再结合采样数据修改模型，讨论生态保护决策。'),
]

def hps_prompt(topic):
    for key,idea in HPS_CASES:
        if key in topic:return idea
    return '让学生提出一个可检验的问题，列出可比较的证据，再区分观察、推论和结论。'


def make_plan(report, topic_override=''):
    focus=report['focus']
    primary=(topic_override.strip()[:100] if topic_override.strip() else
             focus[0]['topic'] if focus else '孟德尔分离定律（演示样例课程）')
    related=next((r for r in focus if r['topic']==primary),None)
    questions=(related['questions'] if related else 0)
    wrong=(related['wrong'] if related else 0)
    attempts=(related['attempts'] if related else 0)
    notes=(f'此知识点有{questions}次学生提问、{attempts}次答题，其中{wrong}次答错。'
           if related else '当前该知识点暂无演示班级记录；以下内容是通用的备课框架。')
    cases=hps_prompt(primary)
    sections=[
      {'title':'学情与本课问题','bullets':[
          f'主题：{primary}',
          f'演示班级活动：{report["participants"]}名身份、{report["questions"]}次提问、{report["attempts"]}次答题（均为演示）',
          notes,
          '教师核对：题目是否具有代表性，是否需要调整课堂重点。',
      ]},
      {'title':'学习目标','bullets':[
          f'能用自己的语言解释“{primary}”的关键知识。',
          '能指出至少一个常见误区，并用证据修正自己的表述。',
          '能完成相关练习，解释选择依据而非只报选项。',
      ]},
      {'title':'课前诊断与导入','bullets':[
          f'导入问题：关于“{primary}”，你认为最容易混淆的地方是什么？',
          '请学生先独立表达或填写预测，教师不立即公布答案。',
          '根据演示学情中的典型错误组织匿名讨论。',
      ]},
      {'title':'核心知识讲解','bullets':[
          f'梳理“{primary}”的概念、机制和适用条件。',
          '对照学生的原始解释，讨论哪些是事实、哪些是推断。',
          '用一个反例或对照情境说明结论的边界。',
      ]},
      {'title':'跟随科学家探究（HPS）','bullets':[
          cases,
          '学生先提出假设、选择证据，再说明什么结果会反驳自己的想法。',
          '区分历史事实、教学情境重建和示例数据。',
      ]},
      {'title':'随堂练习与针对性反馈','bullets':[
          f'围绕“{primary}”安排基础题和HPS证据推理题各1道。',
          '客观题展示答案依据；对错因分类，不以一次答对断定已掌握。',
          '对薄弱点推荐不同题目进行复测。',
      ]},
      {'title':'课堂小结与下一轮反馈','bullets':[
          '让学生说出：我原先怎么想、证据是什么、我改变了什么判断。',
          '课后继续开放提问与错题回顾，下一次授课前重新汇总。',
          '本提纲为演示数据驱动的备课初稿，须由教师审核后使用。',
      ]},
    ]
    return {'topic':primary,'source_report':report,
            'sections':sections,
            'status':'规则辅助生成的可编辑备课初稿',
            'disclaimer':'全部学情数字来自预设身份的演示操作；未经过真实课堂验证。'}


def plan_markdown(plan):
    lines=[f'# {plan["topic"]} · 教师备课初稿','',f'> {plan["status"]}；{plan["disclaimer"]}','']
    for i,sec in enumerate(plan['sections'],1):
        lines.append(f'## {i}. {sec["title"]}')
        lines +=['- '+x for x in sec['bullets']]
        lines.append('')
    return '\n'.join(lines)


def ai_rewrite_messages(plan):
    """No raw student messages, student IDs, or names are sent to the AI."""
    source=plan['source_report']
    stats={'participants':source['participants'],'questions':source['questions'],
           'attempts':source['attempts'], 'focus':source['focus'][:3]}
    return [
        {'role':'system','content':
         '你是中学生物学教师的辅助备课助手。仅基于提供的匿名演示汇总数据给出一份清晰的40分钟课堂教学建议。'
         '含教学目标、知识讲解、HPS科学史证据推理活动、课堂练习、误区补救、课后复测。'
         '不要杜撰学生人数、分数、教材页码、历史原话或已开展的课堂实验。'
         '输入数据来自4个虚构演示身份，必须明确写为“演示数据”；教师需要最终审核。'},
        {'role':'user','content':f'课程主题：{plan["topic"]}\n匿名演示数据：{stats}\n当前备课框架：\n{plan_markdown(plan)[:4000]}'}
    ]


def pptx_bytes(plan, edited_sections=None):
    """Create editable 16:9 slides via python-pptx, optionally use teacher-edited outlines."""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    prs=Presentation()
    prs.slide_width=Inches(13.333)
    prs.slide_height=Inches(7.5)
    green=RGBColor(26,90,68)
    ink=RGBColor(34,55,48)
    grey=RGBColor(100,116,110)
    paper=RGBColor(248,251,248)
    def text_box(slide,x,y,w,h,text,font=20,bold=False,color=ink):
        sh=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
        tf=sh.text_frame
        tf.word_wrap=True
        for j,line in enumerate(str(text).split('\n')):
            p=tf.paragraphs[0] if j==0 else tf.add_paragraph()
            p.text=line;p.space_after=Pt(9)
            for r in p.runs:
                r.font.name='Microsoft YaHei';r.font.size=Pt(font);r.font.bold=bold;r.font.color.rgb=color
        return sh
    for i,sec in enumerate(plan['sections'],1):
        slide=prs.slides.add_slide(prs.slide_layouts[6])
        bg=slide.background.fill;bg.solid();bg.fore_color.rgb=paper
        shape=slide.shapes.add_shape(1, Inches(.56), Inches(.58), Inches(.12), Inches(.65))
        shape.fill.solid();shape.fill.fore_color.rgb=green;shape.line.fill.background()
        text_box(slide,.90,.52,11.6,.85,sec['title'],font=31,bold=True,color=green)
        subtitle=f'{plan["topic"]}  ·  教师备课初稿'
        text_box(slide,.95,1.36,11.7,.5,subtitle,font=15,color=grey)
        if edited_sections and len(edited_sections)==len(plan['sections']):
            content=edited_sections[i-1]
            if isinstance(content,(list,tuple)):content='\n'.join(map(str,content))
            content=content.strip() or '\n'.join(sec['bullets'])
            lines=[x.strip().lstrip('•-· ') for x in content.splitlines() if x.strip()][:6]
        else:lines=sec['bullets'][:6]
        for n,s in enumerate(lines):
            yy=2.02+n*.70
            text_box(slide,.98,yy,.3,.4,'●',font=13,color=green)
            text_box(slide,1.33,yy-.08,11.15,.66,s,font=19,color=ink)
        text_box(slide,.95,7.06,11.8,.27,
             f'BioHPS · 仅供演示与教师审核 · 非真实课堂学情   |   {i}/7',font=10,color=grey)
    out=BytesIO();prs.save(out);return out.getvalue()


def ai_report_messages(report):
    """Summarize aggregate demo issues without shipping raw questions to provider."""
    return [
        {'role':'system','content':
         '你是初高中生物学课堂分析助手，输入只是匿名的4个虚构演示学生身份的汇总记录。'
         '据实归纳最突出的三个疑问类别、可能的学习困难、可验证的课堂活动和下一节课优先级。'
         '不得虚构真实学生、考试成绩、诊断准确率或已发生的课堂活动。'
         '明确这些是演示数据；建议应便于教师审核。'},
        {'role':'user','content':f"演示班级汇总：参与身份 {report['participants']}；提问 {report['questions']}；"
         f"答题 {report['attempts']}；答错 {report['wrong']}。"
         f"知识点统计：{report['focus'][:8]}。匿名错因统计：{report['error_tags']}。"}
    ]
