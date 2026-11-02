"""Process-isolated ArcMap adapter. No code strings from a model are executed."""
import json,subprocess,tempfile,threading,os,sys
from pathlib import Path
from process_control import terminate_owned
class ArcMap:
    def __init__(self,root=None):
        self.python=Path(r'C:\Python27\ArcGIS10.8\python.exe');self.executable=Path(r'C:\Program Files (x86)\ArcGIS\Desktop10.8\bin\ArcMap.exe')
        self.root=Path(root or getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]));self.process=None;self.cancelled=threading.Event()
    def launch(self,mxd=None):
        if not self.executable.exists():raise ValueError('ArcMap executable not found')
        args=[str(self.executable)]
        if mxd:
            p=Path(mxd).resolve()
            if not p.is_file() or p.suffix.lower()!='.mxd':raise ValueError('Select an existing MXD')
            args.append(str(p))
        subprocess.Popen(args,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        return 'ArcMap launch requested'
    def cancel(self):
        self.cancelled.set()
        terminate_owned(self.process)
    def execute(self,action,**params):
        if action not in ('detect','inspect_mxd','export_pdf','copy_mxd','inspect_dataset','buffer','multiple_ring_buffer','union','intersect','identity','update','erase','symdiff'):raise ValueError('Unsupported ArcMap action')
        if not self.python.exists():raise ValueError('ArcMap Python 2.7 not found')
        self.cancelled.clear()
        with tempfile.TemporaryDirectory(prefix='fox-arcmap-') as tmp:
            request=Path(tmp)/'request.json';result=Path(tmp)/'result.json';request.write_text(json.dumps(dict(action=action,**params),ensure_ascii=True),'utf-8')
            self.process=subprocess.Popen([str(self.python),str(self.root/'integrations/arcmap_worker.py'),str(request),str(result)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:log=self.process.communicate(timeout=180)[0]
            except subprocess.TimeoutExpired:terminate_owned(self.process);self.process.communicate();raise ValueError('ArcMap task timed out')
            if self.cancelled.is_set():raise ValueError('ArcMap task stopped; inspect any partially written output')
            if not result.exists():raise ValueError('ArcMap worker did not return a result')
            data=json.loads(result.read_text('utf-8'))
            if not data.get('ok'):raise ValueError(data.get('error','ArcMap task failed'))
            return data['result']
