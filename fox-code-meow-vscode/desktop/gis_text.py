"""Local natural-language parameter templates; no model/network/execution."""
import re
def parse(text):
    if not isinstance(text,str) or not text.strip() or len(text)>2000:raise ValueError('请输入1–2000字的GIS任务')
    actions=[('交集取反','symdiff'),('对称差','symdiff'),('相交','intersect'),('交集','intersect'),('联合','union'),('标识','identity'),('更新','update'),('擦除','erase')]
    for word,action in actions:
        if word in text:return {'action':action}
    if '检查' in text or '坐标系' in text:return {'action':'inspect_dataset'}
    if not any(w in text for w in ('缓冲','多环','三环')) and not ('公园' in text and '不融合' in text):raise ValueError('目前识别数据检查、缓冲区和六种叠加；请明确操作名称')
    # Only explicit metre distances. Never infer units from unlabeled digits.
    groups=re.findall(r'(-?\d+(?:\.\d+)?(?:\s*[,，、/]\s*-?\d+(?:\.\d+)?)*)(?:\s*)(?:米|m\b)',text,re.I)
    values=[float(n) for g in groups for n in re.findall(r'-?\d+(?:\.\d+)?',g)]
    if not values:raise ValueError('请写明距离及“米”单位，例如200、500、1000米')
    if any(v==0 or abs(v)>1000000 for v in values):raise ValueError('距离须非零且不超过1000000米')
    multi=len(values)>1 or '多环' in text or '三环' in text
    if multi:
        if len(values)<2 or len(values)>10 or min(values)<=0:raise ValueError('多环需要2–10个正距离')
        return {'action':'multiple_ring_buffer','distances':sorted(set(values)),'dissolve':'NONE' if any(w in text for w in ('不融合','不合并')) else 'ALL','outside_only':'外围' in text or '不含原面' in text}
    side='RIGHT' if '右侧' in text else 'LEFT' if '左侧' in text else 'OUTSIDE_ONLY' if '外围' in text or '不含原面' in text else 'FULL'
    return {'action':'buffer','distance':values[0],'side':side,'end':'FLAT' if '平头' in text or '平直' in text else 'ROUND','dissolve':'ALL' if '融合' in text and '不融合' not in text else 'NONE'}
