import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from pet import Pet
p=Pet();p.open_assistant();p.root.after(45000,p.close);p.run()
