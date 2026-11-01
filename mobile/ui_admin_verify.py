"""Isolated admin UI QA: temporary database, no real questions modified."""
import os
import shutil
import sqlite3
import tempfile
import threading
from pathlib import Path
from flask import Flask
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from admin import install

os.environ['FOX_ADMIN_PASSWORD']='local-ui-test-only'
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp);(root/'upstream').mkdir()
    shutil.copytree(Path(__file__).parent/'web',root/'web')
    db=sqlite3.connect(root/'upstream/database.db')
    db.executescript('create table tiku(question text primary key,answer text);create table tiku_detail(question text primary key,title text,options text);');db.close()
    app=Flask(__name__,static_folder=str(root/'web'),static_url_path='');app.secret_key='test-only'
    install(app,root,{})
    server=make_server('127.0.0.1',5081,app,threaded=True)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={'width':1280,'height':900});errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto('http://127.0.0.1:5081/admin',wait_until='networkidle')
            page.locator('#adminPassword').fill('local-ui-test-only');page.locator('#adminLogin button').click()
            page.locator('#workspace').wait_for(state='visible')
            page.locator('#question').fill('test-001');page.locator('#title').fill('管理端测试题目');page.locator('#answer').fill('option-a')
            page.locator('#editor button[type=submit], #editor button:not([type])').click()
            page.get_by_text('管理端测试题目',exact=True).wait_for()
            Path('screenshots').mkdir(exist_ok=True);page.screenshot(path='screenshots/admin-desktop.png',full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.locator('body').evaluate('e=>e.scrollWidth<=innerWidth')
            page.screenshot(path='screenshots/admin-mobile.png',full_page=True)
            page.on('dialog',lambda d:d.accept())
            page.get_by_role('button',name='删除',exact=True).click()
            page.get_by_text('没有匹配的题目。',exact=True).wait_for()
            page.locator('#logout').click();page.locator('#adminLogin').wait_for(state='visible')
            assert not errors,errors
            browser.close()
    finally: server.shutdown()
print('Admin UI verified: login, save, delete, logout, desktop/mobile layout')
