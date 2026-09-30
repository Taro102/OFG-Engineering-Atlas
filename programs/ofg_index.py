#!/usr/bin/env python3
"""Build a local SQLite catalog/index over the OFG migration bundle.
Default mode indexes all state records, raw worker returns, source metadata, and selected compact CSVs.
Use --include-large to stream-index DATA01/DATA02/site-work CSV row text as well.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,os,re,sqlite3,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from ofg_current import load_context,resolve_instance,effective,output_path,read,sha,canonical,require,historical,classify_origin
ROOT_DEFAULT=Path(__file__).resolve().parents[1]

def sha256_file(p,block=1024*1024):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(block),b''): h.update(b)
    return h.hexdigest()

def classify(rel):
    s=rel.lower()
    if s.startswith('state/'): return 'STATE'
    if 'worker_returns' in s: return 'WORKER_RETURN'
    if 'reference_raw/rev3_volumes' in s: return 'REV3_VOLUME'
    if 'reference_raw' in s: return 'REFERENCE_RAW'
    if s.startswith('programs/'): return 'PROGRAM'
    if s.startswith('manifests/'): return 'MANIFEST'
    return 'OTHER'

def init_db(db):
    c=db.cursor()
    c.executescript('''
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY,path TEXT UNIQUE,category TEXT,ext TEXT,size_bytes INTEGER,sha256 TEXT,package_id TEXT,task_id TEXT,cycle_id TEXT);
    CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY,source_path TEXT,dataset TEXT,record_key TEXT,record_type TEXT,object_id TEXT,system_id TEXT,event_date TEXT,state TEXT,text TEXT,json TEXT);
    CREATE TABLE IF NOT EXISTS edges(id INTEGER PRIMARY KEY,src TEXT,rel TEXT,dst TEXT,source_path TEXT,state TEXT,json TEXT);
    CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY,value_json TEXT);
    CREATE INDEX IF NOT EXISTS idx_records_key ON records(record_key);
    CREATE INDEX IF NOT EXISTS idx_records_object ON records(object_id);
    CREATE INDEX IF NOT EXISTS idx_records_system ON records(system_id);
    CREATE INDEX IF NOT EXISTS idx_records_date ON records(event_date);
    CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src);
    CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
    ''')
    try: c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(text, content="records", content_rowid="id")')
    except sqlite3.OperationalError: pass
    db.commit()

def json_text(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True)

def infer(obj):
    if not isinstance(obj,dict): return None,None,None,None,None
    keys={str(k).lower():v for k,v in obj.items()}
    pick=lambda names: next((keys[n] for n in names if n in keys and keys[n] not in (None,'')),None)
    rk=pick(['uid','id','asset_id','object_id','record_id','package_id','return_packet_id','edge_id','cycle','cycle_id','conflict_id'])
    typ=pick(['kind','record_type','event_type','package_type','artifact_type','subject'])
    oid=pick(['object_id','asset_id','object','target','uid'])
    sid=pick(['system_id','system'])
    date=pick(['date','event_date','historical_date','configuration_cut'])
    return *(str(x) if x is not None else None for x in (rk,typ,oid,sid,date)),

def add_record(db,source,dataset,obj,state=None):
    rk,typ,oid,sid,date=infer(obj if isinstance(obj,dict) else {})
    txt=json_text(obj) if not isinstance(obj,str) else obj
    cur=db.execute('INSERT INTO records(source_path,dataset,record_key,record_type,object_id,system_id,event_date,state,text,json) VALUES(?,?,?,?,?,?,?,?,?,?)',(source,dataset,rk,typ,oid,sid,date,state,txt,json_text(obj) if not isinstance(obj,str) else None))
    rid=cur.lastrowid
    try: db.execute('INSERT INTO records_fts(rowid,text) VALUES(?,?)',(rid,txt))
    except sqlite3.OperationalError: pass

def parse_jsonish_text(text):
    s=text.strip()
    if s.startswith('```'):
        s=re.sub(r'^```(?:json)?\s*','',s); s=re.sub(r'\s*```\s*$','',s)
    try:return json.loads(s)
    except Exception:return None

def docx_text(path):
    try:
        with zipfile.ZipFile(path) as z:
            xml=z.read('word/document.xml')
        root=ET.fromstring(xml)
        return '\n'.join(t.text or '' for t in root.iter() if t.tag.endswith('}t'))
    except Exception:return ''

def index_state(db,root):
    for p in sorted((root/'state').glob('*')):
        if p.suffix=='.json': add_record(db,str(p.relative_to(root)),p.stem,json.load(open(p,encoding='utf-8')),'HISTORICAL_COMPATIBILITY')
        elif p.suffix=='.jsonl':
            for n,line in enumerate(open(p,encoding='utf-8'),1):
                if line.strip(): add_record(db,str(p.relative_to(root)),p.stem,json.loads(line),None)

def index_worker_returns(db,root):
    d=root/'working_raw'/'by_package'
    if not d.exists(): return
    for p in sorted(d.iterdir()):
        if not p.is_file(): continue
        text=p.read_text(encoding='utf-8',errors='ignore'); obj=parse_jsonish_text(text)
        add_record(db,str(p.relative_to(root)),'worker_returns',obj if obj is not None else text,'RAW_RETURN')

def index_compact_reference(db,root,include_large=False,docs=False):
    ref=root/'reference_raw'
    for p in sorted(ref.rglob('*')):
        if not p.is_file(): continue
        rel=str(p.relative_to(root)); size=p.stat().st_size
        with open(p,'rb') as probe:
            if probe.read(64).startswith(b'version https://git-lfs.github.com/spec/v1'): continue
        if p.suffix.lower()=='.csv':
            if size>5_000_000 and not include_large: continue
            with open(p,encoding='utf-8-sig',errors='replace',newline='') as f:
                for i,row in enumerate(csv.DictReader(f),1):
                    row['_row_number']=i; add_record(db,rel,p.stem,row,'REFERENCE_ROW')
        elif p.suffix.lower() in ('.json','.geojson') and size<20_000_000:
            try: add_record(db,rel,p.stem,json.load(open(p,encoding='utf-8')),'REFERENCE_JSON')
            except Exception: pass
        elif p.suffix.lower()=='.txt' and size<5_000_000:
            add_record(db,rel,p.stem,p.read_text(encoding='utf-8',errors='ignore'),'REFERENCE_TEXT')
        elif docs and p.suffix.lower()=='.docx':
            t=docx_text(p)
            if t: add_record(db,rel,p.stem,t,'REFERENCE_DOCX_TEXT')

def index_edges(db,root):
    p=root/'state'/'provenance_bindings.jsonl'
    if p.exists():
        for line in open(p,encoding='utf-8'):
            if not line.strip(): continue
            o=json.loads(line); db.execute('INSERT INTO edges(src,rel,dst,source_path,state,json) VALUES(?,?,?,?,?,?)',(o.get('src'),o.get('rel'),o.get('dst'),str(p.relative_to(root)),o.get('state'),json_text(o)))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=str(ROOT_DEFAULT)); ap.add_argument('--db',default=None); ap.add_argument('--include-large',action='store_true'); ap.add_argument('--docs',action='store_true'); ap.add_argument('--candidate',action='store_true'); a=ap.parse_args()
    root=Path(a.root).resolve(); ctx=load_context(root,a.candidate); dbp=Path(a.db).resolve() if a.db else root/'generated'/'index.sqlite'
    root=ctx['root']; dbp=output_path(ctx,dbp); dbp.parent.mkdir(parents=True,exist_ok=True)
    if dbp.exists(): dbp.unlink()
    db=sqlite3.connect(dbp); init_db(db)
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p==dbp or any(x in ('.git','generated','__pycache__') for x in p.relative_to(root).parts): continue
        rel=str(p.relative_to(root)); raw=p.read_bytes() if p.stat().st_size<5_000_000 else None
        text=raw.decode('utf-8','ignore') if raw and p.suffix.lower() in ('.txt','.md','.json') else ''
        def mm(pattern):
            m=re.search(pattern,text); return m.group(1) if m else None
        db.execute('INSERT OR REPLACE INTO files(path,category,ext,size_bytes,sha256,package_id,task_id,cycle_id) VALUES(?,?,?,?,?,?,?,?)',(rel,classify(rel),p.suffix.lower(),p.stat().st_size,sha256_file(p),mm(r'"(?:PACKAGE_ID|RETURN_PACKET_ID)"\s*:\s*"([^"]+)"'),mm(r'"TASK_ID"\s*:\s*"([^"]+)"'),mm(r'"CYCLE_ID"\s*:\s*"([^"]+)"')))
    db.execute('INSERT INTO kv(key,value_json) VALUES(?,?)',('current_root',json.dumps({'state_root':ctx['state']['state_root_hash'],'base_head':ctx['state']['base_head']})))
    for section in ['working','reference','active']: add_record(db,'state/current_root.json','CURRENT_'+section,effective(ctx,section),'CURRENT_DERIVED_PROJECTION')
    index_state(db,root); index_worker_returns(db,root); index_compact_reference(db,root,a.include_large,a.docs); index_edges(db,root)
    db.execute('INSERT OR REPLACE INTO kv(key,value_json) VALUES(?,?)',('index_config',json.dumps({'root':str(root),'include_large':a.include_large,'docs':a.docs},separators=(',',':')))); db.commit()
    counts={t:db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['files','records','edges']}
    print(json.dumps({'status':'PASS','db':str(dbp),'counts':counts,'include_large':a.include_large,'docs':a.docs},ensure_ascii=False,separators=(',',':')))
if __name__=='__main__': main()
