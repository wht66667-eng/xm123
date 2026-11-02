import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from arcmap_bridge import ArcMap
result=ArcMap().execute('detect');assert result['install']['Version']=='10.8';print(json.dumps({'arcmapVersion':result['install']['Version'],'license':result['license']}))
