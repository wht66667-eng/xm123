"""Reviewable ArcMap operations UI. MIT fox."""
import json
from pathlib import Path
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QComboBox,QFileDialog,QPlainTextEdit,QTabWidget,QScrollArea,QCheckBox
from arcmap_bridge import ArcMap
from task_journal import TaskJournal

def build_mxd(window):
    from qt_assistant import text,btn,card
    page=QWidget();v=QVBoxLayout(page);v.setContentsMargins(0,0,0,0);bridge=ArcMap();journal=TaskJournal(window.data/'task-history');plan=[None]
    v.addWidget(text('ArcMap 10.8 · 地图工作台','title'));v.addWidget(text('独立ArcPy进程执行；先预览任务，再执行。输出必须是新文件。','muted'))
    controls=QHBoxLayout();controls.addWidget(btn('检测环境',lambda:window.start_task(lambda:json.dumps(journal.run('ArcMap环境检测',{},lambda:bridge.execute('detect')),ensure_ascii=False,indent=2))));controls.addWidget(btn('打开 ArcMap',lambda:window.status.setText(bridge.launch())));v.addLayout(controls)
    f,fields=card();v.addWidget(f);fields.addWidget(text('选择操作','muted'));action=QComboBox()
    for label,key in [('读取MXD图层与数据框','inspect_mxd'),('导出地图为PDF','export_pdf'),('另存MXD副本','copy_mxd')]:action.addItem(label,key)
    fields.addWidget(action);source=QLineEdit();source.setPlaceholderText('选择已有的 .mxd 地图文件');fields.addWidget(source)
    def choose_source():
        value=QFileDialog.getOpenFileName(window,'选择地图文件','','ArcMap地图 (*.mxd)')[0]
        if value:source.setText(value)
    fields.addWidget(btn('选择地图文件',choose_source));output=QLineEdit();output.setPlaceholderText('导出/另存时选择新输出文件');fields.addWidget(output)
    def choose_output():
        ext='PDF (*.pdf)' if action.currentData()=='export_pdf' else 'ArcMap地图 (*.mxd)';value=QFileDialog.getSaveFileName(window,'选择新的输出文件','',ext)[0]
        if value:output.setText(value)
    fields.addWidget(btn('选择输出位置',choose_output));preview=QPlainTextEdit();preview.setReadOnly(True);preview.setMaximumHeight(150);v.addWidget(preview)
    def prepare():
        src=Path(source.text()).resolve();kind=action.currentData()
        if not src.is_file() or src.suffix.lower()!='.mxd':window.status.setText('先选择已有MXD文件。');return
        params={'mxd':str(src)}
        if kind!='inspect_mxd':
            target=Path(output.text()).resolve();ext='.pdf' if kind=='export_pdf' else '.mxd'
            if not output.text() or target.exists() or target.suffix.lower()!=ext:window.status.setText('输出必须是扩展名匹配、尚不存在的新文件。');return
            params['output']=str(target)
        plan[0]=(kind,params);preview.setPlainText(json.dumps({'操作':action.currentText(),'参数':params,'说明':'读取磁盘上已保存的地图；不使用CURRENT，不自动保存当前ArcMap窗口。'},ensure_ascii=False,indent=2));execute.setEnabled(True)
    def run():
        if not plan[0] or window.busy:return
        kind,params=plan[0];execute.setEnabled(False)
        window.start_task(lambda:json.dumps(journal.run('ArcMap '+kind,params,lambda:bridge.execute(kind,**params)),ensure_ascii=False,indent=2))
    def invalidate(*args):plan[0]=None;execute.setEnabled(False)
    row=QHBoxLayout();row.addWidget(btn('预览任务',prepare));execute=btn('执行已预览任务',run,'primary');execute.setEnabled(False);row.addWidget(execute);row.addWidget(btn('停止 ArcPy 任务',bridge.cancel));v.addLayout(row)
    source.textChanged.connect(invalidate);output.textChanged.connect(invalidate);action.currentIndexChanged.connect(invalidate)
    v.addWidget(text('停止只终止本插件启动的ArcPy任务，不关闭ArcMap。写出中断时请检查部分输出。','muted'));v.addStretch();return page

def build_geoprocess(window):
    from qt_assistant import text,btn,card
    page=QWidget();v=QVBoxLayout(page);v.setContentsMargins(0,0,0,0);bridge=ArcMap();journal=TaskJournal(window.data/'task-history');plan=[None]
    v.addWidget(text('缓冲区与叠加分析','title'));v.addWidget(text('选择矢量数据，预览参数后执行。只写入新的Shapefile；缓冲距离单位为米。','muted'))
    request=QLineEdit();request.setPlaceholderText('例如：铁路右侧150米圆头缓冲，或公园200、500、1000米不融合');v.addWidget(request)
    def from_text():
        try:
            from gis_text import parse
            data=parse(request.text());action.setCurrentIndex(action.findData(data['action']))
            if 'distance' in data:distance.setText(str(data['distance']))
            if 'distances' in data:rings.setText(','.join(str(x) for x in data['distances']))
            for key,control in [('side',side),('end',end),('dissolve',dissolve)]:
                if key in data:control.setCurrentText(data[key])
            if 'outside_only' in data:outside.setChecked(data['outside_only'])
            invalidate();window.status.setText('已从文字填入参数，请核对输入、输出并预览；尚未执行。')
        except ValueError as e:window.status.setText(str(e))
    v.addWidget(btn('从文字填入参数',from_text))
    f,fields=card();v.addWidget(f);action=QComboBox()
    for label,key in [('检查数据 / 坐标系 / 属性','inspect_dataset'),('缓冲区 Buffer','buffer'),('多环缓冲区 Multiple Ring Buffer','multiple_ring_buffer'),('联合 Union','union'),('相交 Intersect','intersect'),('标识 Identity','identity'),('更新 Update','update'),('擦除 Erase','erase'),('交集取反 SymDiff','symdiff')]:action.addItem(label,key)
    fields.addWidget(action)
    source=QLineEdit();source.setPlaceholderText('输入要素 .shp');fields.addWidget(source)
    overlay=QLineEdit();overlay.setPlaceholderText('叠加要素 .shp（仅叠加分析需要）');fields.addWidget(overlay)
    def choose(line):
        path=QFileDialog.getOpenFileName(window,'选择Shapefile','','Shapefile (*.shp)')[0]
        if path:line.setText(path)
    row=QHBoxLayout();row.addWidget(btn('选择输入',lambda:choose(source)));row.addWidget(btn('选择叠加图层',lambda:choose(overlay)));fields.addLayout(row)
    output=QLineEdit();output.setPlaceholderText('新的输出 .shp（检查数据时不需要）');fields.addWidget(output)
    def choose_output():
        path=QFileDialog.getSaveFileName(window,'选择新输出','','Shapefile (*.shp)')[0]
        if path:output.setText(path)
    fields.addWidget(btn('选择输出',choose_output));options=QWidget();ov=QVBoxLayout(options);ov.setContentsMargins(0,0,0,0)
    distance=QLineEdit('100');distance.setPlaceholderText('单次缓冲距离，可为负值；米');ov.addWidget(text('单次距离 / 多环距离（逗号分隔，米）','muted'));ov.addWidget(distance)
    rings=QLineEdit('200,500,1000');ov.addWidget(rings);side=QComboBox();side.addItems(['FULL','LEFT','RIGHT','OUTSIDE_ONLY']);end=QComboBox();end.addItems(['ROUND','FLAT']);dissolve=QComboBox();dissolve.addItems(['NONE','ALL']);row=QHBoxLayout()
    for label,control in [('侧类型',side),('末端',end),('融合',dissolve)]:row.addWidget(text(label,'muted'));row.addWidget(control)
    ov.addLayout(row);outside=QCheckBox('多环仅保留面要素外围（不含原面）');ov.addWidget(outside);fields.addWidget(options)
    unknown=QCheckBox('已核对：两个未知坐标数据来自同一套局部坐标（仅演示叠加）');fields.addWidget(unknown)
    preview=QPlainTextEdit();preview.setReadOnly(True);preview.setMinimumHeight(120);v.addWidget(preview)
    def invalidate(*args):plan[0]=None;execute.setEnabled(False)
    def update_options(*args):
        kind=action.currentData();is_buffer=kind in ('buffer','multiple_ring_buffer');options.setVisible(is_buffer);distance.setVisible(kind=='buffer');rings.setVisible(kind=='multiple_ring_buffer');side.setEnabled(kind=='buffer');end.setEnabled(kind=='buffer');outside.setVisible(kind=='multiple_ring_buffer');overlay.setEnabled(not is_buffer and kind!='inspect_dataset');unknown.setVisible(not is_buffer and kind!='inspect_dataset');invalidate()
    def prepare():
        invalidate()
        try:
            kind=action.currentData();src=Path(source.text()).resolve()
            if not src.is_file() or src.suffix.lower()!='.shp':raise ValueError('请选择完整Shapefile的.shp文件。')
            params={'input':str(src)}
            if kind!='inspect_dataset':
                target=Path(output.text()).resolve()
                if not output.text() or target.suffix.lower()!='.shp' or target.exists() or not target.parent.is_dir():raise ValueError('请选择尚不存在的.shp输出，父文件夹须已存在。')
                params['output']=str(target)
            if kind=='buffer':params.update(distance=float(distance.text()),side=side.currentText(),end=end.currentText(),dissolve=dissolve.currentText())
            elif kind=='multiple_ring_buffer':params.update(distances=[float(x.strip()) for x in rings.text().split(',')],dissolve=dissolve.currentText(),outside_only=outside.isChecked())
            elif kind!='inspect_dataset':
                other=Path(overlay.text()).resolve()
                if not other.is_file() or other.suffix.lower()!='.shp':raise ValueError('请选择叠加要素的.shp文件。')
                params.update(overlay=str(other),allow_unknown_coordinates=unknown.isChecked())
            plan[0]=(kind,params);preview.setPlainText(json.dumps({'操作':action.currentText(),'参数':params,'注意':'缓冲区要求已知的米制投影；叠加坐标系须一致。未知坐标不推断真实位置或平方米。'},ensure_ascii=False,indent=2));execute.setEnabled(True)
        except (ValueError,OSError) as e:window.status.setText(str(e))
    def run():
        if not plan[0] or window.busy:return
        kind,params=plan[0];invalidate();window.start_task(lambda:json.dumps(journal.run('ArcMap '+kind,params,lambda:bridge.execute(kind,**params)),ensure_ascii=False,indent=2))
    row=QHBoxLayout();row.addWidget(btn('预览参数',prepare));execute=btn('执行已预览分析',run,'primary');execute.setEnabled(False);row.addWidget(execute);row.addWidget(btn('停止分析',bridge.cancel));v.addLayout(row)
    for control in (source,overlay,output,distance,rings):control.textChanged.connect(invalidate)
    for control in (side,end,dissolve):control.currentIndexChanged.connect(invalidate)
    unknown.toggled.connect(invalidate);outside.toggled.connect(invalidate);action.currentIndexChanged.connect(update_options);update_options();v.addStretch()
    window.arcmap_gp_controls={'action':action,'source':source,'overlay':overlay,'output':output,'distance':distance,'rings':rings,'execute':execute,'prepare':prepare,'preview':preview}
    return page

def build_arcmap(window):
    tabs=QTabWidget()
    for label,page in [('地图文档',build_mxd(window)),('空间分析',build_geoprocess(window))]:
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(page);tabs.addTab(scroll,label)
    return tabs
