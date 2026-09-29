#!/usr/bin/env python3
"""Bounded retrieval CLI for OFG state and raw reference data."""
from __future__ import annotations
import argparse,csv,json,os,sqlite3,sys
from pathlib import Path
ROOT_DEFAULT=Path(__file__).resolve().parents[1]

def dbopen(root,dbpath=None):
    p=Path(dbpath) if dbpath else Path(root)/'ofg_master_state.sqlite'
    return sqlite3.connect(p),p

def query_db(db,q,limit,dataset=None,object_id=None):
    clauses=[]; args=[]
    if dataset: clauses.append('dataset=?'); args.append(dataset)
    if object_id: clauses.append('(object_id=? OR record_key=?)'); args.extend([object_id,object_id])
    where=(' AND '+' AND '.join(clauses)) if clauses else ''
    try:
        sql='SELECT r.id,r.source_path,r.dataset,r.record_key,r.record_type,r.object_id,r.system_id,r.event_date,r.state,r.text FROM records_fts f JOIN records r ON r.id=f.rowid WHERE records_fts MATCH ?'+where+' LIMIT ?'
        rows=db.execute(sql,[q]+args+[limit]).fetchall()
    except sqlite3.OperationalError:
        sql='SELECT id,source_path,dataset,record_key,record_type,object_id,system_id,event_date,state,text FROM records WHERE text LIKE ?'+where+' LIMIT ?'
        rows=db.execute(sql,['%'+q+'%']+args+[limit]).fetchall()
    cols=['id','source_path','dataset','record_key','record_type','object_id','system_id','event_date','state','text']
    return [dict(zip(cols,r)) for r in rows]

def raw_scan(root,terms,limit=50,path_contains=None):
    terms=[t.lower() for t in terms]; out=[]
    for p in Path(root,'reference_raw').rglob('*'):
        if not p.is_file() or p.suffix.lower() not in ('.csv','.txt','.json','.geojson'): continue
        rel=str(p.relative_to(root))
        if path_contains and path_contains.lower() not in rel.lower(): continue
        if p.suffix.lower()=='.csv':
            with open(p,encoding='utf-8-sig',errors='replace',newline='') as f:
                reader=csv.reader(f); header=next(reader,[])
                for n,row in enumerate(reader,2):
                    s=' | '.join(row)
                    if all(t in s.lower() for t in terms):
                        out.append({'source_path':rel,'line':n,'header':header,'row':row})
                        if len(out)>=limit:return out
        else:
            with open(p,encoding='utf-8',errors='ignore') as f:
                for n,line in enumerate(f,1):
                    if all(t in line.lower() for t in terms):
                        out.append({'source_path':rel,'line':n,'text':line.rstrip('\n')})
                        if len(out)>=limit:return out
    return out

def neighbors(db,node,limit=100):
    rows=db.execute('SELECT src,rel,dst,source_path,state,json FROM edges WHERE src=? OR dst=? LIMIT ?',(node,node,limit)).fetchall()
    return [{'src':r[0],'rel':r[1],'dst':r[2],'source_path':r[3],'state':r[4],'json':json.loads(r[5]) if r[5] else None} for r in rows]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=str(ROOT_DEFAULT)); ap.add_argument('--db',default=None)
    sub=ap.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('query'); q.add_argument('text'); q.add_argument('--limit',type=int,default=20); q.add_argument('--dataset'); q.add_argument('--object')
    s=sub.add_parser('scan'); s.add_argument('terms',nargs='+'); s.add_argument('--limit',type=int,default=50); s.add_argument('--path-contains')
    n=sub.add_parser('neighbors'); n.add_argument('node'); n.add_argument('--limit',type=int,default=100)
    st=sub.add_parser('state'); st.add_argument('--section',choices=['working','reference','active'],default='working')
    c=sub.add_parser('cycle'); c.add_argument('cycle')
    cf=sub.add_parser('conflicts'); cf.add_argument('--state')
    op=sub.add_parser('open'); op.add_argument('--contains')
    a=ap.parse_args(); root=Path(a.root)
    if a.cmd=='state':
        fn={'working':'current_working_state.json','reference':'reference_state.json','active':'active_cycle_c011.json'}[a.section]
        print(Path(root,'state',fn).read_text(encoding='utf-8')); return
    if a.cmd=='cycle':
        rows=[json.loads(x) for x in Path(root,'state','cycle_history.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        print(json.dumps([r for r in rows if r['cycle'].upper()==a.cycle.upper()],ensure_ascii=False,indent=2)); return
    if a.cmd=='conflicts':
        rows=[json.loads(x) for x in Path(root,'state','conflicts.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        if a.state: rows=[r for r in rows if a.state.lower() in r.get('state','').lower()]
        print(json.dumps(rows,ensure_ascii=False,indent=2)); return
    if a.cmd=='open':
        rows=[json.loads(x) for x in Path(root,'state','open_frontiers.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        if a.contains: rows=[r for r in rows if a.contains.lower() in r.get('subject','').lower()]
        print(json.dumps(rows,ensure_ascii=False,indent=2)); return
    if a.cmd=='scan': print(json.dumps(raw_scan(root,a.terms,a.limit,a.path_contains),ensure_ascii=False,indent=2)); return
    db,_=dbopen(root,a.db)
    if a.cmd=='query': print(json.dumps(query_db(db,a.text,a.limit,a.dataset,a.object),ensure_ascii=False,indent=2))
    elif a.cmd=='neighbors': print(json.dumps(neighbors(db,a.node,a.limit),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
