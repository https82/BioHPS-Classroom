from pathlib import Path
p=Path(__file__).resolve().parents[1]/'app.py'
s=p.read_text(encoding='utf-8')
s=s.replace('from learning_loop import BANK, available, new_session, current_question, submit_answer, start_recheck, progress_summary', '''from learning_loop import BANK, available, new_session, current_question, submit_answer, start_recheck, progress_summary
from senior_practice import SENIOR_BANK
BANK.update(SENIOR_BANK)''')
s=s.replace('from curriculum import THEMES, MODES, OFFICIAL_CURRICULUM, load_cards, get_theme_cards, retrieve, resolve_course_context, make_course_messages, sanitize_course_answer', '''from curriculum import (THEMES, MODES, OFFICIAL_CURRICULUM, SENIOR_THEMES,
    SENIOR_CURRICULUM, load_all_cards, filter_stage, get_theme_cards,
    retrieve, resolve_course_context, make_course_messages, sanitize_course_answer)''')
s=s.replace("page_title='探知 BioHPS | AI生物智慧课堂'", "page_title='探知 BioHPS | 初高中生物学习'")
s=s.replace("initial_sidebar_state='expanded'", "initial_sidebar_state='collapsed'")
s=s.replace('    CURRICULUM_CARDS=load_cards(ROOT)','    CURRICULUM_CARDS=load_all_cards(ROOT)')
s=s.replace("    st.error('知识库文件缺失或格式无效，软件暂时无法启动课程教学。请确认已复制完整的 knowledge 文件夹。')", "    st.error('课程内容暂时无法加载，请联系维护人员检查课程文件。')")
s=s.replace("    st.code('必须包含：knowledge/library.json 及 knowledge/curriculum_cards.json')", "    st.code('请检查：knowledge 目录和所有课程内容文件')")
start=s.index('NAV=[')
end=s.index('\n\n\ndef reset():',start)
s=s[:start]+'''# Keep advanced HPS / record / teacher features, but offer only five daily-use tabs.
NAV=['🏠 首页','🧠 科学探究','📊 学习记录','📚 科学故事','🧑‍🏫 教师与帮助',
     '💬 问问题','✅ 做练习','🧪 做实验','📖 学课程']
NAV_ORDER=[NAV[0],NAV[8],NAV[5],NAV[6],NAV[7]]
''' +s[end:]
s=s.replace("def go_course(question='', mode='知识理解'):","def go_course(question='', mode='知识理解', stage=None):")
s=s.replace("    st.session_state['course_question']=question", "    st.session_state['course_question']=question\n    if stage in ('初中','高中','自动'):\n        st.session_state['course_stage']=stage\n        if stage!='自动': st.session_state['site_stage']=stage")
s=s.replace("    if card_id in BANK:\n        st.session_state['learning_card_choice']=card_id", "    if card_id in BANK:\n        st.session_state['learning_card_choice']=card_id\n        st.session_state['practice_stage']='高中' if card_id.startswith('HS-') else '初中'")
start=s.index('with st.sidebar:\n')
end=s.index("if st.session_state.get('old_case')!=case:",start)
s=s[:start]+'''with st.sidebar:
    st.markdown('### 🌿 探知 BioHPS')
    st.caption('初高中生物学习')
    st.radio('课程阶段',['初中','高中'],key='site_stage',horizontal=True)
    st.divider()
    st.caption('其他功能')
    st.button('📊 我的学习记录',use_container_width=True,on_click=go,args=(NAV[2],))
    st.button('🔬 科学探究对话',use_container_width=True,on_click=go,args=(NAV[1],))
    st.button('📚 科学故事',use_container_width=True,on_click=go,args=(NAV[3],))
    st.button('🧑‍🏫 教师备课',use_container_width=True,
              on_click=go_course,args=('', '教师备课'))
    with st.expander('设置与使用说明',expanded=False):
        st.caption('学习内容为辅助资料，重要概念请结合教材核对。')
        st.caption('AI回答可能出错，请勿输入姓名、电话或其他个人隐私。')
        st.caption('在线提问会调用外部AI服务。')
        st.caption('当前AI模型：'+str(read_config('BIOHPS_MODEL') or '未设置'))
        st.button('作品与使用帮助',on_click=go,args=(NAV[4],))
    if 'selected_case' not in st.session_state:
        st.session_state.selected_case=list(CASES)[0]
    if st.session_state.get('navigation') in (NAV[1],NAV[2],NAV[3]):
        st.selectbox('科学探究主题',list(CASES),key='selected_case')
        if st.button('重新开始探究',use_container_width=True):
            reset();st.rerun()
    case=st.session_state.selected_case
    use_ai=True

''' +s[end:]
start=s.index('st.markdown(\'<div class="hero">')
end=s.index("elif page==NAV[1]:",start)
s=s[:start]+'''st.markdown('<div style="font-size:27px;font-weight:780;color:#183f32;margin:0 0 4px">🌿 探知 BioHPS</div>',unsafe_allow_html=True)
st.caption('你的初高中生物学习伙伴')
st.radio('学习导航',NAV_ORDER,key='navigation',horizontal=True,label_visibility='collapsed')
st.divider()
page=st.session_state.navigation

if page==NAV[0]:
    st.markdown('## 想学什么生物知识？')
    st.caption('直接问、按课程学，或者动手练一练。')
    st.text_input('输入你想了解的问题',placeholder='例如：DNA为什么能储存遗传信息？',key='home_question')
    st.button('开始提问',type='primary',use_container_width=True,
              on_click=lambda:go_course(st.session_state.get('home_question',''),stage=st.session_state.get('site_stage','初中')))
    st.markdown('### 选择一种学习方式')
    c1,c2,c3=st.columns(3,gap='medium')
    with c1:
        st.markdown('**📖 按课程学**')
        st.caption('初中七大主题、高中五大模块')
        st.button('浏览课程',use_container_width=True,on_click=go,args=(NAV[8],))
    with c2:
        st.markdown('**✅ 练一练**')
        st.caption('答题、纠错，再换一道题巩固')
        st.button('开始练习',use_container_width=True,on_click=go,args=(NAV[6],))
    with c3:
        st.markdown('**🧪 做实验**')
        st.caption('改变条件，学会设计对照实验')
        st.button('进入实验',use_container_width=True,on_click=go,args=(NAV[7],))
    st.markdown('### 试试这些问题')
    samples=(
        [('鲸为什么不是鱼？','为什么鲸生活在水里却属于哺乳动物？'),
         ('植物为什么需要光？','绿色植物为什么需要光照？'),
         ('什么是食物链？','食物链和食物网有什么联系？')]
        if st.session_state.get('site_stage','初中')=='初中' else
        [('ATP有什么作用？','ATP如何为细胞生命活动供能？'),
         ('什么是减数分裂？','减数分裂中染色体如何变化？'),
         ('什么是血糖稳态？','胰岛素与胰高血糖素怎样调节血糖？')]
    )
    for col,(label,question) in zip(st.columns(3),samples):
        with col:
            st.button(label,use_container_width=True,on_click=go_course,
                      args=(question,'知识理解',st.session_state.get('site_stage','初中')),
                      key='home_sample_'+label)

elif page==NAV[8]:
    headline('📖 学课程','按初中主题或高中模块查找知识点。不同教材版本的章节安排可能有差异。')
    if 'catalog_stage' not in st.session_state:
        st.session_state.catalog_stage=st.session_state.get('site_stage','初中')
    grade=st.radio('学习阶段',['初中','高中'],key='catalog_stage',horizontal=True)
    topics=THEMES if grade=='初中' else SENIOR_THEMES
    topic=st.selectbox('学习主题',topics,key='catalog_topic_'+grade)
    study_cards=[c for c in CURRICULUM_CARDS if c['theme']==topic and c.get('grade','初中')==grade]
    search=st.text_input('搜索知识点',placeholder='输入关键词，例如 细胞、免疫、遗传…',key='catalog_search')
    if search.strip():
        study_cards=[c for c in study_cards if search.lower().strip() in
                   (c['title']+' '+c['summary']+' '+' '.join(c.get('keywords',[]))).lower()]
    st.caption(f'本主题已有 {len(study_cards)} 条学习概要')
    if study_cards:
        by_id={x['id']:x for x in study_cards}
        chosen=st.selectbox('选择知识点',list(by_id),format_func=lambda cid:by_id[cid]['title'],key='catalog_card_'+grade)
        item=by_id[chosen]
        st.markdown('#### '+escape(item['title']))
        st.write(item['summary'])
        st.markdown('**想一想：** '+item.get('guide_question','你能举出生活中的例子吗？'))
        left,right=st.columns(2)
        with left:
            st.button('问AI进一步理解',type='primary',use_container_width=True,
                      on_click=go_course,args=(item.get('guide_question',item['title']),'知识理解',grade))
        with right:
            if chosen in BANK:
                st.button('做这节的练习',use_container_width=True,on_click=go_learning,args=(chosen,))
            else:
                st.button('换个问题问AI',use_container_width=True,on_click=go_course,
                          args=('请用中学生能理解的方式讲解'+item['title'],'知识理解',grade))
    else:
        st.info('这一主题下没有找到相关知识点，请换个关键词或直接向AI提问。')
    with st.expander('课程资料说明'):
        st.write('目前收录初中153条、高中112条人工编写的课程学习概要，覆盖主要主题，但不是完整教材，也未完成学科教师逐条审核。')
        st.markdown('初中主题参考：[义务教育生物学课程标准（2022年版）]('+OFFICIAL_CURRICULUM+')')
        st.markdown('高中模块参考：[普通高中生物学课程标准（2017年版2020年修订）]('+SENIOR_CURRICULUM+')')

''' +s[end:]
# user-facing practice and lab text less jargon, no status clutter
s=s.replace("headline('🎯 自适应学练 · 从听懂到真正会做',\n             '先用精选知识题检测理解；答错后对应纠错，再用不同题目复测。成绩是当前会话的练习记录，需教师复核。')\n    st.info('**与普通聊天的区别：** 不是AI一句“你掌握了”就算通过。只有实际提交答案，并由可检查的预编写答案规则判定后，系统才更新本次练习状态。')", "headline('✅ 做练习','先答一道题，答错会帮助你理解，再换一道题巩固。')")
s=s.replace("    bank_ids=[cid for cid in BANK if cid in by_id]\n    cid=st.selectbox('选择练习知识点（已制作两套检测题的精选内容）',bank_ids,", "    if 'practice_stage' not in st.session_state:\n        st.session_state.practice_stage=st.session_state.get('site_stage','初中')\n    practice_stage=st.radio('学习阶段',['初中','高中'],key='practice_stage',horizontal=True)\n    bank_ids=[cid for cid in BANK if cid in by_id and by_id[cid].get('grade','初中')==practice_stage]\n    if st.session_state.get('learning_card_choice') not in bank_ids:\n        st.session_state.pop('learning_card_choice',None)\n    cid=st.selectbox('选择练习知识点',bank_ids,")
s=s.replace("format_func=lambda x:f\"{by_id[x]['theme']}｜{by_id[x]['title']}（{x}）\"", "format_func=lambda x:by_id[x]['title']")
s=s.replace("        st.caption('这张知识卡未经教师逐条审核；练习题是开发者编写的初步形成性评价，不代表正式考试成绩。')", "        # Learning information kept in the help accordion rather than every card.")
s=s.replace("        st.markdown('**关联易混淆点：** '+c.get('misconception','暂无'))", "        with st.expander('容易弄错的地方'):\n            st.write(c.get('misconception','暂无'))")
s=s.replace("        st.markdown('**为什么只有21个知识点支持自动核对？**')\n        st.caption('153张知识卡都能用于课程问答。但客观题必须逐道编写答案和误区解释；尚未完成审核的其他内容不冒充已验证的自动评分。')", "        with st.expander('关于练习范围'):\n            st.caption('练习仅覆盖部分知识点，答案仍需教师复核；其他知识点可以继续使用自由问答。')")
s=s.replace("headline('🔬 虚拟实验室 · 亲手改变变量，理解科学对照',\n             '先预测，再记录模拟结果，最后比较两组条件。实验不调用DeepSeek；所有现象都是明确标记的教学示意，不是实测数据。')", "headline('🧪 做实验','自己调整实验条件，比较两组结果，学习怎样做好对照。')")
s=s.replace("    st.warning('**科学性声明：** '+spec['disclaimer']+' 这是为理解实验变量而编写的定性示意模型，不能用于推算实际光合速率、萌发概率或作物最适温度。')", "    with st.expander('这是什么实验？'):\n        st.write('这里的结果用于帮助理解实验设计，不是对真实生物实验的测量。')\n        st.caption(spec['disclaimer'])")
s=s.replace("'记录本次示意试验'", "'保存本组实验'")
s=s.replace("'最新示意结果'", "'本组示意结果'")
s=s.replace("text='相对教学示意等级（不是实测百分比）'", "text='示意等级'")
s=s.replace("'示意结果':t['result']['label']", "'结果':t['result']['label']")
s=s.replace("st.write('**观察到的示意变化：** '+result['demonstration_change'])", "st.write('**两组比较：** '+result['demonstration_change'])")
s=s.replace("st.caption(result['caution'])", "# Evidence caveat is retained within the experiment help section.")
s=s.replace("st.caption('至少记录两组试验，才能检查控制变量是否合理。')", "st.caption('先保存两组不同条件的实验，再来比较。')")
s=s.replace("'清空这个实验的示意记录'", "'清空本次实验记录'")
# AI page streamlined
s=s.replace("headline('💬 全课程AI课堂 · 直接提问，自动识别',\n             '无需选择章节！直接输入生物学问题。系统优先匹配课程知识卡，未收录的问题交由AI谨慎辅导。')\n    st.caption('默认自动匹配 · 无需选择教材章节 · 知识库未覆盖时可用通用AI答疑（将明确标注）。153张知识卡仍待教师逐条审核。')\n    st.markdown(f'**主题覆盖：** {len(THEMES)}个主题 · {len(CURRICULUM_CARDS)}张原创知识卡（待审核） · {len(MODES)}种课堂任务模式')", "headline('💬 问问题','不需要先选章节，直接问你不明白的生物问题。')\n    st.radio('学习阶段',['自动','初中','高中'],key='course_stage',horizontal=True)")
# minimize curriculum directory
start=s.index("    with st.expander('📚 查看七大课程主题目录'",s.index("else:\n    headline('💬 问问题'"))
end=s.index("    mode=st.radio('选择本次学习方式'",start)
s=s[:start]+"    # The full curriculum catalogue now has its own clean page.\n"+s[end:]
s=s.replace("mode=st.radio('选择本次学习方式',MODES,horizontal=True,key='course_mode')", "mode=st.selectbox('我想要',MODES,key='course_mode')")
s=s.replace("with st.expander('⚙️ 高级设置（非必选）· 想手动限定章节时再展开',expanded=False):", "with st.expander('按知识点查找（可选）',expanded=False):")
s=s.replace("selected_theme=st.selectbox('学习主题',['自动识别']+THEMES,key='course_theme')", "selected_theme=st.selectbox('学习主题',['自动识别']+(SENIOR_THEMES if st.session_state.course_stage=='高中' else THEMES if st.session_state.course_stage=='初中' else THEMES+SENIOR_THEMES),key='course_theme')")
s=s.replace("visible_cards=CURRICULUM_CARDS if selected_theme=='自动识别' else get_theme_cards(CURRICULUM_CARDS,selected_theme)","visible_cards=filter_stage(CURRICULUM_CARDS,st.session_state.course_stage) if selected_theme=='自动识别' else get_theme_cards(CURRICULUM_CARDS,selected_theme)")
s=s.replace("level=st.selectbox('学习层次',['初中通用','七年级入门','八年级拓展'],key='course_level')", "level= {'高中':'高中课程','初中':'初中课程','自动':'根据问题自动调整'}[st.session_state.course_stage]")
s=s.replace("        st.caption('不同教材的章节排序可能有差异；课程主题与年级册次并非固定一一对应关系。')", "        st.caption('章节顺序以你正在使用的教材为准。')")
s=s.replace("    if selected_theme=='自动识别' and selected_id is None:\n        st.caption('✅ 当前：自动识别主题与知识点，无需手动选择章节。')\n    else:\n        st.caption('ℹ️ 当前：手动限定了主题或知识点，仅在你需要时使用。')", "    if selected_theme!='自动识别' or selected_id is not None:")
s=s.replace("course_key = '|'.join([selected_theme, str(selected_id or ''), mode, level])", "course_key = '|'.join([selected_theme, str(selected_id or ''), mode, level])")
s=s.replace("'发送给AI（可能产生API费用）'", "'发送问题'")
s=s.replace("        elif not use_ai:\n            st.warning('左侧的实时AI开关目前关闭。')\n","")
s=s.replace("question,CURRICULUM_CARDS,selected_id=selected_id,", "question,filter_stage(CURRICULUM_CARDS,st.session_state.course_stage),selected_id=selected_id,")
s=s.replace("            if not ctx:\n                st.info('本地知识卡未收录这一提问；将使用通用AI生物辅导，不会假称引用教材。')", "            if not ctx:\n                st.caption('这道题没有找到本地学习资料，将使用AI直接解释。')")
s=s.replace("'正在自动识别知识主题并生成教学反馈…'", "'正在思考你的问题…'")
s=s.replace("        st.markdown('#### 💬 本次课堂对话')", "        st.markdown('### 我们的对话')")
s=s.replace("            st.info('无需选择任何章节，直接输入生物学问题即可。系统会自动匹配知识卡或进行通用AI辅导。')", "            st.caption('你的问题和回答会显示在这里。')")
s=s.replace("        st.markdown('#### 📚 本地知识依据')", "        st.markdown('#### 相关课程内容')")
s=s.replace("            st.caption('本轮知识来源：'+latest['retrieval'])\n            st.caption('实际响应模型：'+latest['model'])", "            # Provenance remains in the downloadable session record.")
s=s.replace("                st.warning('本轮未命中本地知识卡：回答来自通用AI知识，尚未进行教材依据核验。')", "                st.caption('本轮由AI直接作答，可结合教材核对。')")
s=s.replace("                st.info('直接提问后，这里将显示匹配的知识卡或标记为通用AI答疑。')", "                st.caption('回答后这里会显示相关课程内容。')")
s=s.replace("with st.expander(entry['id']+' · '+entry['title'],expanded=True):", "with st.expander(entry['title'],expanded=False):")
s=s.replace("                st.caption('所属主题：'+entry['theme'])", "                st.caption('主题：'+entry['theme'])")
s=s.replace("                st.caption('审核状态：'+entry.get('review_status','待教师审核'))\n                st.caption('资料说明：'+entry.get('source_title','原创知识概要'))\n                st.caption('课程标准链接只用于主题组织，不是该知识点的逐条事实引用。')", "                with st.expander('资料说明'):\n                    st.caption('该内容为人工编写的学习概要，尚需教师复核，不等于教材原文。')")
s=s.replace("                if entry.get('curriculum_reference','').startswith('https://www.moe.gov.cn/'):", "                if entry.get('curriculum_reference','').startswith(('https://www.moe.gov.cn/','https://www.pep.com.cn/')):")
s=s.replace("                if latest and entry['id'] in latest.get('knowledge_match_scores',{}):\n                    st.caption('检索相对匹配分：'+str(latest['knowledge_match_scores'][entry['id']])+'（不是准确率或置信度）')", "")
s=s.replace("        st.divider()\n        st.caption('课程问答调用次数：'+str(st.session_state.course_calls)+' / 18（当前浏览器会话）')\n        st.caption('优先采用专业词语、课程别名与离线TF-IDF相似度混合检索；未命中时自动由模型进行通用生物知识辅导，不使用外部向量模型，也不代表权威教材逐条核验。')", "        with st.expander('学习提醒'):\n            st.caption('AI回答和学习资料可能存在错误，重要内容请对照教材。')")
s=s.replace("    st.markdown('**拓展说明：** 开发者可在 `knowledge/custom_notes.jsonl` 添加新的课程卡片，扩展至出版社教材或校本课程，但需自行核实来源、版权与科学准确性。')", "")
s=s.replace("st.caption('BioHPS V7.0 · 全课程AI生物智慧课堂 | 21个精选知识点的离线学练 + 两类教学示意实验。知识卡仍待教师审核，结果不代表真实教学效果。')", "st.caption('探知 BioHPS · 初高中生物学习助手')")
s=s.replace("BioHPS V7.0", "BioHPS V8.0")
p.write_text(s,encoding='utf-8')
