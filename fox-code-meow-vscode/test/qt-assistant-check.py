import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtCore import QTimer,Qt
from qt_assistant import AssistantWindow,ConfirmDialog
app=QApplication([])
with tempfile.TemporaryDirectory() as tmp:
 window=AssistantWindow(None,Path(tmp));window.show();app.processEvents()
 assert window.badge.text()=='待配置'
 assert window.stack.count()==7
 for i,name in enumerate(['chat','knowledge','api','files','arcmap','team','workbench']):
  window.switch(i);app.processEvents();window.grab().save(str(Path('test-artifacts')/('lounge-'+name+'.png')))
 window.switch(2);agnes=next(i for i,p in enumerate(window.providers) if p['id']=='agnes');window.provider.setCurrentIndex(agnes);app.processEvents();assert window.model_id.currentText()=='agnes-3.0-flash'
 assert window.protocol.count()==3
 dialog=ConfirmDialog(window,'核对删除目标','仅测试预览，不执行删除。',True);dialog.show();app.processEvents();assert not dialog.ok.isEnabled();dialog.word.setText('DELETE');assert dialog.ok.isEnabled();dialog.grab().save('test-artifacts/lounge-confirm.png');dialog.reject()
 window.close()
print('PASS journal UI: 7 pages, actual configuration status, Agnes preset, 3 protocols, typed deletion confirmation; zero API calls')
