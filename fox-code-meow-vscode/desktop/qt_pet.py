"""Native alpha desktop host, implemented with Qt. MIT fox."""
import sys,time
from pathlib import Path
from PySide6.QtWidgets import QApplication,QWidget,QMenu,QLabel,QInputDialog,QLineEdit
from PySide6.QtGui import QPainter,QPixmap,QColor,QPainterPath,QFont
from PySide6.QtCore import Qt,QTimer,QRectF,QPoint

class SpeechBubble(QWidget):
    def __init__(self,parent):
        super().__init__(parent,Qt.Tool|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint);self.setAttribute(Qt.WA_TranslucentBackground)
        self.label=QLabel(self);self.label.setWordWrap(True);self.label.setFont(QFont('Microsoft YaHei',10));self.label.setStyleSheet('color:#66483B;background:transparent;');self.label.move(18,12)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.hide)
    def speak(self,text,pos):
        self.label.setText(str(text)[:500]);self.label.setFixedWidth(244);self.label.adjustSize();height=min(210,max(68,self.label.height()+34));self.resize(280,height);self.label.resize(244,height-30)
        screen=QApplication.primaryScreen().availableGeometry();x=max(screen.left(),min(screen.right()-280,pos.x()-20));y=max(screen.top(),pos.y()-height+24);self.move(x,y);self.show();self.timer.start(3600);self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);shape=QPainterPath();shape.addRoundedRect(QRectF(1,1,self.width()-2,self.height()-16),18,18);shape.moveTo(126,self.height()-16);shape.lineTo(140,self.height()-2);shape.lineTo(152,self.height()-16);shape.closeSubpath();p.setPen(QColor('#E8BFA5'));p.setBrush(QColor('#FFF7EC'));p.drawPath(shape)

def run(test_output=None):
    from pet import Pet,DATA
    from qt_assistant import AssistantWindow
    if test_output:
        import tempfile,pet as pet_module
        fixture=tempfile.TemporaryDirectory(prefix='fox-dialog-test-');DATA=Path(fixture.name);pet_module.DATA=DATA;pet_module.STATE=DATA/'pet.json'
    app=QApplication(sys.argv);app.setQuitOnLastWindowClosed(False)
    model=Pet();model.root.update();model.root.withdraw()
    assets=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))/'assets'
    class DesktopFox(QWidget):
        def __init__(self):
            super().__init__();self.setWindowTitle('fox · 自由桌宠');self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool);self.setAttribute(Qt.WA_TranslucentBackground)
            self.resize(240,240);self.move(300,300);self.images={n:[QPixmap(str(assets/f'{n}-{i}.png')) for i in range(6)] for n in ('idle','wave','happy','pat','sleep','think')};self.image=self.images['idle'][0];self.anchor=None;self.dragged=False
            self.speech=SpeechBubble(self)
            self.timer=QTimer(self);self.timer.timeout.connect(self.update_model);self.timer.start(40)
        def update_model(self):
            try:
                model.root.update()
                action=getattr(model,'render_action','idle');index=getattr(model,'render_index',0)
                pix=self.images[action][index]
                self.image=pix.transformed(__import__('PySide6.QtGui',fromlist=['QTransform']).QTransform().scale(-1,1)) if action=='wave' and model.direction<0 else pix
                if not model.dragging:self.move(model.pos_x,model.pos_y)
                self.update()
            except Exception:
                self.timer.stop();self.close();app.quit()
        def paintEvent(self,event):
            painter=QPainter(self);painter.drawPixmap(0,0,self.image)
        def mousePressEvent(self,event):
            if event.button()==Qt.LeftButton:
                self.anchor=event.globalPos()-self.pos();self.dragged=False;model.dragging=True;model.pause_until=time.monotonic()+5;model.move_until=0
        def mouseMoveEvent(self,event):
            if self.anchor is not None and event.buttons()&Qt.LeftButton:
                pos=event.globalPos()-self.anchor;screen=app.primaryScreen().availableGeometry();x=max(screen.left(),min(screen.right()-239,pos.x()));y=max(screen.top(),min(screen.bottom()-239,pos.y()))
                self.move(x,y);model.pos_x=x;model.pos_y=y;model.root.geometry(f'+{x}+{y}');self.dragged=True
        def mouseReleaseEvent(self,event):
            if event.button()==Qt.LeftButton:
                model.dragging=False;self.anchor=None;model.pause_until=time.monotonic()+5
                if not self.dragged:model.pat()
        def mouseDoubleClickEvent(self,event):
            model.move_until=0;model.pause_until=time.monotonic()+5;model.open_assistant()
        def rename(self):
            model.move_until=0;model.pause_until=time.monotonic()+60
            value,ok=QInputDialog.getText(self,'fox · 我该怎么称呼你','称呼（最多30字）',QLineEdit.Normal,str(model.state.get('name','')))
            model.pause_until=time.monotonic()+4
            if ok and value.strip():
                model.state['name']=value.strip()[:30];model.save();model.bubble_until=time.monotonic()+4;model.message.set(model.state['name']+'，记住啦。以后就这样叫你，喵～')
        def focus(self):
            minutes,ok=QInputDialog.getInt(self,'一起专注','专注几分钟？',25,1,180)
            if ok:model.focus_minutes=minutes;model.focus_end=time.monotonic()+minutes*60;model.bubble_until=time.monotonic()+4;model.message.set('好呀，我安静陪你专注。')
        def contextMenuEvent(self,event):
            model.move_until=0;model.pause_until=time.monotonic()+5
            menu=QMenu(self);menu.setStyleSheet('QMenu{background:#FFF8EF;color:#66483B;border:1px solid #E8BFA5;padding:7px;border-radius:10px;font-size:14px;}QMenu::item{padding:8px 22px;}QMenu::item:selected{background:#FFE1C8;border-radius:6px;}')
            for title,fn in [('聊天 / 文档 / API / 文件管理',model.open_assistant),('摸摸头',model.pat),('投喂',model.feed),('休息 / 睡醒',model.sleep),('自由走动 / 原地停留',model.toggle_roam),('专注计时',self.focus),('停止计时',model.stop_focus),('设置称呼',self.rename),('减少动画',model.toggle_motion),('查看记录',model.records),('退出狐狸娘',self.quit)]:menu.addAction(title,fn)
            menu.exec_(event.globalPos())
        def quit(self):
            self.timer.stop();model.close();self.close();app.quit()
    pet=DesktopFox()
    assistant=[None]
    def open_lounge():
        if assistant[0] is None:assistant[0]=AssistantWindow(model,DATA,pet)
        assistant[0].show();assistant[0].raise_();assistant[0].activateWindow()
    model.assistant_callback=open_lounge
    model.bubble_callback=lambda text:pet.speech.speak(text,pet.pos());pet.show()
    if test_output:
        def verify():
            try:
                assert pet.testAttribute(Qt.WA_TranslucentBackground)
                assert pet.windowFlags()&Qt.FramelessWindowHint
                assert pet.x()!=300, "pet must roam after idle delay"
                def accept_name():
                    dialog=app.activeModalWidget()
                    assert isinstance(dialog,QInputDialog)
                    dialog.setTextValue('测试称呼');dialog.accept()
                QTimer.singleShot(100,accept_name);pet.rename();assert model.state['name']=='测试称呼'
                def accept_minutes():
                    dialog=app.activeModalWidget();assert isinstance(dialog,QInputDialog);dialog.setIntValue(5);dialog.accept()
                QTimer.singleShot(100,accept_minutes);pet.focus();assert model.focus_minutes==5
                pet.grab().save(str(test_output))
            finally: pet.quit()
        QTimer.singleShot(4200,verify)
    app.exec()
