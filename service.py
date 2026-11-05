"""Server-side TeleAI Responses client, retaining legacy completion compatibility."""
import os
import threading
import time
from urllib.parse import urlsplit
import requests

_IN_FLIGHT = threading.BoundedSemaphore(1)


def provider_name(base=None):
    base=str(base if base is not None else read_config('BIOHPS_API_BASE',''))
    host=urlsplit(base).hostname or ''
    if host=='openapi.teleagi.cn':return '中国电信星辰大模型'
    if host=='api.deepseek.com':return 'DeepSeek'
    return '已配置的在线模型'


def read_config(key, default=""):
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


def _configured_value(value):
    value=str(value or '').strip()
    return bool(value) and not any(mark in value.lower() for mark in (
        '请填写','请填入','your_api_key','your-model','example_api_key','placeholder'))


def config_status():
    keys={'BIOHPS_API_BASE':'API地址','BIOHPS_MODEL':'模型名称','BIOHPS_API_KEY':'API密钥'}
    missing=[label for key,label in keys.items() if not _configured_value(read_config(key,''))]
    return {'ready':not missing,'missing_labels':missing}


def call_ai(messages, requester=None, *, json_output=False, output_schema=None, max_tokens=2200):
    key = read_config('BIOHPS_API_KEY')
    base = str(read_config('BIOHPS_API_BASE','') or '').strip().rstrip('/')
    model = str(read_config('BIOHPS_MODEL','') or '').strip()
    if not all(_configured_value(value) for value in (key,base,model)):
        return {'ok': False, 'error': '未配置完整的API参数', 'model': None, 'text': '', 'tokens': None}
    if not base.startswith('https://'):
        return {'ok': False, 'error': 'API必须使用HTTPS地址', 'model': None, 'text': '', 'tokens': None}
    provider=provider_name(base)
    try:
        post = requester or requests.post
        responses=base.endswith('/responses') or urlsplit(base).hostname=='openapi.teleagi.cn'
        if responses:
            endpoint=base if base.endswith('/responses') else base+'/responses'
            payload={'model':model,'input':[{'role':m['role'],'content':m['content']} for m in messages],
                     'stream':False,'max_output_tokens':max_tokens,'reasoning':{'effort':'none'}}
            if output_schema:
                payload['text']={'format':{'type':'json_schema','name':'biohps_mentor_content','strict':True,'schema':output_schema}}
            elif json_output:payload['text']={'format':{'type':'json_object'}}
        else:
            endpoint=base if base.endswith('/chat/completions') else base+'/chat/completions'
            payload={'model':model,'messages':messages,'max_tokens':max_tokens}
            if output_schema:payload['response_format']={'type':'json_schema','json_schema':{
                'name':'biohps_mentor_content','strict':True,'schema':output_schema}}
            elif json_output:payload['response_format']={'type':'json_object'}
        # The entry-level model service allows one concurrent request. Never retry a
        # successful response, and never include upstream error bodies/credentials in UI.
        with _IN_FLIGHT:
            for attempt in range(2):
                response=post(endpoint,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},
                              json=payload,timeout=85)
                if getattr(response,'status_code',200 if response.ok else 500) not in (429,503) or attempt:break
                time.sleep(1.2)
        if not response.ok:
            hints={400:'请求参数不兼容',401:'API密钥无效',402:'余额不足',403:'调用权限不足',404:'模型不可用',429:'触发额度或频率限制',503:'服务提供方不可用'}
            return {'ok':False,'error':f'HTTP {response.status_code} · '+hints.get(response.status_code,'服务请求失败'),'model':model,'text':'','tokens':None}
        data=response.json()
        if responses:
            if data.get('status') not in (None,'completed'):
                return {'ok':False,'error':'模型未完整完成回答，请缩小任务后重试','model':model,'text':'','tokens':data.get('usage')}
            content='\n'.join(c.get('text','') for item in data.get('output',[]) if item.get('type')=='message'
                              for c in item.get('content',[]) if c.get('type')=='output_text')
            reason=data.get('status','unknown')
        else:
            msg=data['choices'][0].get('message',{})
            content=msg.get('content') or ''
            if isinstance(content,list):
                content='\n'.join(x.get('text','') for x in content if isinstance(x,dict) and x.get('type')=='text')
            reason=data['choices'][0].get('finish_reason','unknown')
        text=content.strip() if isinstance(content,str) else ''
        if not text:
            return {'ok':False,'error':f'模型返回空文本（finish_reason={reason}），请缩短上下文或调整模型输出配置','model':data.get('model',model),'text':'','tokens':data.get('usage')}
        return {'ok':True,'error':'','model':data.get('model',model),'text':text,'tokens':data.get('usage'),
                'provider':provider,'response_id':data.get('id','')}
    except requests.Timeout:
        return {'ok':False,'error':'请求超时，请检查模型服务或稍后重试','model':model,'text':'','tokens':None}
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        return {'ok':False,'error':'模型响应异常：'+type(exc).__name__,'model':model,'text':'','tokens':None}
