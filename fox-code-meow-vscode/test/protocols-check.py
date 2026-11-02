import sys,tempfile,json,threading
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from assistant import ask,save_config
from http.server import HTTPServer,BaseHTTPRequestHandler
calls=[]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));calls.append((self.path,dict(self.headers),body))
  if self.path.endswith('/responses'):response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'正确回答'}]}]}
  elif self.path.endswith('/messages'):response={'content':[{'type':'text','text':'正确回答'}]}
  else:response={'choices':[{'message':{'content':'正确回答'}}]}
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps(response).encode())
server=HTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with tempfile.TemporaryDirectory() as temp:
  for kind,path in [('chat','chat/completions'),('responses','responses'),('messages','messages')]:
   count=len(calls);save_config(temp,f'http://127.0.0.1:{server.server_port}/v1','mock','local-test-key',kind);assert len(calls)==count
   assert ask(temp,'测试')=='正确回答';assert len(calls)==count+1;url,headers,body=calls[-1];assert url=='/v1/'+path
   if kind=='responses':assert 'input' in body and 'messages' not in body
   if kind=='messages':assert body['system'] and len(body['messages'])==1 and {k.lower():v for k,v in headers.items()}.get('x-api-key')=='local-test-key'
 print('PASS all 3 desktop protocol schemas, credentials, responses and zero calls on save')
finally:server.shutdown()
