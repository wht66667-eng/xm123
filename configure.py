from fox_config import load_env,configure,diagnostics

if __name__=='__main__':
    load_env()
    try:configure()
    except (ValueError,OSError) as e:print('配置未保存：',e)
    diagnostics()
