"""Explicit local deletion: no shell, elevation or process termination."""
from pathlib import Path
import os,stat,shutil

def validate_target(value):
    raw=Path(value).absolute()
    if not raw.exists():raise ValueError('目标不存在')
    # Reject reparse points anywhere in the path (includes symlinks/junctions).
    for item in [raw,*raw.parents]:
        if item.is_symlink() or getattr(item.lstat(),'st_file_attributes',0)&1024:raise ValueError('不支持符号链接或目录联接')
    target=raw.resolve()
    protected=[Path(target.anchor),Path.home()]
    for key in ('WINDIR','ProgramFiles','ProgramFiles(x86)','ProgramData','APPDATA','LOCALAPPDATA'):
        if os.environ.get(key):
            base=Path(os.environ[key]).resolve()
            if target==base or base in target.parents:raise ValueError('此系统或应用数据目录不允许删除')
    for name in ('Desktop','Documents','Downloads','Pictures','Videos','Music'):
        protected.append(Path.home()/name)
    if target in protected or target in Path(__file__).resolve().parents:raise ValueError('不允许删除磁盘根目录、用户根目录或程序目录')
    return target

def delete_original(value,force=False):
    target=validate_target(value)
    if target.is_dir():
        for base,dirs,files in os.walk(target,followlinks=False):
            for name in dirs+files:
                child=Path(base)/name
                if child.is_symlink() or getattr(child.lstat(),'st_file_attributes',0)&1024:raise ValueError('目录内存在链接，未执行删除')
    def retry(fn,path,exc):
        p=Path(path).resolve()
        if p!=target and target not in p.parents:raise ValueError('删除路径超出所选目标')
        if not force:raise exc[1]
        os.chmod(p,stat.S_IWRITE|stat.S_IREAD);fn(path)
    if target.is_dir():shutil.rmtree(target,onerror=retry)
    else:
        if force:os.chmod(target,stat.S_IWRITE|stat.S_IREAD)
        target.unlink()
    return str(target)
