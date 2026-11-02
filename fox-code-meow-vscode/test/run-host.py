from pathlib import Path
import os, subprocess

root=Path(__file__).resolve().parents[1]
out=root/'test-artifacts';out.mkdir(exist_ok=True)
env=dict(os.environ);env.pop('ELECTRON_RUN_AS_NODE',None)
env['FOX_HOST_TEST_RESULT']=str(out/'host-result.json')
exe=Path(os.environ['LOCALAPPDATA'])/'Programs/Microsoft VS Code/Code.exe'
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
args=[str(exe),'--new-window','--skip-welcome','--skip-release-notes','--skip-add-to-recently-opened','--disable-updates','--disable-telemetry','--user-data-dir',str(out/'profile'),'--extensions-dir',str(out/'extensions'),'--extensionDevelopmentPath='+str(root),'--extensionTestsPath='+str(root/'test/host.cjs')]
result=subprocess.run(args,env=env,startupinfo=si,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
(out/'host-process.log').write_bytes(result.stdout)
print('Host exit code:',result.returncode)
if (out/'host-result.json').exists():print((out/'host-result.json').read_text())
else:print(result.stdout.decode('utf-8',errors='replace')[-1500:])
