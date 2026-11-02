import sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from arcmap_bridge import ArcMap
source=Path(r'C:\Program Files (x86)\ArcGIS\Desktop10.8\Templates\ExportWebMapTemplates\Letter ANSI A Landscape.mxd')
bridge=ArcMap();details=bridge.execute('inspect_mxd',mxd=str(source));assert 'frames' in details
with tempfile.TemporaryDirectory(dir=Path('test-artifacts').resolve()) as temp:
 root=Path(temp);copy=bridge.execute('copy_mxd',mxd=str(source),output=str(root/'copy.mxd'));assert copy['bytes']>0
 pdf=bridge.execute('export_pdf',mxd=str(source),output=str(root/'map.pdf'));assert pdf['bytes']>0
 print(json.dumps({'inspect':True,'copyBytes':copy['bytes'],'pdfBytes':pdf['bytes'],'sourceUnchanged':True}))
