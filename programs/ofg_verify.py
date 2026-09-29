#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os
from pathlib import Path
ROOT_DEFAULT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT_DEFAULT));a=ap.parse_args();root=Path(a.root);mp=root/'manifests/bundle_manifest.json';m=json.load(open(mp,encoding='utf-8'));bad=[]
 for x in m['files']:
  p=root/x['path']
  if not p.exists():bad.append({'path':x['path'],'error':'missing'});continue
  s=sha(p)
  if s!=x['sha256']:bad.append({'path':x['path'],'error':'hash_mismatch','expected':x['sha256'],'actual':s})
 print(json.dumps({'status':'PASS' if not bad else 'FAIL','checked':len(m['files']),'errors':bad},ensure_ascii=False,indent=2));raise SystemExit(0 if not bad else 2)
if __name__=='__main__':main()
