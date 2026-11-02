# -*- coding: utf-8 -*-
"""Bounded ArcMap geoprocessing actions. Python 2.7, MIT fox."""
import os,math

def describe(path):
    import arcpy
    if not arcpy.Exists(path):raise ValueError('Input dataset not found')
    d=arcpy.Describe(path);sr=getattr(d,'spatialReference',None)
    result={'path':path,'dataType':d.dataType,'shapeType':getattr(d,'shapeType',None),
            'count':int(arcpy.GetCount_management(path).getOutput(0)),
            'fields':[{'name':f.name,'type':f.type} for f in arcpy.ListFields(path)],
            'spatialReference':sr.name if sr else None,'srType':sr.type if sr else None,
            'linearUnit':getattr(sr,'linearUnitName',None) if sr else None}
    if hasattr(d,'extent'):
        e=d.extent;result['extent']=[e.XMin,e.YMin,e.XMax,e.YMax]
    if result['shapeType']=='Polygon':
        with arcpy.da.SearchCursor(path,['SHAPE@AREA']) as rows:result['areaNativeUnits']=sum(r[0] for r in rows)
    with arcpy.da.SearchCursor(path,[f.name for f in arcpy.ListFields(path) if f.type not in ('Geometry','Blob','Raster')]) as rows:
        result['sampleRows']=[]
        for i,row in enumerate(rows):
            if i>=12:break
            result['sampleRows'].append(list(row))
    return result

def new_output(path):
    import arcpy
    if not path or not path.lower().endswith('.shp'):raise ValueError('Choose a NEW .shp output')
    if not os.path.isdir(os.path.dirname(os.path.abspath(path))):raise ValueError('Output folder does not exist')
    # Reject stale sidecars as well as complete existing datasets.
    stem=os.path.splitext(path)[0]
    if arcpy.Exists(path) or any(os.path.exists(stem+e) for e in ('.shp','.shx','.dbf','.prj','.cpg','.sbn','.sbx','.shp.xml')):raise ValueError('Output or sidecar already exists; choose a new name')
    return path

def number(value):
    v=float(value)
    if math.isnan(v) or math.isinf(v) or v==0 or abs(v)>1000000:raise ValueError('Distance must be finite, nonzero and at most 1000000 metres')
    return v

def execute(req):
    import arcpy
    arcpy.env.overwriteOutput=False
    action=req['action'];source=req.get('input','');info=describe(source)
    if action=='inspect_dataset':return info
    if info['shapeType'] not in ('Point','Multipoint','Polyline','Polygon'):raise ValueError('Choose a feature dataset')
    output=new_output(req.get('output',''));warnings=[]
    if action in ('buffer','multiple_ring_buffer'):
        if info['srType']!='Projected' or info['linearUnit'] not in ('Meter','Metre'):raise ValueError('Buffer requires a known projected coordinate system in metres; project a COPY first')
        dissolve=req.get('dissolve','NONE')
        if dissolve not in ('NONE','ALL'):raise ValueError('Dissolve must be NONE or ALL')
        if action=='buffer':
            distance=number(req.get('distance',0));side=req.get('side','FULL');end=req.get('end','ROUND')
            if side not in ('FULL','LEFT','RIGHT','OUTSIDE_ONLY') or end not in ('ROUND','FLAT'):raise ValueError('Invalid buffer side/end')
            if side in ('LEFT','RIGHT') and info['shapeType']!='Polyline':raise ValueError('LEFT/RIGHT require lines')
            if side=='OUTSIDE_ONLY' and info['shapeType']!='Polygon':raise ValueError('OUTSIDE_ONLY requires polygons')
            if end=='FLAT' and info['shapeType']!='Polyline':raise ValueError('FLAT requires lines')
            if distance<0 and info['shapeType']!='Polygon':raise ValueError('Negative distance requires polygons')
            arcpy.Buffer_analysis(source,output,str(distance)+' Meters',side,end,dissolve,'','PLANAR')
        else:
            values=req.get('distances',[])
            if not isinstance(values,list) or not 1<=len(values)<=10:raise ValueError('Choose 1-10 ring distances')
            values=sorted(set(number(x) for x in values))
            if values[0]<=0:raise ValueError('Ring distances must be positive')
            outside=req.get('outside_only',False)
            if outside and info['shapeType']!='Polygon':raise ValueError('Outside-only rings require polygons')
            arcpy.MultipleRingBuffer_analysis(source,output,values,'Meters','distance',dissolve,'OUTSIDE_ONLY' if outside else 'FULL')
    else:
        other=req.get('overlay','');other_info=describe(other)
        a=arcpy.Describe(source).spatialReference;b=arcpy.Describe(other).spatialReference
        if a.name=='Unknown' or b.name=='Unknown':
            if not (a.name==b.name=='Unknown' and req.get('allow_unknown_coordinates') is True):raise ValueError('Unknown coordinates: explicitly confirm both datasets use the same local coordinates')
            warnings.append('Both coordinate systems are unknown. Output is a local-coordinate demonstration; metre/area interpretation is not verified.')
        elif a.exportToString()!=b.exportToString():raise ValueError('Coordinate systems differ: project a COPY explicitly before overlay')
        if action in ('union','update','symdiff') and (info['shapeType']!='Polygon' or other_info['shapeType']!='Polygon'):raise ValueError('This operation requires two polygon datasets')
        if action=='union':arcpy.Union_analysis([source,other],output,'ALL','','GAPS')
        elif action=='intersect':arcpy.Intersect_analysis([source,other],output,'ALL','','INPUT')
        elif action=='identity':arcpy.Identity_analysis(source,other,output,'ALL')
        elif action=='update':arcpy.Update_analysis(source,other,output,'BORDERS')
        elif action=='erase':arcpy.Erase_analysis(source,other,output)
        elif action=='symdiff':arcpy.SymDiff_analysis(source,other,output,'ALL')
        else:raise ValueError('Unsupported geoprocessing action')
    result=describe(output);result.update(warnings=warnings,messages=arcpy.GetMessages());return result
