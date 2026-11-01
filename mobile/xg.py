from fox_config import read_int
"""Reimplemented HTML form bridge based on static EXE inspection; never executes EXE code."""
import re
import requests
from urllib.parse import urljoin, urlparse, urlencode
from bs4 import BeautifulSoup
from flask import request, jsonify, session, Response

BASE='http://xg.jszjztc.com'

def install(app, client):
    states={}
    def valid(url):
        url=urljoin(BASE,url)
        p=urlparse(url)
        if p.hostname!='xg.jszjztc.com' or p.scheme not in ('http','https') or p.port not in (None,80,443):
            raise ValueError('站点地址不受支持')
        return url

    def parse(response,old):
        if 'pdf' in response.headers.get('Content-Type','').lower():
            return Response(response.content,content_type='application/pdf',headers={'Content-Disposition':'attachment; filename=fox-certificate.pdf'})
        html=response.content.decode('gb18030',errors='replace')
        soup=BeautifulSoup(html,'html.parser')
        for el in soup(['script','style','noscript']): el.decompose()
        forms=[]
        for f in soup.find_all('form'):
            fields=[]
            for el in f.find_all(['input','select','textarea']):
                name=el.get('name')
                if not name: continue
                typ=el.get('type','text').lower() if el.name=='input' else el.name
                val=el.get('value','') if el.name=='input' else el.get_text() if el.name=='textarea' else (el.find('option',selected=True) or el.find('option')).get('value','') if el.find('option') else ''
                fields.append(dict(name=name,type=typ,value=val,checked=el.has_attr('checked'),label=(el.find_next_sibling(string=True) or name).strip()[:180],options=[dict(value=o.get('value',o.get_text()),label=o.get_text(' ',strip=True)) for o in el.find_all('option')]))
            forms.append(dict(action=valid(urljoin(response.url,f.get('action') or response.url)),fields=fields))
        links=[]
        for a in soup.find_all('a',href=True):
            href=a['href']; label=a.get_text(' ',strip=True)
            if not label: continue
            post=re.search(r"__doPostBack\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]*)",href)
            if post: links.append(dict(label=label,event=post.group(1),argument=post.group(2))); continue
            try: url=valid(urljoin(response.url,href))
            except ValueError: continue
            if not href.startswith(('javascript:','#')): links.append(dict(label=label,url=url))
        text=soup.get_text(' ',strip=True)
        old.update(url=response.url,forms=forms)
        old.setdefault('bank',{})
        answer=re.search(r'参考答案[：:]\s*([A-F正确错误对错、,，\s]+)',text)
        if answer:
            title=re.search(r'\d+\.(.+?)参考答案',text)
            if title: old['bank'][title.group(1).strip()]=answer.group(1).strip()
        return jsonify(text=text[:40000],forms=forms,links=links[:200],url=response.url,bankCount=len(old['bank']))

    @app.post('/api/xg')
    def bridge():
        client(); sid=session['sid']; old=states.setdefault(sid,{})
        if 'client' not in old: old['client']=requests.Session()
        c=old['client']
        d=request.get_json() or {}
        if d.get('op')=='bank': return jsonify(bank=old.get('bank',{}))
        if d.get('op')=='submit':
            forms=old.get('forms',[]); index=int(d.get('index',0))
            if index<0 or index>=len(forms): return jsonify(error='请先加载页面'),400
            form=forms[index]; allowed={f['name'] for f in form['fields']}
            values={k:v for k,v in d.get('values',{}).items() if k in allowed or k in ('__EVENTTARGET','__EVENTARGUMENT','ImageButton1.x','ImageButton1.y')}
            body=urlencode(values,doseq=True,encoding='gbk',errors='strict')
            r=c.post(form['action'],data=body,headers={'Content-Type':'application/x-www-form-urlencoded'},timeout=read_int("FOX_REQUEST_TIMEOUT",25,5,120),allow_redirects=False)
        else:
            r=c.get(valid(d.get('url','/login.aspx')),timeout=read_int("FOX_REQUEST_TIMEOUT",25,5,120),allow_redirects=False)
        for _ in range(5):
            if not r.is_redirect: break
            r=c.get(valid(urljoin(r.url,r.headers['Location'])),timeout=read_int("FOX_REQUEST_TIMEOUT",25,5,120),allow_redirects=False)
        r.raise_for_status()
        return parse(r,old)
