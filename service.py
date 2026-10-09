"""Small OpenAI-compatible completion client with a safe user-facing error contract."""
import os
import requests


def read_config(key, default=""):
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


def call_ai(messages, requester=None):
    key = read_config('BIOHPS_API_KEY')
    base = read_config('BIOHPS_API_BASE').rstrip('/')
    model = read_config('BIOHPS_MODEL')
    if not (key and base and model):
        return {'ok': False, 'error': '未配置完整的API参数', 'model': None, 'text': '', 'tokens': None}
    if not base.startswith('https://'):
        return {'ok': False, 'error': 'API必须使用HTTPS地址', 'model': None, 'text': '', 'tokens': None}
    try:
        post = requester or requests.post
        response = post(base+'/chat/completions',
            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},
            json={'model': model,'messages': messages, 'max_tokens': 2200}, timeout=85)
        if not response.ok:
            hints={400:'请求参数不兼容',401:'API密钥无效',402:'余额不足',403:'调用权限不足',404:'模型不可用',429:'触发额度或频率限制',503:'服务提供方不可用'}
            return {'ok':False,'error':f'HTTP {response.status_code} · '+hints.get(response.status_code,'服务请求失败'),'model':model,'text':'','tokens':None}
        data=response.json()
        msg=data['choices'][0].get('message',{})
        content=msg.get('content') or ''
        if isinstance(content, list):
            content='\n'.join(x.get('text','') for x in content if isinstance(x,dict) and x.get('type')=='text')
        text=content.strip() if isinstance(content,str) else ''
        if not text:
            reason=data['choices'][0].get('finish_reason','unknown')
            return {'ok':False,'error':f'模型返回空文本（finish_reason={reason}），请缩短上下文或调整模型输出配置','model':data.get('model',model),'text':'','tokens':data.get('usage')}
        return {'ok':True,'error':'','model':data.get('model',model),'text':text,'tokens':data.get('usage')}
    except requests.Timeout:
        return {'ok':False,'error':'请求超时，请检查模型服务或稍后重试','model':model,'text':'','tokens':None}
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        return {'ok':False,'error':'模型响应异常：'+type(exc).__name__,'model':model,'text':'','tokens':None}
