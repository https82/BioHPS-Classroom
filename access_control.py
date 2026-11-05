"""Separate workspace access codes for the four fictional learners and mentor."""
import hashlib
import hmac
import streamlit as st
from service import read_config

ACTORS={'学生A':'s1','学生B':'s2','学生C':'s3','学生D':'s4','教师':'teacher'}


def _codes():
    return {label:str(read_config('BIOHPS_ACCESS_'+sid.upper(),'') or '').strip() for label,sid in ACTORS.items()}


def authenticated_label():
    codes=_codes()
    if not any(codes.values()):return None  # Local, explicitly labelled demo mode.
    if not all(len(v)>=10 and '请填' not in v for v in codes.values()):
        st.error('工作区访问配置未完成，请管理员配置五个独立访问码。');st.stop()
    label=st.session_state.get('_signed_actor')
    if label in codes:
        token=hashlib.sha256(codes[label].encode()).hexdigest()
        if hmac.compare_digest(token,st.session_state.get('_signed_token','')):return label
    st.title('🌱 探知 · BioHPS')
    st.write('进入自己的学习或导师工作区。课程、练习与科学探究相互连通。')
    options=['学生端','导师端']
    index=1 if st.query_params.get('workspace')=='mentor' else 0
    workspace=st.radio('选择工作区',options,index=index,horizontal=True,key='login_workspace')
    label=st.selectbox('学习身份',list(ACTORS)[:4],key='login_student') if workspace=='学生端' else '教师'
    with st.form('workspace_login'):
        code=st.text_input('工作区访问码',type='password',key='login_access_code')
        submitted=st.form_submit_button('进入工作区',type='primary')
    if submitted:
        if hmac.compare_digest(code,codes[label]):
            st.session_state.clear()
            st.session_state['_signed_actor']=label
            st.session_state['_signed_token']=hashlib.sha256(codes[label].encode()).hexdigest()
            st.rerun()
        else:st.error('访问码不正确，请核对所选工作区。')
    st.caption('竞赛体验使用预设身份。请只输入演示学习资料。')
    st.stop()


def logout():
    st.session_state.clear();st.rerun()
