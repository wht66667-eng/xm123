import tempfile, importlib.util, json, time
from pathlib import Path
import sys
sys.path.insert(0,str(Path("desktop").resolve()))
spec=importlib.util.spec_from_file_location('fox_pet',Path('desktop/pet.py').resolve());mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as temp:
    mod.DATA=Path(temp);mod.STATE=mod.DATA/'pet.json'
    pet=mod.Pet();pet.root.withdraw();pet.root.update()
    pet.pat();assert json.loads(mod.STATE.read_text('utf-8'))['pats']==1
    pet.feed();assert '小鱼干' in pet.message.get()
    pet.sleep();assert pet.sleeping
    pet.toggle_motion();assert pet.reduce_motion
    pet.toggle_quiet();assert pet.quiet
    pet.toggle_quiet()
    (mod.DATA/'learning.json').write_text(json.dumps({'at':time.time()*1000,'status':'测试：正在讲解代码'}),'utf-8')
    pet.next_sync=0;pet.tick();assert '正在讲解代码' in pet.message.get()
    pet.focus_minutes=1;pet.focus_end=time.monotonic()-1;pet.tick();assert pet.state['focusMinutes']==1
    pet.close()
    pet=mod.Pet();pet.root.withdraw();assert pet.state['pats']==1 and pet.state['focusMinutes']==1;pet.close()
print('Desktop checks passed: interactions, state sync, focus completion, persistence, reduced motion, quiet mode')
