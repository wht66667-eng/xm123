# -*- coding: utf-8 -*-
"""ArcMap 10.8 Python 2.7 bridge. Explicit operations only. MIT fox."""
from __future__ import print_function
import json,sys,os,traceback

def execute(request):
    import arcpy
    arcpy.env.overwriteOutput=False
    action=request.get('action')
    if action=='detect':return {'install':arcpy.GetInstallInfo(),'license':arcpy.ProductInfo()}
    if action in ('inspect_dataset','buffer','multiple_ring_buffer','union','intersect','identity','update','erase','symdiff'):
        from arcmap_gp import execute as geoprocess
        return geoprocess(request)
    if action not in ('inspect_mxd','export_pdf','copy_mxd'):raise ValueError('Unsupported ArcMap action')
    source=request.get('mxd','')
    if not os.path.isfile(source) or not source.lower().endswith('.mxd'):raise ValueError('Select an existing MXD file')
    document=arcpy.mapping.MapDocument(source)
    try:
        if action=='inspect_mxd':
            return {'title':document.title,'frames':[{'name':f.name,'spatialReference':f.spatialReference.name} for f in arcpy.mapping.ListDataFrames(document)],'layers':[{'name':l.name,'broken':l.isBroken,'visible':l.visible,'source':l.dataSource if l.supports('DATASOURCE') else None} for l in arcpy.mapping.ListLayers(document)]}
        target=request.get('output','')
        expected='.pdf' if action=='export_pdf' else '.mxd'
        if not target.lower().endswith(expected) or os.path.exists(target):raise ValueError('Output must be a NEW file with matching extension')
        if not os.path.isdir(os.path.dirname(os.path.abspath(target))):raise ValueError('Output folder does not exist')
        if action=='copy_mxd':document.saveACopy(target)
        else:arcpy.mapping.ExportToPDF(document,target,resolution=150)
        return {'output':target,'bytes':os.path.getsize(target)}
    finally:del document

if __name__=='__main__':
    result_path=sys.argv[2]
    try:
        with open(sys.argv[1],'rb') as f:request=json.loads(f.read().decode('utf-8'))
        result={'ok':True,'result':execute(request)}
    except Exception:result={'ok':False,'error':traceback.format_exc()}
    with open(result_path,'wb') as f:f.write(json.dumps(result,ensure_ascii=True).encode('utf-8'))
