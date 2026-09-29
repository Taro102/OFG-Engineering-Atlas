#!/usr/bin/env python3
"""Ingest a worker return into the local OFG migration bundle without global semantic merge."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
ROOT_DEFAULT=Path(__file__).resolve().parents[1]

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def parse(text):
    s=text.strip()
    if s.startswith('```'):
        s=re.sub(r'^```(?:json)?\s*','',s)
        s=re.sub(r'\s*```\s*$','',s)
    try:return json.loads(s)
    except Exception:return None

def deep_find(obj,key):
    if isinstance(obj,dict):
        if key in obj:return obj[key]
        for v in obj.values():
            r=deep_find(v,key)
            if r is not None:return r
    elif isinstance(obj,list):
        for v in obj:
            r=deep_find(v,key)
            if r is not None:return r
    return None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--root',default=str(ROOT_DEFAULT)); ap.add_argument('--no-reindex',action='store_true'); a=ap.parse_args()
    root=Path(a.root).resolve(); src=Path(a.file).resolve(); text=src.read_text(encoding='utf-8',errors='ignore'); obj=parse(text)
    if obj is None:
        print(json.dumps({'status':'FAIL','error':'not_valid_json_or_json_fence'})); raise SystemExit(2)
    pid=deep_find(obj,'RETURN_PACKET_ID') or deep_find(obj,'PACKAGE_ID') or deep_find(obj,'CONTINUATION_PACKET_ID')
    cycle=deep_find(obj,'CYCLE_ID'); baseline=deep_find(obj,'INPUT_BASELINE_ID'); cut=deep_find(obj,'CONFIGURATION_CUT')
    if not pid or 'RETURN' not in str(pid):
        print(json.dumps({'status':'FAIL','error':'return_packet_id_not_detected','detected':pid})); raise SystemExit(2)
    expected_baseline=json.load(open(root/'state/current_working_state.json',encoding='utf-8'))['baseline_id']
    if baseline and baseline!=expected_baseline:
        print(json.dumps({'status':'FAIL','error':'baseline_mismatch','packet':baseline,'expected':expected_baseline})); raise SystemExit(2)
    if cut and cut!='2031-04-19':
        print(json.dumps({'status':'FAIL','error':'configuration_cut_mismatch','packet':cut,'expected':'2031-04-19'})); raise SystemExit(2)
    raw=root/'working_raw'/'ingested'; raw.mkdir(parents=True,exist_ok=True)
    by=root/'working_raw'/'by_package'; by.mkdir(parents=True,exist_ok=True)
    ext=src.suffix if src.suffix else '.txt'; h=sha(src)
    rawdest=raw/(h+ext); bydest=by/(str(pid)+ext)
    if not rawdest.exists(): shutil.copy2(src,rawdest)
    disposition='NEW'
    if bydest.exists():
        old=sha(bydest)
        if old==h: disposition='IDEMPOTENT_DUPLICATE'
        else:
            q=root/'working_raw'/'quarantine'; q.mkdir(parents=True,exist_ok=True)
            qdest=q/(str(pid)+'__'+h[:12]+ext); shutil.copy2(src,qdest)
            print(json.dumps({'status':'QUARANTINE','reason':'same_packet_id_different_hash','package_id':pid,'old_hash':old,'new_hash':h,'path':str(qdest)},ensure_ascii=False,indent=2)); raise SystemExit(3)
    else: shutil.copy2(src,bydest)
    if not a.no_reindex:
        subprocess.run([sys.executable,str(root/'programs'/'ofg_index.py'),'--root',str(root)],check=True,stdout=subprocess.DEVNULL)
    print(json.dumps({'status':'PASS','disposition':disposition,'package_id':pid,'cycle_id':cycle,'sha256':h,'raw_path':str(rawdest.relative_to(root)),'package_path':str(bydest.relative_to(root)),'semantic_merge_performed':False},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
