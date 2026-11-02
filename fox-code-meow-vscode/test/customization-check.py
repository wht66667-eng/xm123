import sys,tempfile,json
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path('desktop').resolve()))
from skins import SkinStore
from obsidian_bridge import Vault
from assistant import Library
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);data=root/'data';data.mkdir();vault=root/'vault';vault.mkdir();note=vault/'note.md';note.write_text('Python函数 return 返回结果','utf-8');hidden=vault/'.obsidian';hidden.mkdir();(hidden/'private.md').write_text('should not import','utf-8')
 v=Vault(data);v.connect(vault);assert v.sync(Library(data/'kb'))[0]==1;assert note.read_text('utf-8').startswith('Python')
 store=SkinStore(data/'skins');folder=store.import_atlas('assets/foxgirl-atlas.png',6);frames,fps=store.load(folder);assert len(frames['idle'])==6;assert fps==8
 print('PASS custom atlas import, declarative skin load, Obsidian local import and hidden-settings exclusion')
