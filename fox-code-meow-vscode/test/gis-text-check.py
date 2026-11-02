import sys
from pathlib import Path
sys.path.insert(0,str(Path('desktop').resolve()))
from gis_text import parse
assert parse('铁路右侧150米圆头缓冲')=={'action':'buffer','distance':150,'side':'RIGHT','end':'ROUND','dissolve':'NONE'}
assert parse('公园200、500、1000米不融合')['distances']==[200,500,1000]
assert parse('仓库500、80、120米外围三环')['outside_only']
assert parse('铁路300米平头缓冲')['end']=='FLAT'
assert parse('图层交集取反')['action']=='symdiff'
for text in ('缓冲150','缓冲nan米','多环100米','缓冲0米'):
 try:parse(text);raise AssertionError(text)
 except ValueError:pass
print('PASS local GIS text parameters, explicit metres, side/cap options, invalid input; zero execution')
