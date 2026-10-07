"""Generate portable BI sources, Power BI source projects and Tableau XML workbooks.

Run from any directory with Python 3.11+, pandas and numpy installed.
Native Power BI Desktop/Tableau validation is a separate, explicitly documented step.
"""
from pathlib import Path
import json, copy, zipfile, xml.etree.ElementTree as ET
import pandas as pd

BASE=Path(__file__).resolve().parents[1]

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2),encoding='utf-8')

def text(path,s):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(s,encoding='utf-8')

def xml(parent,tag,attrs=None,value=None):
    e=ET.SubElement(parent,tag,attrs or {})
    if value is not None:e.text=str(value)
    return e

def m_query(filename,frame):
    types=[]
    for c in frame:
        t='type date' if c in ['month_date','Date'] else 'Int64.Type' if pd.api.types.is_integer_dtype(frame[c]) else 'type number' if pd.api.types.is_numeric_dtype(frame[c]) else 'type text'
        types.append('{"'+c+'", '+t+'}')
    return '\n'.join(['let',f'    Source = Csv.Document(File.Contents(FolderPath & "{filename}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),','    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),','    Typed = Table.TransformColumnTypes(Headers, {'+', '.join(types)+'}, "en-US")','in','    Typed'])

def projection(table,name,measure=False):
    kind='Measure' if measure else 'Column'
    return {'field':{kind:{'Expression':{'SourceRef':{'Entity':table}},'Property':name}},'queryRef':f'{table}.{name}','nativeQueryRef':name}

def power_bi(root,frames,metrics,title):
    directory=root/'powerbi';name=root.name.replace('-','_')
    report=name+'.Report';model=name+'.SemanticModel'
    folder='C:\\Analytics\\'+root.name+'\\bi\\data\\'
    model_obj={'name':name,'compatibilityLevel':1567,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','tables':[],'relationships':[],'expressions':[{'name':'FolderPath','kind':'m','expression':'"'+folder.replace('"','""')+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(list(frames))},{'name':'__PBI_TimeIntelligenceEnabled','value':'0'}]}}
    for tab,frame in frames.items():
        columns=[]
        for c in frame:
            dtype='dateTime' if c in ['month_date','Date'] else 'int64' if pd.api.types.is_integer_dtype(frame[c]) else 'double' if pd.api.types.is_numeric_dtype(frame[c]) else 'string'
            spec={'name':c,'dataType':dtype,'sourceColumn':c,'summarizeBy':'sum' if tab=='FactMonthly' and dtype in ['int64','double'] else 'none'}
            if dtype=='dateTime':spec['formatString']='yyyy-mm-dd'
            if tab=='DimDate' and c=='Date':spec['isKey']=True
            if tab=='DimSegment':spec['isKey']=True
            if tab=='DimDate' and c=='Month':spec['sortByColumn']='MonthSort'
            columns.append(spec)
        query=m_query(tab+'.csv',frame)
        t={'name':tab,'columns':columns,'partitions':[{'name':tab,'mode':'import','source':{'type':'m','expression':query.splitlines()}}]}
        model_obj['model']['tables'].append(t);text(directory/'queries'/f'{tab}.pq',query+'\n')
    relations=[('month_date','DimDate','Date'),('segment','DimSegment','segment')]
    for from_col,to_table,to_col in relations:
        model_obj['model']['relationships'].append({'name':f'FactMonthly_{to_table}','fromTable':'FactMonthly','fromColumn':from_col,'toTable':to_table,'toColumn':to_col,'crossFilteringBehavior':'oneDirection'})
    measures=[]
    for m in metrics:
        expression=f"SUM('FactMonthly'[{m['numerator']}])"
        if m.get('denominator'):expression=f"DIVIDE({expression}, SUM('FactMonthly'[{m['denominator']}]))"
        measures.append({'name':m['label'],'expression':expression,'formatString':'0.0%' if m['unit']=='percent' else '$#,0' if m['unit']=='usd' else '#,0'})
    lead=metrics[0]['label']
    measures.extend([{'name':lead+' Previous Month','expression':f'CALCULATE([{lead}], DATEADD(\'DimDate\'[Date], -1, MONTH))','formatString':measures[0]['formatString']},{'name':lead+' MoM Change %','expression':f'DIVIDE([{lead}] - [{lead} Previous Month], [{lead} Previous Month])','formatString':'0.0%'}])
    model_obj['model']['tables'][0]['measures']=measures
    dump(directory/model/'model.bim',model_obj)
    dump(directory/model/'definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{'qnaEnabled':False}})
    dump(directory/(name+'.pbip'),{'$schema':'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':report}}],'settings':{'enableAutoRecovery':True}})
    dump(directory/report/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../'+model}}})
    definition=directory/report/'definition'
    dump(definition/'version.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json','version':'4.0.0'})
    dump(definition/'report.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.0.0/schema.json','themeCollection':{},'layoutOptimization':'None'})
    dump(definition/'pages/pages.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':['Overview'],'activePageName':'Overview'})
    page=definition/'pages/Overview'
    dump(page/'page.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json','name':'Overview','displayName':title+' (synthetic)','displayOption':'FitToPage','height':850,'width':1280})
    visuals=[]
    for i,m in enumerate(metrics):
        visuals.append((f'KPI_{i}','card',{'Values':{'projections':[projection('FactMonthly',m['label'],True)]}},20+i*310,30,290,120))
    visuals.append(('Trend','lineChart',{'Category':{'projections':[projection('DimDate','Month')]},'Y':{'projections':[projection('FactMonthly',lead,True)]}},20,190,800,300))
    visuals.append(('Comparison','clusteredBarChart',{'Category':{'projections':[projection('DimSegment','segment')]},'Y':{'projections':[projection('FactMonthly',lead,True)]}},850,190,410,300))
    visuals.append(('Segment_Filter','slicer',{'Values':{'projections':[projection('DimSegment','segment')]}},20,520,240,280))
    visuals.append(('Detail','tableEx',{'Values':{'projections':[projection('DimDate','Month'),projection('DimSegment','segment')]+[projection('FactMonthly',m['label'],True) for m in metrics]}},290,520,970,280))
    for i,(vid,vtype,query,x,y,w,h) in enumerate(visuals):
        dump(page/'visuals'/vid/'visual.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json','name':vid,'position':{'x':x,'y':y,'width':w,'height':h,'z':i,'tabOrder':i},'visual':{'visualType':vtype,'query':{'queryState':query},'drillFilterOtherVisuals':True}})
    text(directory/'measures.dax','\n\n'.join(f"// {m['name']}\n{m['name']} = {m['expression']}" for m in measures)+'\n')
    text(directory/'validation_query.dax', 'EVALUATE\nSUMMARIZECOLUMNS(\n'+',\n'.join(f'    "{m["label"]}", [{m["label"]}]' for m in metrics)+'\n)\n')
    dump(directory/'theme.json',{'name':'Analytics Portfolio','dataColors':['#2474A6','#E6A23C','#2C8D75','#9259A6'],'background':'#FFFFFF','foreground':'#17365D','tableAccent':'#2474A6'})
    dump(directory/'expected_totals.json',{m['label']:float(frames['FactMonthly'][m['numerator']].sum()/frames['FactMonthly'][m['denominator']].sum()) if m.get('denominator') else float(frames['FactMonthly'][m['numerator']].sum()) for m in metrics})
    text(directory/'README.md',f'''# Power BI source project\n\n**Status: source files generated; Power BI Desktop open, refresh, DAX execution and visual checks are pending. This is not a validated PBIX.**\n\n## Open and validate\n\n1. Use current Power BI Desktop on Windows. This package contains a `.pbip` shortcut, PBIR report definitions, and a TMSL semantic model.\n2. Extract the complete repository. Keep `bi/data` and `powerbi` folders intact. Open `{name}.pbip`. If the installed release requests a format upgrade, allow it and save a copy.\n3. Transform Data → Manage Parameters → set `FolderPath` to this repository's `bi/data` folder with a trailing separator. Default is `{folder}`. No credentials are required for the local synthetic CSV files.\n4. Close & Apply, then Refresh. The model has **FactMonthly**, a daily **DimDate**, and **DimSegment**, with single-direction many-to-one relationships. Mark DimDate[Date] as the date table if your release requires it for time intelligence.\n5. Check the Overview page: four KPI cards, month trend, segment comparison, segment slicer, and detail table. Verify the slicer affects the cards and trend.\n6. Run `validation_query.dax` in DAX Query View and compare with `expected_totals.json`. Filter each segment and compare with `outputs/monthly_kpis.csv`. Do not average monthly percentages.\n7. Import `theme.json` if desired. Save as `.pbix` via File → Save As after successful refresh and checks. Take screenshots of both Overview and Model view for the portfolio.\n\nIf the source project does not open in your installed version, use a new report and paste the supplied Power Query `.pq` files through Advanced Editor, create the FolderPath text parameter, then add the supplied DAX measures and relationships. Recreate the Overview layout using the visual list in `report_layout.md`. This fallback is a native build exercise, not evidence of a previously verified report.\n\nData is a prepared monthly aggregate, not transaction-level Power Query ETL. The Python pipeline owns transaction cleaning and complex cohort/risk/operational analysis.\n\nReferences: [Microsoft PBIP documentation](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [semantic model format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset), [PBIR report format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report).\n''')
    text(directory/'report_layout.md','# Overview layout\n\n| Visual | Fields |\n|---|---|\n'+''.join(f'| Card {i+1} | [{m["label"]}] |\n' for i,m in enumerate(metrics))+f'| Line chart | DimDate[Month], [{lead}] |\n| Bar chart | DimSegment[segment], [{lead}] |\n| Slicer | DimSegment[segment] |\n| Table | Month, segment, four measures |\n\nSort Month by MonthSort; use a zero baseline for bars. Display rates as percentages and monetary amounts as USD. Label the report synthetic.\n')

def tableau(root,frame,metrics,title):
    directory=root/'tableau';directory.mkdir(exist_ok=True);data_dir=directory/'Data';data_dir.mkdir(exist_ok=True)
    frame.to_csv(data_dir/'monthly.csv',index=False,float_format='%.8f')
    workbook=ET.Element('workbook',{'version':'9.3','source-platform':'mac','original-version':'9.3'})
    ds=xml(xml(workbook,'datasources'),'datasource',{'inline':'true','name':'analytics','caption':title+' (synthetic)','version':'9.3'})
    conn=xml(ds,'connection',{'class':'textscan','directory':'Data','filename':'monthly.csv','server':'','password':'','locale':'en_US'})
    relation=xml(conn,'relation',{'name':'monthly.csv','table':'[monthly.csv]','type':'table'})
    columns=xml(relation,'columns',{'header':'yes','separator':',','character-set':'UTF-8'})
    metadata=xml(conn,'metadata-records');source_columns=[]
    for i,c in enumerate(frame.columns):
        dtype='date' if c=='month_date' else 'integer' if pd.api.types.is_integer_dtype(frame[c]) else 'real' if pd.api.types.is_numeric_dtype(frame[c]) else 'string'
        role='measure' if dtype in ['integer','real'] else 'dimension'
        xml(columns,'column',{'datatype':dtype,'name':c,'ordinal':str(i)})
        rec=xml(metadata,'metadata-record',{'class':'column'})
        for tag,value in [('remote-name',c),('remote-type',7 if dtype=='date' else 3 if dtype=='integer' else 5 if dtype=='real' else 130),('local-name','['+c+']'),('parent-name','[monthly.csv]'),('remote-alias',c),('ordinal',i),('local-type',dtype),('aggregation','Sum' if role=='measure' else 'Count'),('contains-null','false')]:xml(rec,tag,value=value)
        cdef=xml(ds,'column',{'name':'['+c+']','caption':c.replace('_',' ').title(),'datatype':dtype,'role':role,'type':'quantitative' if role=='measure' else 'nominal'});source_columns.append(cdef)
    calcs=[]
    for i,m in enumerate(metrics):
        formula='SUM(['+m['numerator']+'])'
        if m.get('denominator'):formula=f'IF SUM([{m["denominator"]}]) = 0 THEN NULL ELSE {formula} / SUM([{m["denominator"]}]) END'
        name=f'Calculation_KPI_{i}'
        cdef=xml(ds,'column',{'name':'['+name+']','caption':m['label'],'datatype':'real','role':'measure','type':'quantitative','default-format':'p0.0%' if m['unit']=='percent' else '$#,##0' if m['unit']=='usd' else '#,##0'})
        xml(cdef,'calculation',{'class':'tableau','formula':formula});calcs.append(cdef)
    sheets=xml(workbook,'worksheets')
    allcols=source_columns+calcs
    def worksheet(name,kind):
        w=xml(sheets,'worksheet',{'name':name});table=xml(w,'table');view=xml(table,'view');xml(xml(view,'datasources'),'datasource',{'name':'analytics','caption':title+' (synthetic)'})
        deps=xml(view,'datasource-dependencies',{'datasource':'analytics'})
        for c in allcols:deps.append(copy.deepcopy(c))
        instances={}
        for c in allcols:
            key=c.get('name')[1:-1];calc=c.find('calculation') is not None;dimension=c.get('role')=='dimension'
            deriv='User' if calc else 'None' if dimension else 'Sum';prefix='usr' if calc else 'none' if dimension else 'sum';typ='nk' if dimension else 'qk';inst=f'[{prefix}:{key}:{typ}]';instances[key]=f'[analytics].{inst}'
            xml(deps,'column-instance',{'column':c.get('name'),'derivation':deriv,'name':inst,'pivot':'key','type':'nominal' if dimension else 'quantitative'})
        xml(view,'aggregation',{'value':'true'});xml(table,'style');pane=xml(xml(table,'panes'),'pane');xml(xml(pane,'view'),'breakdown',{'value':'auto'})
        mark=xml(pane,'mark',{'class':'Text' if kind.startswith('kpi') or kind=='detail' else 'Line' if kind=='trend' else 'Bar'})
        rows='';cols=''
        if kind.startswith('kpi'):
            index=int(kind[-1]);xml(xml(pane,'encodings'),'text',{'column':instances[f'Calculation_KPI_{index}']})
        elif kind=='trend':rows=instances['Calculation_KPI_0'];cols=instances['month']
        elif kind=='segment':rows=instances['segment'];cols=instances['Calculation_KPI_0']
        else:
            rows=instances['month']+' / '+instances['segment'];xml(xml(pane,'encodings'),'text',{'column':instances['Calculation_KPI_0']})
        xml(table,'rows',value=rows);xml(table,'cols',value=cols)
        return w
    names=[]
    for i,m in enumerate(metrics):names.append(m['label']);worksheet(m['label'],'kpi'+str(i))
    names.extend(['Monthly trend','Segment comparison','Monthly detail']);worksheet('Monthly trend','trend');worksheet('Segment comparison','segment');worksheet('Monthly detail','detail')
    dashboard=xml(xml(workbook,'dashboards'),'dashboard',{'name':'Overview'});xml(dashboard,'style');xml(dashboard,'size',{'maxheight':'900','minheight':'900','maxwidth':'1280','minwidth':'1280'})
    zones=xml(dashboard,'zones')
    for i,name in enumerate(names):
        if i<4:x=i*25000;y=0;w=25000;h=18000
        elif i==4:x=0;y=20000;w=65000;h=42000
        elif i==5:x=66000;y=20000;w=34000;h=42000
        else:x=0;y=64000;w=100000;h=36000
        z=xml(zones,'zone',{'h':str(h),'w':str(w),'x':str(x),'y':str(y),'id':str(i+1),'name':name,'type-v2':'sheet','show-title':'true','show-caption':'false','is-fixed':'true'});xml(z,'zone-style')
    windows=xml(workbook,'windows');win=xml(windows,'window',{'class':'dashboard','name':'Overview'});xml(win,'active',{'id':'1'})
    file=directory/(root.name+'.twb');ET.indent(workbook,space='  ');ET.ElementTree(workbook).write(file,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(directory/(root.name+'.twbx'),'w',zipfile.ZIP_DEFLATED) as z:
        z.write(file,file.name);z.write(data_dir/'monthly.csv','Data/monthly.csv')
    tds=copy.deepcopy(ds);tds.set('inline','false');tds_file=directory/(root.name+'.tds');ET.ElementTree(tds).write(tds_file,encoding='utf-8',xml_declaration=True)
    text(directory/'calculated_fields.txt','\n\n'.join(f'{m["label"]}\n{calcs[i].find("calculation").get("formula")}' for i,m in enumerate(metrics))+'\n')
    text(directory/'README.md',f'''# Tableau workbook sources\n\n**Status: generated XML and packaged CSV are structurally checked. Tableau Desktop/Public open, calculated-field execution, filter configuration, visual layout and native save are pending.**\n\nFiles: `.twb` workbook, `.twbx` packaged workbook containing `Data/monthly.csv`, `.tds` datasource, and explicit calculated-field definitions. The XML uses the documented sample workbook convention from Tableau's official document-api examples; newer Tableau releases may upgrade the format.\n\n## Native verification\n\n1. Open `{root.name}.twbx` in Tableau Desktop or Tableau Public Desktop. If the CSV is not located automatically, Edit Connection and select `Data/monthly.csv`.\n2. Check Month Date is a date; Month and Segment are dimensions; all numeric source columns are measures.\n3. Inspect the four aggregate calculated fields. Rates must divide summed numerators by summed denominators.\n4. Open Overview and verify four KPI worksheets, monthly trend, segment comparison and detail. Use the month field in chronological order and a zero baseline on the bar chart. The detail sheet initially shows the lead measure; add the remaining three measures through Measure Names/Measure Values as a practical extension.\n5. On Monthly detail, drag Segment to Filters, choose all values, then Show Filter. Apply to Worksheets → All Using This Data Source. Add the filter card to the Overview dashboard. Filter synchronization is intentionally a native validation/practice step.\n6. Reconcile KPI totals against `../powerbi/expected_totals.json` and each segment against `../outputs/monthly_kpis.csv`. Fix any native-open or rendering issue before describing this as a tested Tableau dashboard.\n7. Save a new packaged workbook in Tableau and take an Overview screenshot. Publishing to Tableau Public is optional and exposes the included synthetic data publicly.\n\nIf this generated workbook requires repair in your release, create a new workbook from the included CSV and reproduce the listed worksheets using `calculated_fields.txt`. No tested screenshots or native engine result is claimed by this source-generation step.\n\nReferences: [Tableau file formats](https://help.tableau.com/current/pro/desktop/en-us/environ_filesandfolders.htm), [official document-api examples](https://github.com/tableau/document-api-python/tree/master/samples).\n''')

def main():
    for root in [BASE]:
        if not root.is_dir():continue
        payload=json.loads((root/'outputs/dashboard_data.json').read_text());frame=pd.read_csv(root/'outputs/monthly_kpis.csv')
        frame=frame.drop(columns=[c for c in ['margin','default_rate','uptime','utilization'] if c in frame]);frame['month_date']=frame.month+'-01'
        dates=pd.date_range(frame.month_date.min(),pd.Timestamp(frame.month_date.max())+pd.offsets.MonthEnd(0),freq='D')
        calendar=pd.DataFrame({'Date':dates.strftime('%Y-%m-%d'),'Month':dates.strftime('%Y-%m'),'MonthSort':dates.year*100+dates.month,'Year':dates.year,'Quarter':dates.quarter})
        frames={'FactMonthly':frame,'DimDate':calendar,'DimSegment':pd.DataFrame({'segment':sorted(frame.segment.unique())})}
        for n,d in frames.items():
            target=root/'bi/data'/f'{n}.csv';target.parent.mkdir(parents=True,exist_ok=True);d.to_csv(target,index=False,float_format='%.8f')
        power_bi(root,frames,payload['metrics'],payload['title']);tableau(root,frame,payload['metrics'],payload['title']);print(root.name,'Power BI and Tableau sources created')

if __name__=='__main__':main()
