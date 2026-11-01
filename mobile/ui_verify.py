from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:5080',wait_until='networkidle')
    page.locator('.result').first.wait_for()
    assert page.locator('body').evaluate('(e)=>e.scrollWidth<=innerWidth')
    Path('screenshots').mkdir(exist_ok=True)
    page.screenshot(path='screenshots/mobile-library.png',full_page=False)
    page.locator('#query').fill('涉密计算机')
    page.locator('#searchForm button').click()
    page.wait_for_function("document.getElementById('summary').textContent.includes('匹配')")
    assert page.locator('.result').count()>0
    page.locator('[data-view="platform"]').click()
    assert page.locator('#loginForm').is_visible()
    page.screenshot(path='screenshots/mobile-platform.png',full_page=True)
    page.locator('[data-view="xg"]').click()
    assert page.locator('#xg h1').inner_text()=='实训安全准入'
    page.locator('[data-view="tools"]').click()
    assert page.get_by_role('link',name='下载脚本',exact=True).is_visible()
    page.screenshot(path='screenshots/mobile-tools.png',full_page=True)
    # Adapter fixture: existing selected wrong checkbox is deselected;
    # correct answer is checked, unknown next question stops without submission.
    page.goto('http://127.0.0.1:5080',wait_until='networkidle')
    page.set_content('''<div class="type">多选题</div><div class="content">1、维护国家安全人人有责。尤其是大学生，在日常生活中应当注意事项是____。</div><div id="options"></div><button class="next btn">下一题</button><button id="submit">提交</button>''')
    page.evaluate('''()=>{for(const letter of 'ABCDE'){let o=document.createElement('div');o.className='option';o.innerHTML=`<label class="el-checkbox"><span class="el-checkbox__input ${letter==='E'?'is-checked':''}"></span><span class="el-checkbox__label">${letter}.选项</span></label>`;o.querySelector('label').onclick=()=>o.querySelector('.el-checkbox__input').classList.toggle('is-checked');document.querySelector('#options').append(o)}window.submitted=false;document.querySelector('#submit').onclick=()=>window.submitted=true;document.querySelector('.next').onclick=()=>document.querySelector('.content').innerText='未匹配的下一道题';}''')
    page.add_script_tag(content=Path('web/adapter.js').read_text(encoding='utf-8'))
    page.locator('div').filter(has=page.locator('section')).count()
    page.get_by_role('button',name='开始填写',exact=True).click()
    page.wait_for_function("document.querySelector('div[style*=fixed]').shadowRoot.querySelector('p').textContent.includes('未匹配')",timeout=10000)
    assert page.locator('.is-checked').count()==4
    assert not page.evaluate('window.submitted')
    assert not errors,errors
    browser.close()
print('UI verified: 390px layout, navigation, search, adapter matching/stop/no-submit; no page errors')
