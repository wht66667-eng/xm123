import unittest
from unittest.mock import patch
import server

class Tests(unittest.TestCase):
    def setUp(self):
        self.c=server.app.test_client()

    def test_static_and_library(self):
        for url in ('/','/app.js','/style.css','/adapter.js'):
            with self.c.get(url) as response:
                self.assertEqual(response.status_code,200)
        data=self.c.get('/api/library?source=script&q=涉密计算机').json
        self.assertGreater(data['total'],0)
        self.assertEqual(data['items'][0]['source'],'页面脚本')
        self.assertEqual(self.c.get('/api/library?q=NONEXISTENT-fox-987').json['total'],0)
        self.assertGreater(self.c.get('/api/library?source=github').json['githubCount'],0)

    def test_write_boundary(self):
        self.assertEqual(self.c.post('/api/platform/submitPaper',json={}).status_code,401)
        self.assertEqual(self.c.post('/api/login',json={},headers={'Origin':'https://other.invalid'}).status_code,403)

    @patch('server.remote')
    def test_mock_platform_flow(self,remote):
        remote.return_value={'success':True,'data':{'result':{'token':'test-only'}}}
        self.assertTrue(self.c.post('/api/login',json={'school':'test','username':'test','password':'not-real','captcha':'1234'}).json['success'])
        self.assertEqual(self.c.post('/api/platform/unknown',json={}).status_code,400)
        for action in ('activities','preparePaper','recordQuestion','submitPaper'):
            remote.return_value={'code':200,'data':{'result':{'score':88}}}
            self.assertEqual(self.c.post('/api/platform/'+action,json={'mode':'exam','userActivityId':'mock'}).status_code,200)
        remote.return_value={'code':200,'data':{'result':{'questionList':[{'id':'mock-unmatched','title':'test','optionList':[]}]}}}
        result=self.c.post('/api/platform/startPaper',json={'mode':'exam','userActivityId':'mock'}).json
        self.assertEqual(result['data']['result']['questionList'][0]['foxAnswer'],'')
        self.assertTrue(self.c.post('/api/logout',json={}).json['ok'])
        self.assertEqual(self.c.post('/api/platform/activities',json={}).status_code,401)

    @patch('xg.requests.Session')
    def test_xg_form_gbk_and_pdf(self,Session):
        from requests import Response
        c=Session.return_value
        page=Response();page.status_code=200;page.url='http://xg.jszjztc.com/login.aspx';page._content="<form action='/login.aspx'><input name='__VIEWSTATE' type='hidden' value='state'><input name='LoginID'><input name='UserPwd' type='password'><input name='judge' value='正确'><input type='submit' name='submit' value='登录'></form>".encode('gbk')
        c.get.return_value=page
        result=self.c.post('/api/xg',json={}).json
        self.assertEqual(len(result['forms']),1)
        c.post.return_value=page
        self.c.post('/api/xg',json={'op':'submit','values':{'judge':'正确','__VIEWSTATE':'state'}})
        self.assertIn('%D5%FD%C8%B7',c.post.call_args.kwargs['data'])
        pdf=Response();pdf.status_code=200;pdf.url=page.url;pdf._content=b'%PDF-1.4 test';pdf.headers['Content-Type']='application/pdf';c.get.return_value=pdf
        self.assertEqual(self.c.post('/api/xg',json={}).content_type,'application/pdf')

if __name__=='__main__': unittest.main()
