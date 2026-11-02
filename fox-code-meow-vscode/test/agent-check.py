import sys,tempfile,json,threading
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from agent_hub import AgentHub,ROLES
from http.server import HTTPServer,BaseHTTPRequestHandler
calls=[]
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));key=self.headers.get('Authorization');calls.append((key,body));self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'reply-'+key}}]}).encode())
server=HTTPServer(('127.0.0.1',0),H);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with tempfile.TemporaryDirectory() as tmp:
  hub=AgentHub(tmp,Path.cwd())
  for r in ROLES:hub.configure(r,f'http://127.0.0.1:{server.server_port}/v1','mock','role-key-'+r)
  assert not calls
  result=hub.run('检查地图项目',['developer','gis']);assert len(result['results'])==4
  assert [c[0] for c in calls]==['Bearer role-key-'+r for r in ['coordinator','developer','gis','reviewer']]
  assert 'reply-Bearer role-key-coordinator' in calls[1][1]['messages'][-1]['content']
  courses=Path(tmp)/'gis-courses';courses.mkdir();(courses/'lab3.json').write_text(json.dumps({'id':'lab3','title':'海洋叠加实验','text':'最终水位515米，不能混用示例505米。'}),'utf-8')
  count=len(calls);assert hub.courses()[0]['id']=='lab3' and len(calls)==count
  trained=hub.run('请规划洪水损失计算',['gis'],course_id='lab3');assert trained['course']=='lab3'
  assert all('最终水位515米' in c[1]['messages'][-1]['content'] for c in calls[count:])
  try:hub.course_context('../private');raise AssertionError('unsafe course accepted')
  except ValueError:pass
  result=hub.run('停止测试',['developer'],lambda role,state:hub.stop() if state=='completed' else None);assert result['stopped'] and len(result['results'])==1
 print('PASS agent isolated keys, role handoff, skill loading, manual start, stop subsequent requests')
finally:server.shutdown()
