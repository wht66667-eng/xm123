"""Read-only Obsidian Markdown import into the fox private library."""
from pathlib import Path
import os,json
from assistant import Library
class Vault:
    def __init__(self,data):self.data=Path(data);self.settings=self.data/'obsidian-vault.json'
    def connect(self,folder):
        root=Path(folder).resolve()
        if not root.is_dir() or root.is_symlink():raise ValueError('请选择本机Obsidian仓库文件夹')
        self.settings.write_text(json.dumps({'folder':str(root)},ensure_ascii=False),'utf-8');return root
    def sync(self,library):
        root=Path(json.loads(self.settings.read_text('utf-8'))['folder']).resolve()
        def files():
            count=0
            for base,dirs,names in os.walk(root,followlinks=False):
                dirs[:]=[d for d in dirs if not d.startswith('.') and d not in ('node_modules','attachments') and not Path(base,d).is_symlink()]
                for name in names:
                    if count>=1000:return
                    if name.lower().endswith('.md'):count+=1;yield Path(base,name)
        return library.ingest(files())
