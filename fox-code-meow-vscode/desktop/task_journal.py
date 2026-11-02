"""Local task audit records, with no source text or API secrets."""
from pathlib import Path
import json,uuid,datetime,threading
class TaskJournal:
    def __init__(self,root):self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.lock=threading.Lock()
    def run(self,label,parameters,operation):
        ident=uuid.uuid4().hex;path=self.root/(ident+'.json');record={'id':ident,'label':label,'parameters':parameters,'started':datetime.datetime.now().isoformat(timespec='seconds'),'status':'running'}
        def save():
            with self.lock:
                temp=path.with_suffix('.tmp');temp.write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf-8');temp.replace(path)
        save()
        try:
            result=operation();record.update(status='stopped' if isinstance(result,dict) and result.get('stopped') else 'completed',result=result);return result
        except Exception as e:record.update(status='stopped' if 'stopped' in str(e).lower() or '停止' in str(e) else 'failed',error=str(e));raise
        finally:record['finished']=datetime.datetime.now().isoformat(timespec='seconds');save()
