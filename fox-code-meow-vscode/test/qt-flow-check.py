import sys,tempfile,json,time,threading
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from qt_assistant import AssistantWindow
from assistant import save_config
from http.server import HTTPServer,BaseHTTPRequestHandler
calls=[]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))));self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'fox本机模拟回复'}}]}).encode())
server=HTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
app=QApplication([])
try:
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);save_config(root,f'http://127.0.0.1:{server.server_port}/v1','mock','')
  window=AssistantWindow(None,root);window.show();app.processEvents();assert not calls
  window.question.setPlainText('测试气泡');window.send();deadline=time.monotonic()+5
  while window.busy and time.monotonic()<deadline:app.processEvents();QTest.qWait(20)
  assert not window.busy and len(calls)==1 and window.messages.count()==3
  assert calls[0]['messages'][-1]['content'].startswith('测试气泡')
  source=root/'lesson.md';source.write_text('Python return returns value','utf-8');window.import_paths([str(source)]);deadline=time.monotonic()+5
  while window.busy and time.monotonic()<deadline:app.processEvents();QTest.qWait(20)
  assert window.docs.count()==1 and source.exists()
  window.switch(1);window.grab().save('test-artifacts/lounge-docs-populated.png');window.switch(0);window.grab().save('test-artifacts/lounge-chat-tested.png');window.close()
 print('PASS native UI send -> local mock -> reply bubble; local document import -> real document row')
finally:server.shutdown()
