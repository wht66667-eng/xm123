"""Versioned self-maintenance in an isolated source copy. MIT fox."""
from pathlib import Path
from process_control import terminate_owned
import os,shutil,uuid,json,subprocess,threading,hashlib,difflib

class Optimizer:
    def __init__(self,data):self.data=Path(data);self.process=None;self.stopped=threading.Event()
    def fingerprint(self,root):
        root=Path(root)
        return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and not any(x in p.relative_to(root).parts for x in ('test-artifacts','__pycache__','node_modules','.git')) and p.suffix.lower() not in ('.exe','.vsix','.pyc')}
    def stop(self):
        self.stopped.set()
        terminate_owned(self.process)
    def snapshot(self,source):
        source=Path(source).resolve();package=json.loads((source/'package.json').read_text('utf-8'))
        if package.get('name')!='fox-code-meow':raise ValueError('请选择fox插件源码目录')
        run=self.data/'optimization-runs'/uuid.uuid4().hex;target=run/'source'
        if source==target or source in target.parents:raise ValueError('优化副本必须位于源码目录外')
        target.mkdir(parents=True)
        def ignore(directory,names):
            excluded=set(shutil.ignore_patterns('*.exe','*.vsix','*.pyc','__pycache__','.env*','node_modules','test-artifacts')(directory,names))
            for name in names:
                p=Path(directory)/name
                if p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&1024:excluded.add(name)
            return excluded
        for folder in ['src','desktop','integrations','test','assets','third_party_licenses','agent-skills','knowledge']:
            entry=source/folder
            if entry.is_dir() and not entry.is_symlink() and not (getattr(entry.lstat(),'st_file_attributes',0)&1024):shutil.copytree(entry,target/folder,ignore=ignore,symlinks=False)
        for name in ['package.json','README.md','LICENSE','CHANGELOG.md','build.ps1','.vscodeignore','.gitignore']:
            if (source/name).is_file():shutil.copy2(source/name,target/name)
        manifest={str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}
        (run/'baseline.json').write_text(json.dumps(manifest,indent=2),'utf-8');return run
    def apply_candidate(self,run,changes):
        run=Path(run).resolve();target=run/'source';diffs=[];planned=[]
        if not isinstance(changes,list) or len(changes)>8:raise ValueError('一次候选最多8个文件')
        for item in changes:
            name=item['path'];content=item['content'];p=(target/name).resolve()
            if target not in p.parents or p.suffix not in ('.py','.cjs','.js') or p.parts[len(target.parts)] not in ('src','desktop'):raise ValueError('候选只允许修改副本中的src/desktop代码')
            if not p.is_file() or not isinstance(content,str) or len(content)>150000:raise ValueError('候选文件无效')
            old=p.read_text('utf-8');diffs.extend(difflib.unified_diff(old.splitlines(True),content.splitlines(True),fromfile=name,tofile=name));planned.append((p,content))
        backup=run/'baseline-code'
        for p,content in planned:
            saved=backup/p.relative_to(target);saved.parent.mkdir(parents=True,exist_ok=True)
            if not saved.exists():shutil.copy2(p,saved)
            p.write_text(content,'utf-8')
        (run/'candidate.diff').write_text(''.join(diffs),'utf-8');return str(run/'candidate.diff')
    def check(self,run):
        run=Path(run);root=run/'source';node=shutil.which('node');python=shutil.which('python');self.stopped.clear();checks=[]
        before=self.fingerprint(root);commands=[]
        if node:commands.append([node,'--test']+[str(p) for p in (root/'test').glob('*.test.cjs')])
        if python:commands.append([python,'-c',"import ast,pathlib;[ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p)) for p in pathlib.Path('desktop').glob('*.py')];print('Python syntax OK')"])
        if len(commands)<2:raise ValueError('需要本机Node和Python才能检查源码副本')
        for cmd in commands:
            if self.stopped.is_set():break
            self.process=subprocess.Popen(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:output=self.process.communicate(timeout=120)[0].decode('utf-8',errors='replace')
            except subprocess.TimeoutExpired:terminate_owned(self.process);output=self.process.communicate()[0].decode('utf-8',errors='replace')+'\nTimed out'
            checks.append({'command':cmd[:2],'exitCode':self.process.returncode,'output':output[-40000:]})
        report={'stopped':self.stopped.is_set(),'passed':len(checks)==2 and all(c['exitCode']==0 for c in checks),'checks':checks}
        draft='---\nname: fox-maintenance-'+run.name[:8]+'\ndescription: 本次fox源码副本检查提炼的开发习惯草稿。\n---\n\n先创建副本、审阅差异，再执行Node测试与Python语法检查。\n本次结果：'+('通过' if report['passed'] else '未通过或已停止')+'。\n打包必须额外验证独立EXE；保留当前版本。\n'
        (run/'SKILL.md').write_text(draft,'utf-8')
        report['sourceHashes']=self.fingerprint(root)
        if before!=report['sourceHashes']:report.update(passed=False,changedDuringCheck=True)
        (run/'checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8');return report

    def restore(self,run):
        run=Path(run).resolve();target=run/'source';backup=run/'baseline-code';count=0
        if not backup.exists():return 0
        for p in backup.rglob('*'):
            if p.is_file():shutil.copy2(p,target/p.relative_to(backup));count+=1
        return count

    def build(self,run):
        run=Path(run);root=run/'source';report=json.loads((run/'checks.json').read_text('utf-8'))
        current=self.fingerprint(root)
        if not report.get('passed') or report.get('sourceHashes')!=current:raise ValueError('先对当前副本运行检查并通过后再构建')
        node=shutil.which('node');npx_cli=Path(node).parent/'node_modules/npm/bin/npx-cli.js' if node else Path('missing')
        if not node or not npx_cli.is_file():raise ValueError('找不到Node随附的npx-cli.js，请安装完整Node.js')
        commands=[[shutil.which('pyinstaller'),'--noconfirm','--distpath','desktop','--workpath','test-artifacts/pet-build','desktop/fox-pet.spec'],[shutil.which('python'),'test/frozen-check.py'],[node,str(npx_cli),'--yes','@vscode/vsce','package','--allow-missing-repository','--no-dependencies','--out','fox-candidate.vsix']]
        self.stopped.clear();logs=[]
        for cmd in commands:
            if self.stopped.is_set():raise ValueError('候选构建已停止')
            if not cmd[0]:raise ValueError('缺少构建工具，请安装源码依赖')
            (root/'test-artifacts').mkdir(exist_ok=True)
            self.process=subprocess.Popen(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:raw=self.process.communicate(timeout=600)[0]
            except subprocess.TimeoutExpired:terminate_owned(self.process);self.process.communicate();raise ValueError('构建超时')
            logs.append(raw.decode('utf-8',errors='replace')[-50000:]);(run/'build.log').write_text('\n'.join(logs),'utf-8')
            if self.process.returncode:raise ValueError('候选构建未通过，请查看build.log')
        return {'vsix':str(root/'fox-candidate.vsix'),'exe':str(root/'desktop/fox-pet.exe'),'note':'只生成候选安装包，不自动替换运行版本'}
