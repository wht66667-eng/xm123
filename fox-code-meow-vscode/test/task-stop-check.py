import sys,tempfile,threading,time,json
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from arcmap_bridge import ArcMap
from optimizer import Optimizer
from task_journal import TaskJournal
with tempfile.TemporaryDirectory() as tmp:
 journal=TaskJournal(tmp);bridge=ArcMap();errors=[]
 def work():
  try:journal.run('cancel ArcPy',{},lambda:bridge.execute('detect'))
  except Exception as e:errors.append(str(e))
 t=threading.Thread(target=work);t.start();deadline=time.monotonic()+10
 while bridge.process is None and time.monotonic()<deadline:time.sleep(.01)
 assert bridge.process is not None;bridge.cancel();t.join(10);assert not t.is_alive() and errors and 'stopped' in errors[0].lower()
 assert json.loads(next(Path(tmp).glob('*.json')).read_text('utf-8'))['status']=='stopped'
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);source=root/'original';(source/'test').mkdir(parents=True);(source/'desktop').mkdir();(source/'src').mkdir();(source/'package.json').write_text('{"name":"fox-code-meow"}')
 (source/'test/slow.test.cjs').write_text("const{test}=require('node:test');test('long',async()=>await new Promise(r=>setTimeout(r,30000)));")
 runner=Optimizer(root/'app');run=runner.snapshot(source);result=[];t=threading.Thread(target=lambda:result.append(runner.check(run)));t.start();deadline=time.monotonic()+10
 while runner.process is None and time.monotonic()<deadline:time.sleep(.01)
 assert runner.process is not None;runner.stop();t.join(10);assert not t.is_alive() and result[0]['stopped'] and not result[0]['passed'];assert (run/'SKILL.md').is_file()
print('PASS live ArcPy cancellation, stopped audit record, Node process-tree cancellation, development skill draft')
