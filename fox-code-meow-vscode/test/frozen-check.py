"""Verify the packaged artifact, not just imports in the source interpreter."""
from pathlib import Path
import subprocess,json,os,sys
from PyInstaller.archive.readers import CArchiveReader
root=Path(__file__).resolve().parents[1];exe=root/'desktop/fox-pet.exe';out=root/'test-artifacts/frozen-latest.json'
archive=CArchiveReader(str(exe));names=list(archive.toc)
assert not any(Path(n).name.lower().startswith(('icuuc','icuin','icudt')) for n in names),'foreign ICU DLL in bundle'
assert any(n.replace('\\','/').endswith('PySide6/Qt6Widgets.dll') for n in names)
if out.exists():out.unlink()
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
process=subprocess.Popen([str(exe),'--self-test',str(out)],startupinfo=si)
try:code=process.wait(timeout=45)
except subprocess.TimeoutExpired:
 print(out.read_text('utf-8') if out.exists() else 'Frozen process has not produced a result')
 raise
assert out.exists(),'missing frozen self-test result'
result=json.loads(out.read_text('utf-8'));print(json.dumps(result,ensure_ascii=False));assert code==0 and result.get('ok'),result
print('PASS packaged EXE: Qt imports, 4 real pages, process exits successfully, no foreign ICU DLL')
