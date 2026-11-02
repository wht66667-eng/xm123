"""Fox journal UI. Real controls over a quiet illustrated surface. MIT fox."""
import json,os,sys,threading,queue,datetime
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,Signal,QObject,QSize
from PySide6.QtGui import QPainter,QPixmap,QColor,QFont,QPainterPath,QIcon,QKeySequence,QShortcut
from PySide6.QtWidgets import (QWidget,QFrame,QLabel,QPushButton,QVBoxLayout,QHBoxLayout,QStackedWidget,QScrollArea,QPlainTextEdit,QCheckBox,QLineEdit,QComboBox,QFileDialog,QDialog,QDialogButtonBox,QListWidget,QListWidgetItem,QSizePolicy)
from assistant import Library,save_config,ask
from protocols import resolve
from file_actions import validate_target,delete_original

ASSETS=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))/'assets'
STYLE='''
QWidget{color:#614538;font-family:"Microsoft YaHei";font-size:13px;}
QWidget#lounge{background:#FFF9F0;}QFrame#rail{background:#FCF2E4;border-right:1px solid #EBD9C5;}
QLabel#title{font-family:"Microsoft YaHei";font-size:23px;font-weight:600;}QLabel#muted{color:#8B7665;font-size:12px;}QLabel#brand{font-family:Georgia;font-size:27px;font-weight:bold;}QLabel#badge{background:#EAF0DF;border:1px solid #D6E0C9;border-radius:14px;color:#526544;padding:5px 12px;font-size:11px;}
QPushButton{background:#FFF8EF;border:1px solid #E5CBB3;border-radius:17px;padding:9px 16px;color:#614538;}QPushButton:hover{background:#FFEAD5;border-color:#DCA67C;}QPushButton:pressed{background:#FAD6B6;}QPushButton:focus{border:2px solid #B9683D;}QPushButton:disabled{color:#A89686;background:#EEE6DC;border-color:#E4D9CF;}
QPushButton#primary{background:#F18A52;border:1px solid #E87F45;color:white;font-weight:600;}QPushButton#primary:hover{background:#DE7844;}QPushButton#danger{background:#B94D37;border-color:#A24030;color:white;}
QPushButton#nav{border:0;border-radius:15px;text-align:left;padding:13px 18px;background:transparent;font-size:14px;}QPushButton#nav:checked{background:#FFD9BD;color:#5F3525;font-weight:600;}QPushButton#nav:hover{background:#FFE7D1;}
QFrame#card{background:rgba(255,253,247,235);border:1px solid #EBD9C5;border-radius:17px;}QFrame#composer{background:#FFFCF6;border:1px solid #E4D0B9;border-radius:22px;}
QLineEdit,QComboBox{background:#FFFFFF;border:1px solid #E1CCB5;border-radius:12px;padding:10px 12px;selection-background-color:#FFDABD;}QLineEdit:focus,QComboBox:focus{border:2px solid #C3865E;}QComboBox::drop-down{border:0;width:24px;}QComboBox QAbstractItemView{background:#FFFCF5;selection-background-color:#FFE1C6;selection-color:#614538;}
QPlainTextEdit{background:transparent;border:0;padding:5px;selection-background-color:#DCE6C8;}QScrollArea{border:0;background:transparent;}QScrollArea>QWidget>QWidget{background:#FFF9F0;}QScrollBar:vertical{background:transparent;width:7px;}QScrollBar::handle:vertical{background:#D8C8B7;border-radius:3px;min-height:25px;}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
QListWidget{background:transparent;border:0;outline:0;}QListWidget::item{border-radius:12px;margin:4px 0;}QListWidget::item:selected{background:#FFE1C8;}QCheckBox{spacing:8px;color:#7B6856;}QCheckBox::indicator{width:15px;height:15px;}QDialog{background:#FFF8EF;}
'''
def text(value,kind=None):
    l=QLabel(value);l.setWordWrap(True)
    if kind:l.setObjectName(kind)
    return l
def btn(value,fn,kind=None):
    b=QPushButton(value);b.clicked.connect(fn)
    if kind:b.setObjectName(kind)
    return b
def card():
    f=QFrame();f.setObjectName('card');v=QVBoxLayout(f);v.setContentsMargins(20,18,20,18);v.setSpacing(12);return f,v

def avatar(size=44):
    source=QPixmap(str(ASSETS/'avatar.png'));out=QPixmap(size,size);out.fill(Qt.transparent);p=QPainter(out);p.setRenderHint(QPainter.Antialiasing);p.setRenderHint(QPainter.SmoothPixmapTransform);path=QPainterPath();path.addEllipse(0,0,size,size);p.setClipPath(path);p.fillRect(out.rect(),QColor('#FFF0DD'));p.drawPixmap(out.rect(),source);p.end();return out

class JournalSurface(QWidget):
    def __init__(self):super().__init__();self.wallpaper=QPixmap(str(ASSETS/'lounge-wallpaper.png'))
    def paintEvent(self,e):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#FFF9F0'))
        if not self.wallpaper.isNull():p.setOpacity(.53);p.drawPixmap(self.rect(),self.wallpaper)

class DropCard(QFrame):
    filesDropped=Signal(list)
    def __init__(self):
        super().__init__();self.setAcceptDrops(True);self.setStyleSheet('DropCard{background:#FFFAF1;border:1px dashed #DCA77E;border-radius:16px;}');v=QVBoxLayout(self);v.addWidget(text('↥   把资料放进小书包'));v.addWidget(text('拖入文件或文件夹，或使用下方导入按钮。','muted'));self.setMinimumHeight(95)
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls() and all(u.isLocalFile() for u in e.mimeData().urls()):e.acceptProposedAction()
    def dropEvent(self,e):self.filesDropped.emit([u.toLocalFile() for u in e.mimeData().urls()]);e.acceptProposedAction()

class ConfirmDialog(QDialog):
    def __init__(self,parent,title,description,typed=False):
        super().__init__(parent);self.setWindowTitle(title);self.setStyleSheet(STYLE);self.resize(480,310);v=QVBoxLayout(self);v.setContentsMargins(26,24,26,24);v.addWidget(text(title,'title'));info=QPlainTextEdit();info.setPlainText(description);info.setReadOnly(True);info.setMinimumHeight(105);v.addWidget(info)
        self.word=QLineEdit();self.word.setPlaceholderText('输入 DELETE 确认永久删除')
        if typed:v.addWidget(self.word)
        row=QHBoxLayout();row.addStretch();row.addWidget(btn('取消',self.reject));self.ok=btn('确认删除',self.accept,'danger');row.addWidget(self.ok);v.addLayout(row)
        if typed:self.ok.setEnabled(False);self.word.textChanged.connect(lambda value:self.ok.setEnabled(value=='DELETE'))

class AssistantWindow(QWidget):
    def __init__(self,model,data,parent=None):
        super().__init__(parent,Qt.Window);self.model=model;self.data=Path(data);self.library=Library(self.data/'knowledge-desktop');self.workers=queue.Queue();self.busy=False;self.success_callback=None;self.setObjectName('lounge');self.setWindowTitle('fox · 陪伴小窝');self.resize(1040,750);self.setMinimumSize(820,620);self.setStyleSheet(STYLE);self.setWindowIcon(QIcon(avatar(64)));self.config=self.load_config()
        shell=QHBoxLayout(self);shell.setContentsMargins(0,0,0,0);shell.setSpacing(0)
        rail=QFrame();rail.setObjectName('rail');rail.setFixedWidth(185);rv=QVBoxLayout(rail);rv.setContentsMargins(18,28,18,20);rv.setSpacing(10)
        icon=QLabel();icon.setPixmap(avatar(68));rv.addWidget(icon);rv.addWidget(text('fox','brand'));rv.addWidget(text('一直在这里，\n陪你一起进步。','muted'));rv.addSpacing(24)
        self.stack=QStackedWidget();self.nav=[]
        for i,title in enumerate(['◌   聊聊天','♧   小书包','⚿   小钥匙','▱   文件整理']):
            b=btn(title,lambda checked=False,index=i:self.switch(index));b.setObjectName('nav');b.setCheckable(True);rv.addWidget(b);self.nav.append(b)
        rv.addStretch();rv.addWidget(text('小小的日常\n也很了不起。 ♡','muted'));self.pet_icon=QLabel();self.pet_icon.setPixmap(QPixmap(str(ASSETS/'pat-3.png')).scaled(130,130,Qt.KeepAspectRatio,Qt.SmoothTransformation));rv.addWidget(self.pet_icon,0,Qt.AlignCenter)
        shell.addWidget(rail);main=QVBoxLayout();main.setContentsMargins(28,25,28,16);shell.addLayout(main,1)
        head=QHBoxLayout();titlebox=QVBoxLayout();titlebox.addWidget(text('今天也一起进步吧 ฅ','title'));titlebox.addWidget(text('有问题时告诉我，我们把它慢慢拆开。','muted'));head.addLayout(titlebox,1);self.badge=text('已配置' if self.config else '待配置','badge');head.addWidget(self.badge,0,Qt.AlignTop);main.addLayout(head);main.addSpacing(12);main.addWidget(self.stack,1)
        self.status=text('本地资料不联网；只有点击发送才调用 AI。','muted');main.addWidget(self.status)
        self.build_chat();self.build_docs();self.build_settings();self.build_files();self.switch(0);self.refresh_docs();self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(100)
    def load_config(self):
        try:return json.loads((self.data/'desktop-ai.json').read_text('utf-8'))
        except (OSError,ValueError):return {}
    def switch(self,index):
        self.stack.setCurrentIndex(index)
        for i,b in enumerate(self.nav):b.setChecked(i==index)
    def build_chat(self):
        page=JournalSurface();v=QVBoxLayout(page);v.setContentsMargins(12,12,12,0);self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.viewport().setAutoFillBackground(False);self.log=QWidget();self.log.setStyleSheet('background:transparent;');self.messages=QVBoxLayout(self.log);self.messages.setAlignment(Qt.AlignTop);self.messages.setSpacing(16);self.scroll.setWidget(self.log);v.addWidget(self.scroll,1)
        self.add_bubble('欢迎回来呀，今天想学什么？\n可以把资料放进小书包，我们慢慢看。')
        chips=QHBoxLayout();chips.addWidget(btn('⌘  怎么解释代码',lambda:self.add_bubble('在 VS Code 中选中代码，右键选择 fox 解析或建议。也可以将代码粘贴到这里，再点击发送。')));chips.addWidget(btn('▤  查看我的资料',lambda:self.switch(1)));chips.addStretch();v.addLayout(chips)
        composer=QFrame();composer.setObjectName('composer');cv=QVBoxLayout(composer);cv.setContentsMargins(12,10,12,9);self.question=QPlainTextEdit();self.question.setPlaceholderText('和 fox 说句话…');self.question.setFixedHeight(68);cv.addWidget(self.question);actions=QHBoxLayout();actions.addWidget(btn('＋ 资料',lambda:self.switch(1)));self.attach=QCheckBox('附带匹配资料');self.attach.setToolTip('开启后，最多3段匹配资料会随问题发送给当前AI。');actions.addWidget(self.attach);actions.addStretch();self.send_button=btn('发送  ➤',self.send,'primary');actions.addWidget(self.send_button);cv.addLayout(actions);v.addWidget(composer);self.stack.addWidget(page);self.shortcut=QShortcut(QKeySequence('Ctrl+Return'),self);self.shortcut.activated.connect(self.send)
    def add_bubble(self,value,user=False):
        row=QWidget();r=QHBoxLayout(row);r.setContentsMargins(0,0,0,0);r.setSpacing(10)
        if user:r.addStretch(1)
        else:
            face=QLabel();face.setPixmap(avatar());face.setFixedSize(44,44);r.addWidget(face,0,Qt.AlignTop)
        bubble=QFrame();bubble.setMaximumWidth(510);bubble.setStyleSheet('QFrame{background:%s;border:1px solid %s;border-radius:19px;}'%('#DDE6CA' if user else '#FFF0DF','#C7D3B2' if user else '#EDD0B2'));bv=QVBoxLayout(bubble);bv.setContentsMargins(17,12,17,11);label=text(str(value));label.setTextFormat(Qt.PlainText);label.setTextInteractionFlags(Qt.TextSelectableByMouse);label.setStyleSheet('border:0;background:transparent;line-height:1.5;');bv.addWidget(label);time=text(datetime.datetime.now().strftime('%H:%M'),'muted');time.setStyleSheet('border:0;background:transparent;color:#9A8571;font-size:10px;');bv.addWidget(time);r.addWidget(bubble)
        if not user:r.addStretch(1)
        self.messages.addWidget(row);QTimer.singleShot(30,lambda:self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))
    def start_task(self,fn,done=None):
        if self.busy:self.status.setText('我还在处理上一件事，稍等一下喵。');return False
        self.busy=True;self.send_button.setEnabled(False);self.send_button.setText('阅读中…');self.status.setText('小爪子忙碌中，正在处理你这次操作…')
        def worker():
            try:self.workers.put((True,fn(),done))
            except Exception as e:self.workers.put((False,str(e),None))
        threading.Thread(target=worker,daemon=True).start();return True
    def poll(self):
        try:
            ok,result,done=self.workers.get_nowait();self.busy=False;self.send_button.setEnabled(True);self.send_button.setText('发送  ➤');self.add_bubble(result);self.status.setText('完成啦，喵～' if ok else '未完成，错误详情已显示在聊天里。')
            if done:done()
            if not ok:self.switch(0)
        except queue.Empty:pass
    def send(self):
        if self.stack.currentIndex()!=0 or self.busy:return
        question=self.question.toPlainText().strip()
        if not question:return
        if len(question)>6000:self.status.setText('一次最多6000字，问题可以拆小一点哦。');return
        attach=self.attach.isChecked();self.add_bubble(question,True);self.question.clear()
        def work():
            hits=self.library.search(question) if attach else [];context='\n\n'.join(name+'\n'+chunk for score,name,chunk in hits);return ask(self.data,question,context)
        self.start_task(work)
    def build_docs(self):
        page=QWidget();v=QVBoxLayout(page);v.setContentsMargins(0,0,0,0);v.addWidget(text('小书包 · 我的资料库','title'));v.addWidget(text('把资料交给我，一起整理、学习。导入副本保存在本机。','muted'));drop=DropCard();drop.filesDropped.connect(self.import_paths);v.addWidget(drop)
        row=QHBoxLayout();row.addWidget(btn('＋ 导入文档',self.choose_files,'primary'));row.addWidget(btn('导入文件夹',self.choose_folder));row.addStretch();v.addLayout(row);self.docs=QListWidget();self.docs.setSelectionMode(QListWidget.ExtendedSelection);v.addWidget(self.docs,1);self.empty_docs=text('小书包还是空的。先放进一篇文档吧。','muted');v.addWidget(self.empty_docs)
        search=QHBoxLayout();self.search_field=QLineEdit();self.search_field.setPlaceholderText('在本机资料里搜索…');self.search_field.returnPressed.connect(self.search_local);search.addWidget(self.search_field);search.addWidget(btn('本地搜索',self.search_local));v.addLayout(search)
        row=QHBoxLayout();row.addWidget(btn('清理选中副本',self.delete_copies));row.addStretch();v.addLayout(row);self.stack.addWidget(page)
    def refresh_docs(self):
        self.docs.clear();self.doc_paths=self.library.documents();self.empty_docs.setVisible(not self.doc_paths)
        for path in self.doc_paths:
            try:doc=json.loads(path.read_text('utf-8'));name=doc['name'];size=len(doc['text'].encode('utf-8'))
            except (OSError,ValueError,KeyError):continue
            item=QListWidgetItem();item.setData(Qt.UserRole,str(path));item.setSizeHint(QSize(300,75));self.docs.addItem(item);frame=QFrame();frame.setObjectName('card');layout=QHBoxLayout(frame);symbol=text('PDF' if name.lower().endswith('.pdf') else 'TXT');symbol.setStyleSheet('background:#FBE5CF;color:#A55C35;border:0;border-radius:9px;padding:9px;font-weight:bold;');layout.addWidget(symbol);titles=QVBoxLayout();titles.addWidget(text(name));titles.addWidget(text(f'本地副本 · {size/1024:.1f} KB','muted'));layout.addLayout(titles,1);self.docs.setItemWidget(item,frame)
    def choose_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,'挑几篇资料给 fox','','学习文档 (*.txt *.md *.pdf *.docx *.py *.js *.ts *.json *.csv *.html *.css *.cjs);;所有文件 (*)')
        if paths:self.import_paths(paths)
    def choose_folder(self):
        path=QFileDialog.getExistingDirectory(self,'选一个资料文件夹')
        if path:self.import_paths([path])
    def import_paths(self,paths):
        if self.busy:return
        def candidates():
            examined=0
            for value in paths:
                p=Path(value)
                if p.is_symlink():continue
                if p.is_dir():
                    for base,dirs,files in os.walk(p,followlinks=False):
                        dirs[:]=[d for d in dirs if d not in ('.git','node_modules','.venv','venv','__pycache__') and not Path(base,d).is_symlink()]
                        for name in files:
                            if examined>=1000:return
                            examined+=1;yield Path(base,name)
                else:yield p
        self.start_task(lambda:'资料收好啦：成功 %d 篇，跳过 %d 项。原文件保持不变。'%self.library.ingest(candidates()),self.refresh_docs)
    def search_local(self):
        query=self.search_field.text().strip()
        if query:self.start_task(lambda:'本地搜索结果：\n'+('\n\n'.join(name+'\n'+chunk for score,name,chunk in self.library.search(query)) or '还没有找到匹配内容。'),lambda:self.switch(0))
    def delete_copies(self,all_items=False):
        if self.busy:return
        paths=self.library.documents() if all_items else [Path(item.data(Qt.UserRole)) for item in self.docs.selectedItems()]
        if not paths:self.status.setText('先在小书包中选中需要清理的资料。');return
        if ConfirmDialog(self,'清理小书包',f'永久清除 {len(paths)} 篇知识库副本。\n电脑原文件不会被删除。').exec()==QDialog.Accepted:self.start_task(lambda:f'已清除 {self.library.delete(paths)} 篇副本。',self.refresh_docs)
    def build_settings(self):
        page=QWidget();outer=QVBoxLayout(page);outer.setContentsMargins(0,0,0,0);scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();v=QVBoxLayout(body);v.setContentsMargins(0,0,8,0);v.addWidget(text('小钥匙 · AI 接入','title'));v.addWidget(text('选择服务商，也可以自己填写接口和模型。保存不会发请求。','muted'));f,fields=card();v.addWidget(f)
        self.providers=json.loads((ASSETS/'providers.json').read_text('utf-8'));self.provider=QComboBox()
        for p in self.providers:self.provider.addItem(p['label'],p)
        self.protocol=QComboBox()
        for label,value in [('Chat Completions','chat'),('Responses API','responses'),('Messages API','messages')]:self.protocol.addItem(label,value)
        self.base=QLineEdit(self.config.get('url','https://api.deepseek.com'));self.model_id=QComboBox();self.model_id.setEditable(True);self.model_id.setEditText(self.config.get('model','deepseek-flash'));self.key=QLineEdit();self.key.setEchoMode(QLineEdit.Password);self.key.setPlaceholderText('填写对应服务的小钥匙；同接口留空沿用原密钥')
        self.auth=QComboBox()
        for label,value in [('自动匹配协议','auto'),('Authorization: Bearer','bearer'),('x-api-key','x-api-key')]:self.auth.addItem(label,value)
        for title,widget in [('服务商预设',self.provider),('API 协议',self.protocol),('接口基址或完整地址',self.base),('模型 ID（可自由填写）',self.model_id),('API Key',self.key),('认证方式',self.auth)]:fields.addWidget(text(title,'muted'));fields.addWidget(widget)
        self.provider_note=text('模型可用性取决于服务商和你的账户权限。','muted');fields.addWidget(self.provider_note);self.provider.currentIndexChanged.connect(self.provider_changed)
        index=next((i for i,p in enumerate(self.providers) if self.config.get('url','').startswith(p['base']) and p['base']),8 if self.config else 1);self.provider.setCurrentIndex(index);self.provider_changed(index,initial=True)
        if self.config:self.base.setText(self.config['url']);self.model_id.setEditText(self.config['model']);self.protocol.setCurrentIndex(max(0,self.protocol.findData(self.config.get('protocol','chat'))));self.auth.setCurrentIndex(max(0,self.auth.findData(self.config.get('auth','auto'))))
        row=QHBoxLayout();row.addWidget(btn('加密保存小钥匙',self.save_settings,'primary'));row.addWidget(btn('移除已存密钥',self.remove_key));row.addStretch();v.addLayout(row);v.addWidget(text('桌面设置独立于 VS Code。密钥用 Windows 用户加密保存；不展示、不记录到对话。\nAgnes 3.0 Pro 按你提供的文档标为即将上线。所有模型 ID 均可手动修改。','muted'));v.addStretch();scroll.setWidget(body);outer.addWidget(scroll);self.stack.addWidget(page)
    def provider_changed(self,index,initial=False):
        p=self.providers[index];self.model_id.clear();self.model_id.addItems(p.get('models',[]));self.provider_note.setText(p.get('note','模型列表为预设，实际可用性取决于账户权限。'))
        if not initial:self.base.setText(p['base']);self.protocol.setCurrentIndex(max(0,self.protocol.findData(p['protocol'])));self.key.clear()
    def save_settings(self):
        if self.busy:self.status.setText('等当前请求完成后再修改接口。');return
        try:
            base=self.base.text().strip();kind=self.protocol.currentData();target,_=resolve(base,kind);model=self.model_id.currentText().strip();key=self.key.text().strip()
            if not model:raise ValueError('模型名称还没填哦。')
            old=self.load_config()
            if not key and target==old.get('url') and old.get('key'):
                import win32crypt
                key=win32crypt.CryptUnprotectData(bytes.fromhex(old['key']),None,None,None,0)[1].decode()
            save_config(self.data,base,model,key,kind,self.auth.currentData());self.config=self.load_config();self.key.clear();self.badge.setText('已配置');self.status.setText('配置已加密保存，没有发送测试请求。')
        except Exception as e:self.status.setText(str(e))
    def remove_key(self):
        path=self.data/'desktop-ai.json'
        if path.exists() and ConfirmDialog(self,'移除桌面配置','删除当前桌面 API 配置和加密密钥。VS Code 密钥不受影响。').exec()==QDialog.Accepted:path.unlink();self.config={};self.badge.setText('待配置');self.status.setText('桌面密钥已移除。')
    def build_files(self):
        page=QWidget();v=QVBoxLayout(page);v.setContentsMargins(0,0,0,0);v.addWidget(text('文件整理 · 清楚地核对每一步','title'));f,cv=card();cv.addWidget(text('清理知识库副本'));cv.addWidget(text('原文档保持不变，只清理小书包中的导入副本。','muted'));cv.addWidget(btn('选择资料',lambda:self.switch(1)));cv.addWidget(btn('清空全部知识库副本',lambda:self.delete_copies(True)));v.addWidget(f)
        f,cv=card();cv.addWidget(text('永久删除电脑原文件'));cv.addWidget(text('此操作不进回收站。文件夹中的内容也会永久删除。\n执行前必须核对完整路径，并输入 DELETE。','muted'));self.force=QCheckBox('强制模式：清除只读属性后重试');cv.addWidget(self.force);row=QHBoxLayout();row.addWidget(btn('选择原文件',lambda:self.original(False)));row.addWidget(btn('选择原文件夹',lambda:self.original(True)));cv.addLayout(row);v.addWidget(f);v.addStretch();self.stack.addWidget(page)
    def original(self,folder):
        if self.busy:return
        value=QFileDialog.getExistingDirectory(self,'选择要永久删除的原文件夹') if folder else QFileDialog.getOpenFileName(self,'选择要永久删除的原文件')[0]
        if not value:return
        try:target=validate_target(value)
        except Exception as e:self.status.setText(str(e));return
        force=self.force.isChecked()
        if ConfirmDialog(self,'核对删除目标',str(target)+'\n\n原文件永久删除，不进回收站。',True).exec()==QDialog.Accepted:self.start_task(lambda:'已永久删除原目标：'+delete_original(target,force))
