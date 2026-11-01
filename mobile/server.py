from pathlib import Path
import hashlib
import json
import re
import secrets
import sqlite3
import time
import requests
from flask import Flask, request, jsonify, session, send_from_directory, Response

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder='web', static_url_path='')
app.secret_key = secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict', MAX_CONTENT_LENGTH=1024*1024)
BASE = 'https://mars.mycourse.cn/marsapi/api/'
clients = {}
raw = (ROOT/'answer.js').read_text(encoding='utf-8-sig')
bank = json.loads(re.search(r'const answers\s*=\s*({.*?});', raw, re.S)[1].rstrip().replace(',\n}', '\n}'))

def client():
    key = session.get('sid')
    if key not in clients:
        key = secrets.token_urlsafe(32)
        session['sid'] = key
        clients[key] = requests.Session()
    return clients[key]

def remote(path, data=None):
    r = client().post(BASE+path, data=data or {}, timeout=25)
    r.raise_for_status()
    return r.json()

@app.errorhandler(Exception)
def error(exc):
    from werkzeug.exceptions import HTTPException
    if isinstance(exc, HTTPException):
        return jsonify(error=exc.description), exc.code
    return jsonify(error='请求失败，请检查网络或平台返回格式。'), 502

@app.before_request
def same_origin():
    if request.method == 'POST' and request.headers.get('Origin'):
        from urllib.parse import urlparse
        if urlparse(request.headers['Origin']).netloc != request.host:
            return jsonify(error='来源不匹配'), 403

@app.get('/')
def home():
    return app.send_static_file('index.html')

@app.get('/api/library')
def library():
    q = request.args.get('q', '').strip().lower()
    source = request.args.get('source', 'all')
    rows = []
    if source in ('all', 'script'):
        rows += [dict(title=k, answer=v, source='页面脚本', kind='选项字母') for k,v in bank.items() if q in k.lower()]
    with sqlite3.connect(ROOT/'upstream/database.db') as db:
        count = db.execute('select count(*) from tiku').fetchone()[0]
        if source in ('all', 'github'):
            for ident, answer, title, options in db.execute('select t.question,t.answer,d.title,d.options from tiku t left join tiku_detail d on t.question=d.question'):
                if q in (str(title or '')+' '+ident).lower():
                    rows.append(dict(title=title or ('题目 ID：'+ident),answer=answer,source='GitHub 题库',kind='平台选项 ID'))
    return jsonify(items=rows[:100], total=len(rows), scriptCount=len(bank), githubCount=count)

@app.get('/api/schools')
def schools():
    return jsonify(remote('login/v1/listTenant'))

@app.get('/api/captcha')
def captcha():
    stamp = str(int(time.time()*1000))
    session['stamp'] = stamp
    r = client().get(BASE+'login/v1/getCaptcha', params={'timestamp':stamp}, timeout=25)
    r.raise_for_status()
    return Response(r.content, content_type=r.headers.get('Content-Type','image/png'), headers={'Cache-Control':'no-store'})

@app.post('/api/login')
def login():
    d = request.get_json()
    result = remote('login/v1/login',dict(tenantCode=d['school'],username=d['username'],encryptedPassword=hashlib.md5(d['password'].encode()).hexdigest().upper(),captchaCode=d['captcha'],timestamp=session.get('stamp','')))
    token = result.get('data',{}).get('result',{}).get('token')
    if token:
        client().headers.update({'Authorization':token,'Origin':'https://mars.mycourse.cn','Referer':'https://mars.mycourse.cn/deimos/'})
        client().cookies.set('mars_token', token, domain='mars.mycourse.cn')
        session['authenticated'] = True
    return jsonify(result)

@app.post('/api/logout')
def logout():
    c = clients.pop(session.get('sid'),None)
    if c: c.close()
    session.clear()
    return jsonify(ok=True)

@app.post('/api/platform/<action>')
def platform(action):
    if not session.get('authenticated'): return jsonify(error='请先登录'),401
    d = request.get_json() or {}
    if action == 'activities': return jsonify(remote('study/project/v1/index'))
    if action not in ('preparePaper','startPaper','getNear','recordQuestion','submitPaper'):
        return jsonify(error='未知操作'),400
    mode = d.pop('mode','exam')
    if mode not in ('exam','practice'): return jsonify(error='未知模式'),400
    result = remote(f'study/activity/{mode}/v1/{action}',d)
    if action in ('getNear','startPaper'):
        questions = result.get('data',{}).get('result',{}).get('questionList',[])
        with sqlite3.connect(ROOT/'upstream/database.db') as db:
            for question in questions:
                ids = ','.join(str(o['id']) for o in question.get('optionList',[]) if o.get('isCorrect') == 1)
                row = db.execute('select answer from tiku where question=?',(question['id'],)).fetchone()
                question['foxAnswer'] = ids or (row[0] if row else '')
                if ids:
                    db.execute('insert or replace into tiku(question,answer) values(?,?)',(question['id'],ids))
                    db.execute('insert or replace into tiku_detail(question,title,options) values(?,?,?)',(question['id'],question.get('title',''),json.dumps(question.get('optionList',[]),ensure_ascii=False)))
    return jsonify(result)

@app.get('/adapter.js')
def adapter():
    return send_from_directory(ROOT/'web','adapter.js',as_attachment=True,download_name='fox-answer.js')

from xg import install
install(app, client)
from admin import install as install_admin
install_admin(app, ROOT, bank)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5080,debug=False)
