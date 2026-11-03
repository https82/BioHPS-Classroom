"""BioHPS V10.7 teaching-first, desktop-first qualitative inquiry.

Visual cues are illustrative, not biological measurements or predictions.
Business rules, comparison and durable demo records are reused from V10.6.
"""
from __future__ import annotations
import html
from virtual_lab import make_trial, compare_trials, visual_indicator
from demo_store import add_experiment

INTRO = {
    '光合作用': {'title':'一株水草，怎样证明光照会影响光合作用？',
        'context':'假设在相同温度和CO₂条件下观察水生植物。我们改变光照，观察植物周围氧气释放的示意现象。',
        'goal':'只改变光照，比较两组水草周围气泡的疏密，并解释光照为什么会影响氧的释放。',
        'key':'光合作用的光反应依赖光能。光照改变后，氧释放趋势可能随之变化；但CO₂、温度和水分也可能成为限制因素。'},
    '种子萌发': {'title':'种子需要什么条件，才能开始萌发？',
        'context':'以常见植物种子为例，比较水、氧气和温度改变时的萌发条件。不同种类、活力及观察时长会影响真实结果。',
        'goal':'只改变一种条件，观察种子从未萌发到萌发的示意状态，并解释该条件为什么必要。',
        'key':'种子吸水后会启动代谢活动，呼吸通常需要氧气；温度会影响酶活性。缺少其中一个必要条件时，萌发可能受阻。'},
}


def bubble_count(indicator: int) -> int:
    """Bubble ICON count, not bubble/minute or measured oxygen."""
    return 0 if indicator <= 1 else max(1,min(9,round(indicator/11)))


def sprout_count(indicator: int) -> int:
    """Sprout ICON count for visual illustration, NOT germination percentage."""
    return 0 if indicator <= 2 else max(1,min(8,round(indicator/12)))


def _plant_svg(index: int) -> str:
    """Deterministic water-plant diagram with visible oxygen bubble icons."""
    count=bubble_count(index)
    dots=[]
    for k in range(count):
        x=168 + ((k*47)%92) - 46
        y=174 - (k*19)%121
        r=4 + k%3
        dots.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#dff9ff" stroke="#4698b9" stroke-width="1.5"/>')
    leaves=[]
    for i in range(4):
        y=186-i*30
        leaves.append(f'<ellipse cx="{152 if i%2 else 211}" cy="{y}" rx="32" ry="12" transform="rotate({-27 if i%2 else 27} {152 if i%2 else 211} {y})" fill="{["#4fa777","#439b71","#2e815c","#63b489"][i]}"/>')
    return f'''<svg aria-label="水草与周围的气泡示意图" viewBox="0 0 360 244" style="width:100%;max-height:250px;display:block" role="img">
      <defs><linearGradient id="waterGrad" x2="0" y2="1"><stop stop-color="#ecfafe"/><stop offset="1" stop-color="#b8e2ee"/></linearGradient></defs>
      <rect x="62" y="24" width="235" height="194" rx="24" fill="url(#waterGrad)" opacity=".86"/>
      <path d="M62 28 V197 Q62 218 83 218 H276 Q297 218 297 197 V28" fill="none" stroke="#7eb7c7" stroke-width="5" stroke-linecap="round"/>
      <path d="M68 80 C120 73 170 88 223 77 S272 82 292 78" fill="none" stroke="#84c4d8" stroke-width="2" opacity=".7"/>
      <ellipse cx="180" cy="213" rx="62" ry="8" fill="#a3cbbd" opacity=".5"/>
      <path d="M182 209 Q177 175 188 154 Q199 116 185 87" fill="none" stroke="#28795b" stroke-width="6" stroke-linecap="round"/>
      {''.join(leaves)}
      {''.join(dots)}
    </svg>'''


def _seed_svg(index: int) -> str:
    count=sprout_count(index)
    seeds=[]
    for i in range(8):
        x=42+i*40
        grown=i<count
        stem=(f'<path d="M{x} 135 Q{x-8} 112 {x} {89-(i%3)*5}" fill="none" stroke="#439b72" stroke-width="3"/>'
              f'<ellipse cx="{x-9}" cy="{96-(i%3)*5}" rx="12" ry="6" transform="rotate(25 {x-9} {96-(i%3)*5})" fill="#62b88b"/>'
              f'<ellipse cx="{x+9}" cy="{94-(i%3)*5}" rx="12" ry="6" transform="rotate(-25 {x+9} {94-(i%3)*5})" fill="#459970"/>') if grown else ''
        seeds.append(stem + f'<ellipse cx="{x}" cy="139" rx="11" ry="7" fill="#b48d5e" stroke="#8d6942"/>')
    return f'''<svg aria-label="种子及幼苗发育示意图" viewBox="0 0 360 200" style="width:100%;max-height:235px;display:block" role="img">
     <rect x="12" y="119" width="336" height="58" rx="15" fill="#d6c3a2"/>
     <rect x="12" y="132" width="336" height="43" rx="11" fill="#aa8969" opacity=".7"/>
     {''.join(seeds)}
     <path d="M12 176 Q180 192 348 176" fill="none" stroke="#8b785f" stroke-width="3"/>
    </svg>'''



def render_apparatus(st,kind: str,config: dict,title: str) -> None:
    """Render an SVG apparatus reliably using Streamlit's HTML component.

    Streamlit Markdown is not guaranteed to preserve all inline SVG tags, so
    we intentionally use the same HTML component approach as the existing
    Mendel/chromosome visualizations. No scripts or external assets.
    """
    safe_card=view_card(kind,config,title)
    css="""<style>
    *{box-sizing:border-box}html,body{margin:0;padding:0;background:transparent;color:#194735;
    font-family:-apple-system,BlinkMacSystemFont,'Microsoft YaHei',sans-serif}
    .bio-lab-preview{border-radius:20px;border:1px solid #d6e7e0;
    background:linear-gradient(#f2faf6,#ffffff);padding:18px 20px 18px;
    min-height:355px;box-shadow:0 8px 26px rgba(31,81,58,.04)}
    .bio-lab-heading{display:flex;justify-content:space-between;align-items:center;
    font-size:18px;font-weight:750;color:#184737;gap:14px}
    .bio-lab-heading span{font-size:12px;font-weight:500;color:#658276;
    background:#e8f3ed;padding:6px 10px;border-radius:99px;white-space:nowrap}
    .bio-observation{text-align:center;color:#1b6848;font-size:19px;font-weight:800;margin:5px 0 8px}
    .bio-note{font-size:12px;text-align:center;color:#627d70;line-height:1.5}
    </style>"""
    st.components.v1.html('<meta charset="utf-8">'+css+safe_card,height=367,scrolling=False)

def observation_label(kind: str, indicator: int) -> str:
    """A categorical visualization, not observed field counts."""
    if kind=='光合作用':
        return ('没有明显气泡' if indicator<=1 else '气泡较稀疏' if indicator<40 else '可见较多气泡' if indicator<70 else '气泡较密集')
    return ('种子没有萌发' if indicator<=2 else '少量幼苗出现' if indicator<40 else '部分种子萌发' if indicator<70 else '多数种子萌发')


def view_card(kind: str, config: dict, title: str) -> str:
    level=visual_indicator(kind,config)
    picture=_plant_svg(level) if kind=='光合作用' else _seed_svg(level)
    desc=observation_label(kind,level)
    return f'''<div class="bio-lab-preview"><div class="bio-lab-heading">{html.escape(title)}<span>教学虚拟观察</span></div>
        {picture}<div class="bio-observation">{desc}</div>
        <div class="bio-note">{'气泡代表可能的放氧趋势，不代表实测气泡数。' if kind=='光合作用' else '幼苗图标代表条件适宜程度，不代表真实萌发率。'}</div></div>'''


def mechanism(kind: str,changed_field: str) -> tuple[str,str]:
    if kind=='光合作用':
        return {
            'light':('光照提供光反应所需的能量','在其他条件适宜时，增加光照通常能促进光合作用，但达到光饱和后继续增强光照未必有效。'),
            'temperature':('温度影响相关酶的活性','酶促反应存在适宜温度区间；温度越高不代表光合作用一定越强。'),
            'co2':('CO₂是有机物合成的重要碳源','供给受限时即使光照充足，光合速率也可能受限制。'),
            'water':('水参与光合作用并维持细胞正常生理状态','水分不足可能导致气孔调节等变化，不能简单按线性关系解释。')
        }.get(changed_field,('光合作用受多种因素影响','请检查变量的作用机制和限制因素。'))
    return {
        'moisture':('种子吸水后开始启动代谢','缺水不能正常萌发；完全浸泡还可能因供氧不足而妨碍一些种子的萌发。'),
        'temperature':('温度影响萌发过程中的代谢','不同物种有各自适宜温度，过冷或过热可能阻碍萌发。'),
        'oxygen':('有氧呼吸为萌发活动供应能量','常见植物种子一般需要适宜氧气条件；浸没造成的影响还与物种有关。'),
    }.get(changed_field,('萌发需要多种条件','应控制其他条件、避免混杂。'))


def feedback(kind: str, first: dict, second: dict,comparison: dict,prediction: str) -> dict:
    changed=comparison['changed_fields']
    a=visual_indicator(kind,first);b=visual_indicator(kind,second)
    if len(changed)==1:
        heading,why=mechanism(kind,changed[0])
        summary=f'你只改变了「{comparison["changed_labels"][0]}」，其他已列条件保持一致。这是可比较的单变量设计。'
    elif len(changed)==0:
        heading='先改变一个条件';why='两组条件完全相同，无法检验哪种因素产生影响。'
        summary='两组没有不同条件；你可以尝试只调整一项。'
    else:
        heading='不要一次改变多种条件';why='同时改变多个因素时，即使现象不同，也不能把变化单独归因于某一个因素。'
        summary='你改变了'+ '、'.join(comparison['changed_labels'])+'；请重新设计仅有一个因素不同的实验。'
    if a==b: trend='两组示意现象相近'
    elif b>a: trend='第二组的示意现象更明显'
    else: trend='第一组的示意现象更明显'
    if not prediction.strip(): check='下次在操作前先写下你的预测，再比较结果。'
    else:check='请对照操作前写下的预测，判断它是否受到本次比较的支持。'
    return {'heading':heading,'mechanism':why,'comparison':summary,'trend':trend,'reflection':check}


def _photo_controls(st,label: str,prefix: str):
    st.markdown(f'**{label}**')
    light=st.slider('光照强度',0,100,30 if prefix=='A' else 80,key=f'v107_{prefix}_light')
    temperature=st.slider('温度（℃）',5,45,25,key=f'v107_{prefix}_temp')
    co2=st.selectbox('CO₂供应',['不足','适中','充足'],index=2,key=f'v107_{prefix}_co2')
    water=st.selectbox('水分状态',['充足','不足'],key=f'v107_{prefix}_water')
    return {'light':light,'temperature':temperature,'co2':co2,'water':water}


def _seed_controls(st,label: str,prefix: str):
    st.markdown(f'**{label}**')
    moisture=st.selectbox('水分状态',['干燥','适量','完全浸没'],index=1 if prefix=='A' else 1,key=f'v107_{prefix}_moisture')
    temperature=st.slider('温度（℃）',5,45,25,key=f'v107_{prefix}_seedtemp')
    oxygen=st.selectbox('氧气条件',['充足','不足'],index=0 if prefix=='A' else 1,key=f'v107_{prefix}_oxygen')
    return {'moisture':moisture,'temperature':temperature,'oxygen':oxygen}


def render_lab(st,student: str):
    st.markdown('''<div class="bio-section-kicker">SCIENTIFIC INQUIRY · 探究实验室</div>
       <h2 class="bio-lab-title">亲自做一次对照实验</h2>
       <p class="bio-lead">不要先看结果：先提出预测，只改变一个条件，再从生物现象中寻找证据。</p>''',unsafe_allow_html=True)
    kind=st.radio('选择实验课题',['光合作用','种子萌发'],key=f'v107_lab_kind_{student}',horizontal=True)
    meta=INTRO[kind]
    st.markdown(f'''<div class="bio-lab-brief"><div class="bio-step-tag">01 · 研究问题</div>
       <h3>{meta['title']}</h3><p>{meta['context']}</p><div class="bio-brief-goal"><b>今天要证明什么</b>　{meta['goal']}</div></div>''',unsafe_allow_html=True)
    stored=st.session_state.get(f'v107_last_lab_{student}')
    if stored and stored[0]!=kind:
        stored=None
    # The learning OBJECTS are visible before the control form, unlike the old chart-first UI.
    st.markdown('#### 02 · 实验装置与观察区')
    if stored:
        setup_a,setup_b=stored[1]['config'],stored[2]['config']
    elif kind=='光合作用':
        setup_a,setup_b=({'light':0,'temperature':25,'co2':'充足','water':'充足'},)*2
    else:
        setup_a,setup_b=({'moisture':'干燥','temperature':25,'oxygen':'充足'},)*2
    panel_a,panel_b=st.columns(2,gap='large')
    with panel_a:render_apparatus(st,kind,setup_a,'对照组 A')
    with panel_b:render_apparatus(st,kind,setup_b,'实验组 B')
    if not stored:
        st.caption('先在下面设定两组条件，点击「开始观察实验」后，装置里才会出现本次模拟现象。')
    st.markdown('#### 03 · 先作预测，再设置两组条件')
    with st.form(f'v107_lab_form_{student}_{kind}'):

        cols=st.columns(2,gap='large')
        with cols[0]:
            first=_photo_controls(st,'对照组 A','A') if kind=='光合作用' else _seed_controls(st,'对照组 A','A')
        with cols[1]:
            second=_photo_controls(st,'实验组 B','B') if kind=='光合作用' else _seed_controls(st,'实验组 B','B')
        prediction=st.text_area('我预测观察到的变化',placeholder='例如：在其余条件相同时，提高光照强度，水草周围的气泡可能更密集。',max_chars=280,height=78)
        start=st.form_submit_button('开始观察实验',type='primary',use_container_width=True)
    if start:
        trial_a=make_trial(kind,first,prediction)
        trial_b=make_trial(kind,second,prediction)
        comparison=compare_trials(trial_a,trial_b)
        add_experiment(student,kind,comparison,first=trial_a,second=trial_b)
        st.session_state[f'v107_last_lab_{student}']=(kind,trial_a,trial_b,comparison,prediction)
        st.rerun()
    stored=st.session_state.get(f'v107_last_lab_{student}')
    if not stored or stored[0]!=kind:
        return
    _,a,b,d,pred=stored
    aconf=a['config'];bconf=b['config']
    info=feedback(kind,aconf,bconf,d,pred)
    st.markdown('#### 04 · 把观察转化成证据')
    st.markdown(f'''<div class="bio-result-focus"><div class="bio-step-tag">观察结论</div>
       <h3>{info['trend']}</h3><p>{info['comparison']}</p></div>''',unsafe_allow_html=True)
    st.markdown('#### 05 · 解释为什么会这样')
    st.markdown(f'''<div class="bio-explanation"><b>{info['heading']}</b><p>{info['mechanism']}</p>
        <p>{info['reflection']}</p></div>''',unsafe_allow_html=True)
    with st.expander('想进一步学懂原理？'):
        st.write(meta['key'])
        st.write('这里的气泡和幼苗是教学模型的可视化示意，不是从真实植株测得的数据。要得出实际实验结论，需要真实测量、足够重复并控制其他条件。')
    st.markdown('#### 06 · 自己检验是否理解')
    target='同一个实验中，为什么不能同时改变光照和温度？' if kind=='光合作用' else '为什么比较种子萌发时应该只改变水分或氧气中的一项？'
    choices=['因为同时改变多个条件后，不能判断结果由哪一个条件造成','因为科学实验不允许使用温度计','因为每组都必须产生完全相同的结果']
    choice=st.radio(target,choices,key=f'v107_check_{student}_{kind}')
    if st.button('检查我的推理',key=f'v107_check_btn_{student}_{kind}'):
        if choice==choices[0]:st.success('判断正确。单变量对照能够帮助排除其他因素的干扰。')
        else:st.warning('再想一想：如果两个条件都变了，你能指出哪一个才导致变化吗？')
    st.caption('已将这次实验设计与预测保存到你的学习档案，教师端可查看学习过程。')
