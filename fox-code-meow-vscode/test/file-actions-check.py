import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from file_actions import delete_original,validate_target
with tempfile.TemporaryDirectory(dir=Path.cwd()/'test-artifacts') as t:
 p=Path(t)/'sample';p.mkdir();(p/'a.txt').write_text('test');delete_original(p,True);assert not p.exists()
 try:validate_target(Path.home());raise AssertionError()
 except ValueError:pass
print('PASS original deletion fixture and protected-home rejection')
