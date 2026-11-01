import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from school_select import filter_schools,select_school
import fox_config

class Tests(unittest.TestCase):
    def test_school_retry_and_confirmation(self):
        data={'data':{'result':[{'name':'南京学校','code':'nj'},{'name':'苏州学校','code':'sz'}]}}
        replies=iter(['0','2','n','1','y'])
        self.assertEqual(select_school('',data,lambda _:next(replies),lambda _:None),'nj')
        replies=iter(['苏州','1','y'])
        self.assertEqual(select_school('不存在',data,lambda _:next(replies),lambda _:None),'sz')
        self.assertEqual(filter_schools(data['data']['result'],'苏州')[0]['code'],'sz')
    def test_env_defaults_and_no_override(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'.env';file.write_text('FOX_PORT="6090"\nFOX_SCHOOL_KEYWORD="南京"\n',encoding='utf-8')
            with patch.object(fox_config,'config_path',return_value=file),patch.dict(os.environ,{'FOX_PORT':'5080'},clear=True):
                fox_config.load_env()
                self.assertEqual(os.environ['FOX_PORT'],'5080')
                self.assertEqual(os.environ['FOX_SCHOOL_KEYWORD'],'南京')
                self.assertEqual(fox_config.read_int('FOX_PORT',5080,1,65535),5080)
                os.environ['FOX_PORT']='99999'
                with self.assertRaises(ValueError):fox_config.read_int('FOX_PORT',5080,1,65535)

if __name__=='__main__':unittest.main()
