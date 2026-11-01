"""Copyright (c) 2026 fox. SPDX-License-Identifier: MIT"""
def filter_schools(schools,keyword):
    q=keyword.strip().casefold()
    return [s for s in schools if s.get('code') and q in str(s.get('name','')).casefold()]

def select_school(keyword,payload,input_fn=input,output=print):
    schools=payload.get('data',{}).get('result',[])
    if not isinstance(schools,list) or not schools:raise ValueError('平台没有返回学校列表，请检查网络后重试')
    while True:
        matches=filter_schools(schools,keyword)
        if not matches:
            output('没有匹配的学校，可重新输入关键词。')
            keyword=input_fn('学校关键词（留空显示全部；q退出）：').strip()
            if keyword.lower()=='q':raise SystemExit()
            continue
        for i,s in enumerate(matches,1):output(f'[{i}] {s["name"]}  ({s["code"]})')
        output(f'共 {len(matches)} 所学校；输入编号选择，s重新搜索，q退出。')
        choice=input_fn('学校编号：').strip()
        if choice.lower()=='q':raise SystemExit()
        if choice.lower()=='s':keyword=input_fn('学校关键词：').strip();continue
        if not choice.isdigit() or not 1<=int(choice)<=len(matches):output('请输入列表内的有效编号。');continue
        school=matches[int(choice)-1]
        if input_fn(f'确认选择「{school["name"]}」？[Y/n]：').strip().lower() in ('','y','yes'):
            output('已选择学校：'+school['name']);return school['code']
