"""Agent setup and explicitly started handoff chain."""
from pathlib import Path
import json
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QLineEdit,QPlainTextEdit,QCheckBox,QScrollArea
from agent_hub import AgentHub,ROLES

def build_team(window,root):
 from qt_assistant import text,btn,card
 hub=AgentHub(window.data,root);window.agent_hub=hub;outer=QWidget();v=QVBoxLayout(outer);v.setContentsMargins(0,0,0,0);scroll=QScrollArea();scroll.setWidgetResizable(True);page=QWidget();body=QVBoxLayout(page);scroll.setWidget(page);v.addWidget(scroll)
 body.addWidget(text('小队 · 分工与独立配置','title'));body.addWidget(text('每个角色独立保存API和skill；启动一次团队任务，最多6次模型请求。','muted'))
 role=QComboBox()
 for key,(label,duty) in ROLES.items():role.addItem(label,key)
 body.addWidget(role);duty=text('');body.addWidget(duty);f,fields=card();body.addWidget(f)
 providers=json.loads((root/'assets/providers.json').read_text('utf-8'));provider=QComboBox()
 for p in providers:provider.addItem(p['label'],p)
 fields.addWidget(provider);base=QLineEdit();model=QLineEdit();key=QLineEdit();key.setEchoMode(QLineEdit.Password);protocol=QComboBox()
 for label,value in [('Chat Completions','chat'),('Responses','responses'),('Messages','messages')]:protocol.addItem(label,value)
 for label,widget in [('接口地址',base),('模型ID',model),('密钥（仅保留在该角色加密配置）',key),('协议',protocol)]:fields.addWidget(text(label,'muted'));fields.addWidget(widget)
 skill=QPlainTextEdit();skill.setMaximumHeight(170);fields.addWidget(text('该角色的独立skill（只影响建议，不赋予执行权限）','muted'));fields.addWidget(skill)
 def select_provider():
  p=provider.currentData();base.setText(p['base']);model.setText((p['models']or[''])[0]);protocol.setCurrentIndex(max(0,protocol.findData(p['protocol'])));key.clear()
 def load_role():
  r=role.currentData();duty.setText(ROLES[r][1]);skill.setPlainText(hub.skill(r));path=hub.profile(r)/'desktop-ai.json';key.clear()
  if path.exists():
   cfg=json.loads(path.read_text('utf-8'));base.setText(cfg['url']);model.setText(cfg['model']);protocol.setCurrentIndex(max(0,protocol.findData(cfg.get('protocol','chat'))))
  else:select_provider()
 def save():
  if window.busy:return
  try:
   r=role.currentData();secret=key.text();path=hub.profile(r)/'desktop-ai.json'
   if not secret and path.exists():
    from protocols import resolve
    cfg=json.loads(path.read_text('utf-8'))
    if resolve(base.text(),protocol.currentData())[0]==cfg['url']:
     import win32crypt
     secret=win32crypt.CryptUnprotectData(bytes.fromhex(cfg['key']),None,None,None,0)[1].decode()
   if not model.text().strip():raise ValueError('请填写模型ID')
   hub.configure(r,base.text(),model.text(),secret,protocol.currentData());(hub.profile(r)/'SKILL.md').write_text(skill.toPlainText(),'utf-8');key.clear();window.status.setText('角色配置与skill已保存，没有调用AI。')
  except Exception as e:window.status.setText(str(e))
 provider.currentIndexChanged.connect(select_provider);role.currentIndexChanged.connect(load_role);load_role();fields.addWidget(btn('保存这个角色',save,'primary'))
 body.addWidget(text('发起互助任务','title'));task=QPlainTextEdit();task.setPlaceholderText('说明目标、输入和你希望的结果；不会自动执行模型建议。');task.setMaximumHeight(100);body.addWidget(task);choices={}
 course=QComboBox();course.addItem('不附带实验资料',None)
 for item in hub.courses():course.addItem(item['title'],item['id'])
 body.addWidget(course);body.addWidget(text('仅点击启动时，将选定实验的摘要、参数和验证状态发送给小队各角色；不上传原始文件。','muted'))
 row=QHBoxLayout()
 for r in ('developer','gis','librarian','designer'):
  c=QCheckBox(ROLES[r][0]);choices[r]=c;row.addWidget(c)
 body.addLayout(row);body.addWidget(text('固定流程：协调者 → 所选专家 → 审查员。停止后不发新请求；当前网络请求可能需等待结束。','muted'))
 def start():
  selected=[r for r,c in choices.items() if c.isChecked()];q=task.toPlainText();course_id=course.currentData()
  window.start_task(lambda:json.dumps(hub.run(q,selected,course_id=course_id),ensure_ascii=False,indent=2))
 row=QHBoxLayout();row.addWidget(btn('启动团队任务',start,'primary'));row.addWidget(btn('停止后续交接',hub.stop));body.addLayout(row);return outer
