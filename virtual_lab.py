"""Transparent qualitative teaching models for BioHPS interactive inquiry.

These are ORIGINAL pedagogical toy models, not empirical, mechanistic,
calibrated biological simulations or measurements from living material.
"""
from datetime import datetime, timezone

EXPERIMENTS={
 '光合作用': {
   'title':'光照、温度与光合表现',
   'objective':'在控制其他条件的前提下比较一个实验变量，发现光照、CO₂、水分和温度可能共同影响光合表现。',
   'variables':{'light':'光照强度','temperature':'温度','co2':'CO₂供应','water':'水分状态'},
   'disclaimer':'模型展示定性趋势，不对应真实光合速率、气泡数或任意植物的最佳温度。',
 },
 '种子萌发': {
   'title':'水分、温度与种子萌发',
   'objective':'比较典型种子在不同水分、氧气和温度条件下的萌发可能性，学习单一变量对照。',
   'variables':{'moisture':'水分状态','temperature':'温度','oxygen':'氧气条件'},
   'disclaimer':'以常见作物种子的一般教学趋势为例，真实萌发依赖物种、种子活力、观察时长等。',
 },
}

VALID={
 '光合作用':{'light':(0,100),'temperature':(5,45),'co2':['不足','适中','充足'],'water':['不足','充足']},
 '种子萌发':{'moisture':['干燥','适量','完全浸没'],'temperature':(5,45),'oxygen':['不足','充足']},
}

def validate_config(kind, config):
    if kind not in EXPERIMENTS:
        raise ValueError('不支持的实验类型')
    fields=VALID[kind]
    if not isinstance(config,dict) or set(config)!=set(fields):
        raise ValueError('实验变量缺失或出现未知变量')
    for key,expected in fields.items():
        value=config[key]
        if isinstance(expected,tuple):
            if type(value) is not int or not expected[0]<=value<=expected[1]:
                raise ValueError(f'{key}不在有效整数范围内')
        elif value not in expected:
            raise ValueError(f'{key}不是有效选项')
    return True


def simulate(kind, config):
    """Deterministic ordinal teaching response; not a true biological prediction."""
    validate_config(kind,config)
    hints=[]
    if kind=='光合作用':
        light=config['light']
        if light==0: level=0;hints.append('缺少光照，本示意模型中不发生光驱动的光合作用')
        elif light<30:level=1;hints.append('光照较弱，可能成为限制因素')
        elif light<65:level=2;hints.append('光照处于中等设置')
        else:level=3;hints.append('在其他条件适宜的假定下，较强光照可支持较高表现')
        if config['co2']=='不足':
            level=min(level,1);hints.append('CO₂供应不足可能限制光合作用')
        elif config['co2']=='适中':
            level=min(level,2);hints.append('CO₂供应处于中等设置')
        if config['water']=='不足':
            level=min(level,1);hints.append('水分不足可能影响叶片正常生理过程')
        temp=config['temperature']
        if temp <= 10 or temp>=40:
            level=min(level,1);hints.append('极端温度可能明显抑制相关酶活性')
        elif temp<18 or temp>33:
            level=min(level,2);hints.append('偏离本示例的适宜温度区间，表现可能降低')
        title=['不显示光合表现','较低','中等','相对较高'][level]
    else:
        temp=config['temperature']
        level=3
        if temp<=10 or temp>=40:
            level=0;hints.append('温度明显偏离常见作物种子的适宜范围')
        elif temp<18 or temp>32:
            level=min(level,1);hints.append('温度偏离示意的适宜范围')
        if config['moisture']=='干燥':
            level=0;hints.append('缺水时种子通常难以启动萌发过程')
        elif config['moisture']=='完全浸没':
            level=min(level,1);hints.append('完全浸没可能妨碍典型种子的氧气供应')
        if config['oxygen']=='不足':
            level=min(level,1);hints.append('氧气不足可能妨碍呼吸与萌发')
        title=['很难萌发','萌发条件不理想','中等适宜','较适宜'][level]
    return {
        'ordinal_level':level,
        'label':title,
        'explanations':hints,
        'kind':kind,
        'disclaimer':EXPERIMENTS[kind]['disclaimer'],
    }


def make_trial(kind,config,prediction='',trial_id=None):
    """Return plain-JSON-safe trial for browser-local recording."""
    result=simulate(kind,config)
    return {
      'trial_id':trial_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'),
      'kind':kind,'config':dict(config),
      'prediction':str(prediction or '').strip()[:300],
      'result':result,
      'source':'程序生成的教学示意模型；非真实实验观测',
    }


def compare_trials(first,second):
    if first.get('kind')!=second.get('kind') or first.get('kind') not in EXPERIMENTS:
        raise ValueError('不同实验类型的试验不能直接做对照')
    kind=first['kind']
    a,b=first['config'],second['config']
    validate_config(kind,a);validate_config(kind,b)
    differences=[k for k in EXPERIMENTS[kind]['variables'] if a[k]!=b[k]]
    names=[EXPERIMENTS[kind]['variables'][k] for k in differences]
    if not differences:
        verdict='没有改变条件，不能据此判断某个变量的影响。'
        controlled=False
    elif len(differences)>1:
        verdict='同时改变多个因素，存在变量混杂；无法把结果差异归因于其中一个因素。'
        controlled=False
    else:
        verdict=f'仅改变“{names[0]}”，其他已列条件保持一致，属于基本的单变量对照设计。'
        controlled=True
    before=first['result']['ordinal_level'];after=second['result']['ordinal_level']
    change=('示意等级升高' if after>before else '示意等级降低' if after<before else '示意等级未变')
    return {'changed_fields':differences, 'changed_labels':names,'controlled':controlled,
            'verdict':verdict,'demonstration_change':change,
            'caution':'这里只比较教学示意函数的输出；不构成真实生物实验的因果证据。'}


def visual_indicator(kind,config):
    """A smooth 0-100 *pedagogical* display index, not rate/observed measurement.

    The ordinal simulate() remains unchanged for existing reproducibility/tests.
    """
    validate_config(kind,config)
    if kind=='光合作用':
        # Monotonic rise to near saturation (not linear forever).
        light=config['light']
        light_factor=0 if light==0 else 1.0-(2.718281828**(-light/32))
        temp=config['temperature']
        temp_factor=max(.08,1.0-((temp-25)/24)**2)
        co2_factor={'不足':.25,'适中':.7,'充足':1.0}[config['co2']]
        water_factor={'不足':.4,'充足':1.0}[config['water']]
        index=round(100*light_factor*temp_factor*co2_factor*water_factor)
    else:
        temp=config['temperature']
        temp_factor=max(.04,1.0-((temp-25)/24)**2)
        moisture_factor={'干燥':0,'适量':1,'完全浸没':.2}[config['moisture']]
        oxygen_factor={'不足':.2,'充足':1}[config['oxygen']]
        index=round(100*temp_factor*moisture_factor*oxygen_factor)
    return max(0,min(100,index))


def explain_observation(kind,first,second,comparison):
    """Student-facing interpretation of a recorded experiment comparison."""
    if first['kind']!=kind or second['kind']!=kind:raise ValueError('实验类型不匹配')
    a=visual_indicator(kind,first['config']);b=visual_indicator(kind,second['config'])
    labels=comparison['changed_labels']
    if not labels:
        reasoning='两组没有改变任何设定条件；先调整一个因素，再观察结果。'
    elif len(labels)>1:
        reasoning='改变了'+ '、'.join(labels) +'。即使结果出现差异，也不能判断是哪一个因素起作用；试着只保留一个不同条件。'
    else:
        change='升高' if b>a else '降低' if b<a else '基本不变'
        reasoning=f'两组只改变了{labels[0]}，示意指标从{a}变为{b}，整体{change}。请联系该因素对应的生物过程解释原因。'
    nuance=("光照响应会受温度、CO₂和水分制约，并可能逐渐接近饱和。" if kind=='光合作用'
            else '这里比较的是萌发条件适宜程度，不是每粒种子实际发芽的比例。')
    return {'first':a,'second':b,'difference':b-a,'reasoning':reasoning,'nuance':nuance,
            'index_label':'光合作用条件示意指数' if kind=='光合作用' else '萌发条件示意指数'}
