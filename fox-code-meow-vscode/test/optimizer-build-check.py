import sys,tempfile,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from optimizer import Optimizer
source=Path.cwd();before=hashlib.sha256((source/'src/core.cjs').read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='fox-build-test-') as tmp:
 runner=Optimizer(tmp);run=runner.snapshot(source);assert runner.check(run)['passed'];result=runner.build(run);assert Path(result['vsix']).is_file() and Path(result['exe']).is_file();assert hashlib.sha256((source/'src/core.cjs').read_bytes()).hexdigest()==before
 Path('test-artifacts/optimizer-build-result.json').write_text(json.dumps({'ok':True,'candidateBuild':True,'sourceUnchanged':True}),'utf-8')
 print('PASS real candidate EXE build, frozen self-test, VSIX build, original unchanged',flush=True)
