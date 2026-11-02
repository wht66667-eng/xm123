"""Explicit bounded local computer tasks, no generated shell commands."""
from pathlib import Path
import os,hashlib,threading
class ComputerTasks:
    def __init__(self):self.stopped=threading.Event()
    def stop(self):self.stopped.set()
    def inspect_folder(self,value):
        root=Path(value).resolve()
        if not root.is_dir():raise ValueError('请选择文件夹')
        self.stopped.clear();items=[]
        for base,dirs,files in os.walk(root,followlinks=False):
            dirs[:]=[d for d in dirs if d not in ('.git','node_modules','.venv') and not Path(base,d).is_symlink()]
            for name in files:
                if self.stopped.is_set():return {'stopped':True,'items':items}
                p=Path(base,name)
                if p.is_symlink():continue
                try:items.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size})
                except OSError:continue
                if len(items)>=500:return {'stopped':False,'limited':True,'items':items}
        return {'stopped':False,'items':items}
    def open_folder(self,value):
        root=Path(value).resolve()
        if not root.is_dir():raise ValueError('请选择已有文件夹')
        os.startfile(str(root));return {'opened':str(root)}
