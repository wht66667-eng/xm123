"""Protocol translation for explicit desktop requests. MIT fox."""
import urllib.parse
SUFFIX={'chat':'/chat/completions','responses':'/responses','messages':'/messages'}
def resolve(base,protocol='auto'):
    u=urllib.parse.urlsplit(base.strip())
    if u.username or u.password or u.query or u.fragment or not u.hostname:raise ValueError('接口地址格式不正确')
    if u.scheme!='https' and not (u.scheme=='http' and u.hostname in ('localhost','127.0.0.1','::1')):raise ValueError('远程接口需要HTTPS；HTTP仅允许本机')
    path=u.path.rstrip('/');old=next((k for k,s in SUFFIX.items() if path.endswith(s)),None)
    kind=old or 'chat' if protocol=='auto' else protocol
    if kind not in SUFFIX:raise ValueError('不支持的API协议')
    if old:path=path[:-len(SUFFIX[old])]
    return urllib.parse.urlunsplit((u.scheme,u.netloc,path+SUFFIX[kind],'','')),kind

def spec(url,kind,model,key,messages,auth='auto',version='auto'):
    host=urllib.parse.urlsplit(url).hostname
    mode=('x-api-key' if kind=='messages' and host!='api.anthropic.com' else 'bearer') if auth=='auto' else auth
    headers={'Content-Type':'application/json'}
    if key:headers['x-api-key' if mode=='x-api-key' else 'Authorization']=key if mode=='x-api-key' else 'Bearer '+key
    if kind=='responses':body={'model':model,'input':messages,'max_output_tokens':4096,'stream':False,'store':False}
    elif kind=='messages':
        headers['anthropic-version']=('2026-10-21' if host=='api.anthropic.com' else '2023-06-01') if version=='auto' else version
        body={'model':model,'system':'\n'.join(m['content'] for m in messages if m['role']=='system'),'messages':[m for m in messages if m['role']!='system'],'max_tokens':4096,'stream':False}
    else:
        body={'model':model,'messages':messages,'stream':False}
        body['max_completion_tokens' if host=='api.openai.com' else 'max_tokens']=4096
        if host=='api.deepseek.com':body['thinking']={'type':'disabled'}
    return headers,body

def text(kind,data):
    if kind=='responses':
        if data.get('status')=='incomplete':raise ValueError('输出预算不足，回复未完成。请缩小问题后重试。')
        return data.get('output_text') or ''.join(c.get('text','') for o in data.get('output',[]) for c in o.get('content',[]) if c.get('type')=='output_text')
    if kind=='messages':return ''.join(c.get('text','') for c in data.get('content',[]) if c.get('type')=='text')
    return data.get('choices',[{}])[0].get('message',{}).get('content','')
