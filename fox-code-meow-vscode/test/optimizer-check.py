import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from optimizer import Optimizer
with tempfile.TemporaryDirectory() as tmp:
 o=Optimizer(tmp);run=o.snapshot(Path.cwd());assert (run/'source/src/extension.cjs').is_file();candidate=run/'source/src/core.cjs';original=candidate.read_text('utf-8');o.apply_candidate(run,[{'path':'src/core.cjs','content':original+'\n// test candidate\n'}]);assert candidate.read_text('utf-8')!=original;assert o.restore(run)==1;assert candidate.read_text('utf-8')==original;report=o.check(run);assert report['passed'],report
 try:o.apply_candidate(run,[{'path':'../escape.py','content':'bad'}]);raise AssertionError()
 except ValueError:pass
 for relative in ['integrations/arcmap_worker.py','assets/providers.json','package.json','test/core.test.cjs']:
  path=run/'source'/relative;old=path.read_bytes();path.write_bytes(old+b'\n')
  try:o.build(run);raise AssertionError('stale checks accepted: '+relative)
  except ValueError as e:assert '检查' in str(e)
  finally:path.write_bytes(old)
 print('PASS isolated snapshot, unchanged source, bounded candidate paths, Node/Python checks')
