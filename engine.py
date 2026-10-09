import json
import re

CASES = {
 '鹅颈瓶实验': {'topic':'巴斯德鹅颈瓶实验','history':'巴斯德的鹅颈瓶与外界空气相通。煮沸后的肉汤若未受到携带微生物的尘埃污染，通常保持澄清；弯曲处可截留尘埃。倾斜瓶身让肉汤接触瓶颈积尘后可能出现微生物生长。','misconception':'空气不能进入瓶内','question':'你预测什么现象？为什么？'},
 '光合作用': {'topic':'光照对光合作用的影响','history':'改变光照条件时，需尽量保持植物材料、温度、二氧化碳和检测时长一致。气泡数仅可在一定实验条件下作间接指标，不能等同准确光合速率。','misconception':'一次同时改变多个条件','question':'改变光照会如何影响你选择的观测指标？'},
 '种子萌发': {'topic':'种子萌发条件探究','history':'水分、氧气和适宜温度都可能影响萌发。比较水分时，应控制种子批次、数量、温度、观察时间等。','misconception':'将多个因素同时改变','question':'若只探究水分，你预计怎样的结果？'}
}
STAGES=['提出假设','识别变量','设计对照','解释证据']
RUBRIC={'假设提出':25,'变量控制':25,'对照设置':25,'证据解释':25}

def scaffold(stage, case):
    questions=[f'关于{CASES[case]["topic"]}，请先说出一条可以检验的假设，以及你预测的现象。',
        '你要改变哪个因素，测量什么结果？还有哪些条件需要保持一致？',
        '请说出实验组与对照组怎么设置，并说明怎样排除其他解释。',
        '根据可能出现的两种结果，各能得出什么结论？还存在哪些局限？']
    return questions[min(max(stage,0),3)]

def make_messages(history,case,stage,mastery):
    background=CASES[case]['history']
    system=f'''你是面向初中生的探知·BioHPS科学探究导师。采用HPS(科学史、科学哲学、科学社会学)视角；不应将一般生物事实都称为HPS创新。
主题：{CASES[case]['topic']}。经过人工整理但尚未外部核验的参考资料：{background}
当前探究阶段：{STAGES[stage]}。之前已暂时掌握的维度：{', '.join(STAGES[i] for i in range(4) if mastery[i]) or '无'}。
教学原则：严禁把错误认识夸奖为正确；区分肯定学生参与和肯定事实准确性。先识别学生最新表述中真正的理解和误解。原则上每次仅提出一个关键问题，不先直接公布全部答案；连续卡住可提供一小步支架。学生问原因时可以给局部提示，但尽量保留进一步思考空间。不要编造引文、实验数据或研究结论，不应宣称已有教学效果验证。科学概念务必准确。答复为中文，60-180字。
请仅输出一个可被json.loads读取的JSON对象，不要Markdown围栏，严格如下：
{{"feedback":"对学生本轮回答的简短、科学准确的反馈并且只提出一个核心问题","diagnosis":"简洁的当前误区或理解情况，供研发者查看","evidence":"引用学生最新输入中的短语作为判断依据；不可虚构","achieved":false,"confidence":"low"}}
其中 achieved 仅表示学生在**当前阶段**已经充分展示出该阶段要求：阶段0=可检验假设及合理预测；阶段1=正确识别自变量、因变量和关键控制因素；阶段2=可执行的实验组、对照组且主要只变一项；阶段3=据观测推断结论并指出至少一个局限。仅学生问问题、尚有关键错误、或证据不足时必须false。confidence仅可为low/medium/high。不要使用整数成绩。'''
    return [{'role':'system','content':system}]+[{'role':r,'content':t} for r,t in history[-12:]]

def parse_feedback(text):
    s=(text or '').strip()
    if s.startswith('```'):
        s=re.sub(r'^```(?:json)?\s*|\s*```$', '', s,flags=re.I).strip()
    if not s.startswith('{'):
        start=s.find('{'); end=s.rfind('}')
        if start>=0 and end>start:s=s[start:end+1]
    try: d=json.loads(s)
    except (ValueError,TypeError): return None
    if not isinstance(d,dict) or not isinstance(d.get('feedback'),str) or not d['feedback'].strip():return None
    if type(d.get('achieved')) is not bool:return None
    conf=d.get('confidence','low')
    if conf not in ('low','medium','high'): conf='low'
    return {'feedback':d['feedback'].strip()[:1500], 'diagnosis':str(d.get('diagnosis',''))[:300],
        'evidence':str(d.get('evidence',''))[:300], 'achieved':d['achieved'],'confidence':conf}

def validate_advance(result,student_text):
    # Guardrail: model must cite exact evidence from the newest student message, with high confidence.
    evidence=result.get('evidence','').strip()
    return bool(result.get('achieved') and result.get('confidence')=='high' and
                len(evidence)>=3 and evidence in student_text)

# V2.2: Keep scientific concept understanding separate from inquiry skills.
CONCEPTS = {
    '鹅颈瓶实验': ['空气能够进入鹅颈瓶', '瓶颈弯曲处可截留携带微生物的颗粒', '肉汤接触积尘后可能出现微生物生长'],
    '光合作用': ['光照可影响光合作用', '一次重点比较一个实验因素', '观测指标有适用条件和局限'],
    '种子萌发': ['种子萌发需要适当环境条件', '研究一个因素时需控制其他条件', '实验结论依赖可靠观测'],
}
STATUSES = ('尚未体现', '存在误解', '初步理解', '表现出正确理解')

def make_dual_messages(history, case, stage, mastery, concept_state):
    messages = make_messages(history, case, stage, mastery)
    system = messages[0]['content']
    system = system[:system.find('请仅输出一个可被json.loads读取的JSON对象')] if '请仅输出一个可被json.loads读取的JSON对象' in system else system
    system += f'''\n科学概念与探究能力必须分开评价。知识点：{json.dumps(CONCEPTS[case], ensure_ascii=False)}。
已有概念记录（暂定，可能需修正）：{json.dumps(concept_state, ensure_ascii=False)}。
根据学生最新消息，最多更新与其实际回答相关的概念点；学生纠正错误时要允许将“存在误解”改为“表现出正确理解”。
概念更新使用 concepts 数组，每项形式为：{{"concept":"必须完全等于上方的某个知识点","status":"尚未体现/存在误解/初步理解/表现出正确理解","evidence":"逐字引用最新一条学生消息中的短句"}}。
绝不根据模型自己说的话推断学生已掌握；未提及则不更新。阶段达标评定与概念理解分开，阶段{stage}={STAGES[stage]}，严格遵循该阶段评价标准。\n
仅输出JSON对象：{{"feedback":"面向学生的科学准确反馈，通常一个核心问题，避免一次公布全部答案","diagnosis":"本轮探究能力的诊断","evidence":"从最新学生消息逐字摘录的证据","achieved":false,"confidence":"low","concepts":[]}}。
confidence仅为low、medium、high。所有引文须精确来自最新学生消息；不得编造来源、测试数据和评分。'''
    messages[0]['content'] = system
    return messages

def parse_dual_feedback(raw):
    base = parse_feedback(raw)
    if base is None:
        return None
    try:
        s = (raw or '').strip()
        if s.startswith('```'):
            s = re.sub(r'^```(?:json)?\s*|\s*```$', '', s, flags=re.I).strip()
        obj = json.loads(s if s.startswith('{') and s.endswith('}') else s[s.find('{'):s.rfind('}')+1])
    except (ValueError, TypeError):
        obj = {}
    base['concepts'] = obj.get('concepts', []) if isinstance(obj.get('concepts', []), list) else []
    return base

def validated_concept_updates(result, case, student_text):
    """Accept only allowed labels, exact case concepts and verbatim student evidence."""
    out = []
    for item in result.get('concepts', []):
        if not isinstance(item, dict):
            continue
        concept, status, evidence = item.get('concept'), item.get('status'), item.get('evidence')
        if (concept in CONCEPTS[case] and status in STATUSES and isinstance(evidence, str)
                and len(evidence.strip()) >= 3 and evidence.strip() in student_text):
            out.append({'concept':concept,'status':status,'evidence':evidence.strip()[:200]})
    return out

def update_concept_state(old_state, updates):
    state = dict(old_state)
    for item in updates:
        state[item['concept']] = {'status':item['status'],'evidence':item['evidence']}
    return state


def parse_model_output(raw):
    """Return (student_facing_text, structured_result_or_None, format_tag).

    Never expose machine-readable JSON verbatim in the student chat.
    """
    text=(raw or '').strip()
    structured=parse_dual_feedback(text)
    if structured:
        return structured['feedback'], structured, 'validated_json'
    # Many models omit achieved/confidence/concepts but still supply a useful feedback field.
    cleaned=re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.I).strip()
    candidates=[cleaned]
    start=cleaned.find('{'); end=cleaned.rfind('}')
    if start>=0 and end>start:candidates.append(cleaned[start:end+1])
    for candidate in candidates:
        try:obj=json.loads(candidate)
        except (ValueError,TypeError):continue
        if isinstance(obj,dict):
            feedback=obj.get('feedback')
            if isinstance(feedback,str) and feedback.strip():
                return feedback.strip()[:1500],None,'partial_json_feedback_only'
            return '模型仅返回了结构化诊断，未提供面向学生的反馈，请重新提问。',None,'json_without_feedback'
    # For an obviously JSON-shaped broken string, avoid leaking technical data.
    if cleaned.startswith('{') or cleaned.startswith('```json'):
        match=re.search(r'"feedback"\s*:\s*"((?:[^"\\]|\\.)*)"',cleaned,re.S)
        if match:
            try: feedback=json.loads('"'+match.group(1)+'"')
            except ValueError:feedback=match.group(1)
            if feedback.strip():return feedback.strip()[:1500],None,'incomplete_json_feedback_only'
        return '模型返回了不完整的教学反馈。请重试本轮问题。',None,'malformed_json'
    return (text[:4000] if text else '模型没有返回文本，请重试。'),None,'plain_text'

# V3.1: Conservative stage-gates. A model suggestion alone NEVER completes a stage.
# These checks are transparent educational heuristics, not validated assessment tools.
STAGE_CRITERIA = [
    '提出与实验事实相符、能够通过观察检验的假设，并预测可观察的现象',
    '识别自变量、因变量及至少一项需要保持一致的条件',
    '设计实验组和对照组，并说明两组应尽量只改变研究因素',
    '结合两组观察结果解释证据，并指出至少一项结论局限',
]
CASE_OBJECTIVES = {
    '鹅颈瓶实验': {
        'question':'鹅颈瓶能让空气进入，为什么煮沸肉汤通常仍能保持澄清？',
        'outcome':'比较直立与倾斜鹅颈瓶的观察结果，检验尘埃污染这一解释',
        'materials':'鹅颈瓶结构图、实验现象记录卡（数字讨论，不要求实际煮沸）',
        'samples':[
            ('识别典型误解','我认为鹅颈瓶里肉汤没有出现微生物，是因为空气完全无法进入瓶内。'),
            ('修正科学概念','我明白了，鹅颈瓶允许空气进入，但弯曲处可以截留带有微生物的尘埃。'),
            ('提出可检验预测','如果倾斜鹅颈瓶，让肉汤接触瓶颈积尘，那么肉汤可能出现微生物生长、变得浑浊；保持直立的瓶中肉汤则可能保持澄清。'),
        ],
    },
    '光合作用': {
        'question':'改变光照条件时，怎样比较植物光合作用的可观察差异？',
        'outcome':'提出光照影响可观察指标的预测，并控制温度和材料差异',
        'materials':'水生植物观察资料、光照条件记录、时间与气泡计数记录卡',
        'samples':[
            ('识别变量误解','我想同时提高光照和温度，看看植物产生的气泡是不是变多。'),
            ('修正科学概念','应该主要改变光照强度，同时保持温度、植物材料和观察时长一致。'),
            ('提出可检验预测','如果在其他条件相同的情况下提高光照强度，适当范围内相同时长的氧气气泡数可能增加。'),
        ],
    },
    '种子萌发': {
        'question':'水分对种子萌发有什么影响？怎样排除温度等因素的干扰？',
        'outcome':'用可比较的水分条件检验假设，并记录萌发数量',
        'materials':'同批次种子、观察记录表、水分条件设置卡',
        'samples':[
            ('识别变量误解','我准备一组不浇水还放到冰箱里，另一组浇水并放在温暖的地方。'),
            ('修正科学概念','只改变供水情况，保持种子来源、温度、观察时间等条件一致。'),
            ('提出可检验预测','如果在相同温度、种子批次和观察时间下，一组供给适量水，另一组不给水，那么适量供水组预计萌发种子更多。'),
        ],
    },
}


def _contains_any(text, words):
    return any(w in text for w in words)


def _denied_misconception(text, match):
    prefix = text[max(0, match.start()-12):match.start()]
    return bool(re.search(r'(?:不是|并非|不对|错误|纠正|误认为|原先认为|以前认为|曾认为).{0,8}$', prefix))


def misconception_blockers(case, text):
    """Block clear, affirmative misconceptions; quoted/corrected claims are excluded."""
    t = (text or '').replace(' ', '')
    out = []
    if case == '鹅颈瓶实验':
        patterns = [r'空气.{0,6}(?:完全)?(?:无法|不能|进不去|进不了|不可能).{0,3}进入',
                    r'空气(?:完全)?(?:无法|不能|进不去|进不了)进入',
                    r'(?:瓶口|鹅颈瓶)(?:是|完全)?(?:密封|封闭)(?:的)?']
        for p in patterns:
            for m in re.finditer(p, t):
                if not _denied_misconception(t, m):
                    out.append('存在“空气不能进入/瓶口密封”的关键认识错误')
                    break
            if out:break
    elif case == '光合作用':
        if _contains_any(t, ['同时改变光照和温度', '光照和温度都改变', '同时提高光照和温度']):
            out.append('同时改变光照和温度，不能归因于单一因素')
    elif case == '种子萌发':
        if ('不浇水' in t or '不给水' in t) and ('冰箱' in t or '低温' in t) and _contains_any(t, ['另一组','对照组','比较','一组']):
            out.append('水分和温度同时改变，无法独立检验水分效应')
    return list(dict.fromkeys(out))


def stage_gate(stage, case, student_text):
    """Return (criteria_met, actionable_reasons), independent of the LLM's claimed score.

    The gate is deliberately conservative; it can reject a valid free-form student answer.
    Passing it does NOT mean educational correctness has been proven.
    """
    t = (student_text or '').strip().replace(' ', '')
    issues = []
    if len(t) < 18:
        return False, ['回答过短，尚不足以支持阶段评价']
    issues.extend(misconception_blockers(case, t))
    if stage == 0:
        conditions = ['如果','假如','若','当','在其他条件','与','比较','预计','预测','倾斜','提高','增加','改变']
        outcomes = {'鹅颈瓶实验':['肉汤','浑浊','澄清','微生物','生长','污染'],
                    '光合作用':['气泡','氧气','光合作用','速率'],
                    '种子萌发':['萌发','发芽','种子']}[case]
        effects = ['会','可能','预计','预测','增加','减少','更多','更少','出现','保持','变得','提高','降低','产生','不出现']
        if not _contains_any(t, conditions):issues.append('尚未给出明确的条件或可检验假设')
        if not (_contains_any(t, outcomes) and _contains_any(t, effects)):
            issues.append('尚未给出可观察的现象预测')
        if case == '鹅颈瓶实验' and not _contains_any(t, ['倾斜','积尘','尘埃','污染','肉汤接触','保持直立']):
            issues.append('需要将假设与鹅颈瓶的可比较实验条件联系起来')
    elif stage == 1:
        if not _contains_any(t, ['自变量','改变','研究因素','比较因素']):issues.append('没有明确研究时主动改变的因素')
        if not _contains_any(t, ['因变量','测量','记录','观察指标','萌发数量','气泡数','是否浑浊','浑浊程度','萌发率']):issues.append('没有明确记录或测量的结果')
        if not _contains_any(t, ['控制','一致','相同','保持','不变','固定']):issues.append('没有说明需要保持一致的条件')
    elif stage == 2:
        if not _contains_any(t, ['对照组','对照','实验组','一组','两组','另一组']):issues.append('没有描述可比较的实验组与对照组')
        if not _contains_any(t, ['只改变','仅改变','只有','其余','相同','一致','保持','不变']):issues.append('没有说明如何避免无关变量干扰')
        if not _contains_any(t, ['倾斜','直立','光照','水分','浇水','温度','种子','肉汤']):issues.append('缺少实验条件的具体设置')
    elif stage == 3:
        if not _contains_any(t, ['结果','观察','显示','浑浊','澄清','萌发','气泡','数据','比较']):issues.append('没有引用可观察结果或比较证据')
        if not _contains_any(t, ['因此','说明','支持','推断','意味着','可以认为']):issues.append('没有依据结果提出解释')
        if not _contains_any(t, ['但是','不过','局限','不能完全','还需','可能还有','误差','重复','不足','无法排除']):issues.append('没有指出至少一项结论局限')
    else:
        issues.append('未知探究阶段')
    return (not issues),issues


def assess_transition(result, case, stage, student_text):
    """Transparent result; both high-confidence anchored model feedback AND rules needed."""
    ok, issues = stage_gate(stage, case, student_text)
    if result is None:
        return {'accepted':False, 'reasons':['未获得完整结构化模型评价']+issues,
                'model_claimed':False,'rule_passed':ok}
    anchored = validate_advance(result, student_text)
    if not anchored:
        issues = ['模型未提供高置信度且可核对的学生原话证据'] + issues
    return {'accepted':bool(anchored and ok),'reasons':issues,'model_claimed':bool(result.get('achieved')),
            'rule_passed':ok}


def validate_concepts_strict(result, case, student_text):
    """Reject self-contradictory optimistic labels for clear misconceptions."""
    updates = validated_concept_updates(result, case, student_text)
    blockers = misconception_blockers(case, student_text)
    if blockers:
        return [u for u in updates if u['status'] not in ('初步理解','表现出正确理解')]
    return updates


def make_competition_messages(history,case,stage,mastery,concept_state):
    messages = make_dual_messages(history,case,stage,mastery,concept_state)
    messages[0]['content'] += f'''\n比赛版阶段门槛（人工拟定、尚未教学验证）：{STAGE_CRITERIA[stage]}。
若学生的关键假设与科学事实冲突，即使表达了某种预测，也不要判定当前阶段完成。
若学生仅修正概念但未提出可检验预测，应将概念状态更新，不自动推进探究阶段。
feedback用简洁、自然的中文表达：先指出学生回答中具体的一个问题，再只提出一个最重要的追问，通常60—140字。不要把内部JSON/评分术语写在feedback里。完成情况及每条概念证据只能依据最新学生原话，不能引用你以前生成的回答。避免夸赞错误结论；不要虚构教学效果。'''
    return messages
