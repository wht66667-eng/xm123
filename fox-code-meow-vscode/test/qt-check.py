import sys
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from qt_pet import run
run(Path('test-artifacts/transparent-pet.png').resolve())
print('PASS native Qt transparent frameless render and event loop')
