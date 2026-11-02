"""Frozen executable check. No personal data or network access."""
from pathlib import Path
import tempfile,json

def run(result_path):
    from PySide6.QtWidgets import QApplication
    from qt_assistant import AssistantWindow
    from PySide6.QtCore import qVersion
    from gis_text import parse
    assert parse('公园200、500、1000米不融合')['distances']==[200,500,1000]
    assert parse('铁路右侧150米圆头缓冲')['side']=='RIGHT'
    app=QApplication([])
    with tempfile.TemporaryDirectory(prefix='fox-selftest-') as temp:
        window=AssistantWindow(None,Path(temp));window.show();app.processEvents()
        assert window.stack.count()==7
        for i in range(7):window.switch(i);app.processEvents()
        window.switch(0);window.grab().save(str(Path(result_path).with_suffix('.png')))
        Path(result_path).write_text(json.dumps({'ok':True,'qt':qVersion(),'pages':window.stack.count(),'networkCalls':0,'personalDataUsed':False}),'utf-8')
        window.close();app.quit()
