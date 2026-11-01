import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from admin import install

class AdminTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'upstream').mkdir()
        self.db=self.root/'upstream/database.db'
        with sqlite3.connect(self.db) as db:
            db.execute('create table tiku(question text primary key, answer text)')
            db.execute('create table tiku_detail(question text primary key,title text,options text)')
        db.close()
        app=Flask(__name__);app.secret_key='test-only';install(app,self.root,{})
        self.client=app.test_client()
        self.env=patch.dict(os.environ,{'FOX_ADMIN_PASSWORD':'test-admin-password'});self.env.start()
    def tearDown(self):
        self.env.stop();self.temp.cleanup()
    def login(self):
        return self.client.post('/api/admin/login',json={'password':'test-admin-password'})
    def test_auth_and_disabled(self):
        self.assertEqual(self.client.get('/api/admin/questions').status_code,401)
        self.assertEqual(self.client.post('/api/admin/login',json={'password':'wrong'}).status_code,401)
        with patch.dict(os.environ,{'FOX_ADMIN_PASSWORD':''}):self.assertEqual(self.login().status_code,503)
    def test_crud_export_import(self):
        self.assertEqual(self.login().status_code,200)
        row={'question':'q1','answer':'a1,a2','title':'测试题'}
        self.assertTrue(self.client.post('/api/admin/save',json=row).json['ok'])
        self.assertEqual(self.client.get('/api/admin/questions?q=测试').json['total'],1)
        exported=self.client.get('/api/admin/export').json
        self.assertEqual(exported,[row])
        self.client.post('/api/admin/delete',json={'question':'q1'})
        self.assertEqual(self.client.get('/api/admin/questions').json['total'],0)
        self.assertEqual(self.client.post('/api/admin/import',json=exported).json['count'],1)
        self.client.post('/api/admin/logout',json={})
        self.assertEqual(self.client.get('/api/admin/export').status_code,401)
    def test_atomic_import_and_input_validation(self):
        self.login()
        valid={'question':'q1','answer':'a1','title':'test'}
        self.assertEqual(self.client.post('/api/admin/import',json=[valid,{}]).status_code,400)
        self.assertEqual(self.client.get('/api/admin/questions').json['total'],0)
        self.assertEqual(self.client.post('/api/admin/import',json=[valid,valid]).status_code,400)
        self.assertEqual(self.client.get('/api/admin/questions?page=abc').status_code,400)

if __name__=='__main__': unittest.main()
