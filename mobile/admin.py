# Copyright (c) 2026 fox. SPDX-License-Identifier: MIT
"""fox authenticated question-bank administration. Disabled without FOX_ADMIN_PASSWORD."""
import os
import secrets
import sqlite3
import json
from contextlib import contextmanager
from flask import request, jsonify, session, send_from_directory

def install(app, root, script_bank):
    @contextmanager
    def connection():
        db=sqlite3.connect(root/'upstream/database.db')
        try:
            with db: yield db
        finally: db.close()

    def validate(row):
        q=str(row.get('question','')).strip(); answer=str(row.get('answer','')).strip()
        title=str(row.get('title','')).strip()
        if not q or not answer or len(q)>300 or len(answer)>3000 or len(title)>10000:
            raise ValueError('题目 ID 和答案必填，长度须符合限制')
        return q,answer,title

    @app.get('/admin')
    def admin_home():
        return send_from_directory(root/'web','admin.html')

    @app.before_request
    def protect_admin():
        if not request.path.startswith('/api/admin'): return
        if not os.environ.get('FOX_ADMIN_PASSWORD'):
            return jsonify(error='管理端未启用，请设置 FOX_ADMIN_PASSWORD 后重启服务'),503
        if request.path!='/api/admin/login' and not session.get('fox_admin'):
            return jsonify(error='请先登录管理端'),401

    @app.post('/api/admin/login')
    def admin_login():
        data=request.get_json() or {}
        password=str(data.get('password',''))
        if not secrets.compare_digest(password.encode(),os.environ['FOX_ADMIN_PASSWORD'].encode()):
            return jsonify(error='管理密码错误'),401
        session['fox_admin']=True
        return jsonify(ok=True)

    @app.post('/api/admin/logout')
    def admin_logout():
        session.pop('fox_admin',None)
        return jsonify(ok=True)

    @app.get('/api/admin/environment')
    def admin_environment():
        import platform
        import importlib.metadata
        return jsonify(Python=platform.python_version(),system=platform.system(),Flask=importlib.metadata.version('Flask'),databaseExists=(root/'upstream/database.db').exists(),configExists=__import__('fox_config').config_path().exists(),host=os.environ.get('FOX_HOST','127.0.0.1'),port=os.environ.get('FOX_PORT','5080'),requestTimeout=os.environ.get('FOX_REQUEST_TIMEOUT','25'),signature='Copyright (c) 2026 fox · MIT License')

    @app.get('/api/admin/questions')
    def admin_questions():
        query=request.args.get('q','').strip()
        try: page=max(0,int(request.args.get('page',0)))
        except ValueError: return jsonify(error='页码必须是整数'),400
        pattern='%'+query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        where="where t.question like ? escape '\\' or coalesce(d.title,'') like ? escape '\\'"
        join='from tiku t left join tiku_detail d on t.question=d.question '
        with connection() as db:
            total=db.execute('select count(*) '+join+where,(pattern,pattern)).fetchone()[0]
            rows=db.execute('select t.question,t.answer,coalesce(d.title,\'\') '+join+where+' order by t.question limit 30 offset ?',(pattern,pattern,page*30)).fetchall()
            count=db.execute('select count(*) from tiku').fetchone()[0]
        return jsonify(items=[dict(question=q,answer=a,title=t) for q,a,t in rows],total=total,page=page,githubCount=count,scriptCount=len(script_bank))

    @app.post('/api/admin/save')
    def admin_save():
        try: q,answer,title=validate(request.get_json() or {})
        except ValueError as e: return jsonify(error=str(e)),400
        with connection() as db:
            db.execute('insert into tiku(question,answer) values(?,?) on conflict(question) do update set answer=excluded.answer',(q,answer))
            db.execute('insert into tiku_detail(question,title,options) values(?,?,?) on conflict(question) do update set title=excluded.title',(q,title,'[]'))
        return jsonify(ok=True)

    @app.post('/api/admin/delete')
    def admin_delete():
        q=str((request.get_json() or {}).get('question',''))
        with connection() as db:
            deleted=db.execute('delete from tiku where question=?',(q,)).rowcount
            db.execute('delete from tiku_detail where question=?',(q,))
        return jsonify(ok=True,deleted=deleted)

    @app.get('/api/admin/export')
    def admin_export():
        with connection() as db:
            rows=db.execute("select t.question,t.answer,coalesce(d.title,'') from tiku t left join tiku_detail d on t.question=d.question order by t.question").fetchall()
        body=json.dumps([dict(question=q,answer=a,title=t) for q,a,t in rows],ensure_ascii=False,indent=2)
        return app.response_class(body,mimetype='application/json',headers={'Content-Disposition':'attachment; filename=fox-question-bank.json','Cache-Control':'no-store'})

    @app.post('/api/admin/import')
    def admin_import():
        rows=request.get_json()
        if not isinstance(rows,list) or len(rows)>5000:
            return jsonify(error='导入格式必须是最多5000条记录的 JSON 数组'),400
        try:
            if any(not isinstance(r,dict) for r in rows): raise ValueError('每条记录必须是对象')
            prepared=[validate(r) for r in rows]
            if len({r[0] for r in prepared})!=len(prepared): raise ValueError('导入文件内有重复题目 ID')
        except ValueError as e: return jsonify(error=str(e)),400
        with connection() as db:
            for q,a,t in prepared:
                db.execute('insert into tiku(question,answer) values(?,?) on conflict(question) do update set answer=excluded.answer',(q,a))
                db.execute('insert into tiku_detail(question,title,options) values(?,?,?) on conflict(question) do update set title=excluded.title',(q,t,'[]'))
        return jsonify(ok=True,count=len(prepared))
