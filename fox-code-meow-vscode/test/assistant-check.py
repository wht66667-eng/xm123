import sys,tempfile,json,threading
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from assistant import Library,endpoint,save_config,ask
from http.server import HTTPServer,BaseHTTPRequestHandler
with tempfile.TemporaryDirectory() as tmp:
 r=Path(tmp);source=r/'source';source.mkdir();p=source/'hello.md';p.write_text('Python函数使用def定义。api_key=private-value','utf-8')
 lib=Library(r/'kb');assert lib.ingest([p])[0]==1;hits=lib.search('Python函数');assert hits and 'private-value' not in hits[0][2]
 try:lib.delete([p]);raise AssertionError('original deletion allowed')
 except ValueError:pass
 lib.delete(lib.documents());assert p.exists() and not lib.documents()
 calls=[]
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def do_POST(self):
   calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))));self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'本机模拟回答'}}]}).encode())
 server=HTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 save_config(r,f'http://127.0.0.1:{server.server_port}/v1','mock','test-only-not-a-real-key');assert not calls
 cfg=(r/'desktop-ai.json').read_text();assert 'test-only-not-a-real-key' not in cfg
 assert ask(r,'问题','本地片段')=='本机模拟回答';assert len(calls)==1
 server.shutdown()
 for url in ['http://example.com','https://user:pass@example.com','https://example.com?key=x']:
  try:endpoint(url);raise AssertionError('bad URL allowed')
  except ValueError:pass
print('PASS desktop assistant: import/search/redaction, original protection, encrypted key, explicit local mock request, endpoint validation')
