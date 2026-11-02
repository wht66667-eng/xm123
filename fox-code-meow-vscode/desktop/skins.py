"""Declarative local sprite packs. No scripts or archive extraction."""
from pathlib import Path
import json,uuid,shutil
from PIL import Image
STATES=('idle','wave','happy','pat','sleep','think')
class SkinStore:
    def __init__(self,root):self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
    def load(self,folder):
        root=Path(folder).resolve();manifest=json.loads((root/'skin.json').read_text('utf-8'));result={};total=0;pixels=0
        for state in STATES:
            names=manifest.get('states',{}).get(state,manifest.get('states',{}).get('idle',[]))
            if not names or len(names)>60:raise ValueError('每组动作需要1–60帧，必须提供idle')
            result[state]=[]
            for name in names:
                p=(root/name).resolve()
                if root not in p.parents or p.suffix.lower()!='.png' or p.is_symlink():raise ValueError('帧图路径必须位于皮肤目录内')
                total+=p.stat().st_size
                if total>80*1024*1024:raise ValueError('皮肤总大小不能超过80MB')
                with Image.open(p) as im:
                    pixels+=im.width*im.height
                    if max(im.size)>2048 or pixels>24000000:raise ValueError('皮肤解码体积过大；单帧最多2048像素，总计最多2400万像素')
                    im.verify()
                result[state].append(p)
        return result,max(1,min(30,int(manifest.get('fps',8))))
    def import_folder(self,folder):
        frames,fps=self.load(folder);dest=self.root/uuid.uuid4().hex;dest.mkdir();manifest={'name':Path(folder).name,'fps':fps,'states':{}}
        for state,paths in frames.items():
            manifest['states'][state]=[]
            for i,p in enumerate(paths):
                name=f'{state}-{i}.png';shutil.copy2(p,dest/name);manifest['states'][state].append(name)
        (dest/'skin.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8');return dest
    def import_atlas(self,path,columns,rows=6):
        if not 1<=columns<=30 or rows!=6:raise ValueError('图集使用6行，1–30列；动作顺序见模板')
        with Image.open(path) as atlas:
            if max(atlas.size)>12000:raise ValueError('图集边长最多12000像素')
            dest=self.root/uuid.uuid4().hex;dest.mkdir();manifest={'name':Path(path).stem,'fps':8,'states':{}}
            for row,state in enumerate(STATES):
                manifest['states'][state]=[]
                for col in range(columns):
                    frame=atlas.crop((round(col*atlas.width/columns),round(row*atlas.height/rows),round((col+1)*atlas.width/columns),round((row+1)*atlas.height/rows))).convert('RGBA');frame.thumbnail((600,600),Image.Resampling.LANCZOS);name=f'{state}-{col}.png';frame.save(dest/name);manifest['states'][state].append(name)
            (dest/'skin.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8');return dest
