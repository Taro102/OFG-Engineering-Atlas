#!/usr/bin/env python3
"""OFG-EA MRE2 deterministic encoding, hashing, chunking and verification."""
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path

CODEC='OFG-EA-MRE2'

def canonical_bytes(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode('utf-8')

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_file(path, block=1024*1024):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(block),b''): h.update(b)
    return h.hexdigest()

def envelope(payload, shard_id, shard_type, master_epoch=2, logical_scope='GLOBAL', generation_scope='T1-G2', baseline_id='OFG-EA-B000-REV3-REVW3-REVS-2031-04-19', configuration_cut='2031-04-19', sequence=1, sequence_total=1, depends_on=None, previous_hash=None):
    payload_hash=sha256_bytes(canonical_bytes(payload))
    return {'codec':CODEC,'schema':'2.0.0','shard_id':shard_id,'shard_type':shard_type,'master_epoch':master_epoch,'logical_scope':logical_scope,'generation_scope':generation_scope,'baseline_id':baseline_id,'configuration_cut':configuration_cut,'sequence':sequence,'sequence_total':sequence_total,'depends_on':depends_on or [],'previous_hash':previous_hash,'payload_hash':payload_hash,'payload':payload}

def verify_envelope(e):
    if e.get('codec') != CODEC: return False,'codec_mismatch'
    got=sha256_bytes(canonical_bytes(e.get('payload')))
    return (got==e.get('payload_hash'), 'ok' if got==e.get('payload_hash') else f'payload_hash_mismatch:{got}')

def chunk_jsonl(path, outdir, prefix='SHARD', max_bytes=2_000_000, shard_type='DATA'):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    chunks=[]; rows=[]; nbytes=0
    with open(path,'r',encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            obj=json.loads(line); b=len(canonical_bytes(obj))+1
            if rows and nbytes+b>max_bytes:
                chunks.append(rows); rows=[]; nbytes=0
            rows.append(obj); nbytes+=b
    if rows: chunks.append(rows)
    prev=None; outputs=[]
    total=len(chunks)
    for i,payload in enumerate(chunks,1):
        sid=f'{prefix}-{i:04d}'
        env=envelope(payload,sid,shard_type,sequence=i,sequence_total=total,previous_hash=prev)
        out=outdir/f'{sid}.json'
        out.write_bytes(canonical_bytes(env))
        prev=sha256_file(out)
        outputs.append({'path':str(out),'sha256':prev,'payload_hash':env['payload_hash'],'sequence':i})
    return outputs

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    v=sub.add_parser('verify'); v.add_argument('path')
    h=sub.add_parser('hash'); h.add_argument('path')
    c=sub.add_parser('chunk-jsonl'); c.add_argument('path'); c.add_argument('outdir'); c.add_argument('--prefix',default='SHARD'); c.add_argument('--max-bytes',type=int,default=2_000_000); c.add_argument('--type',default='DATA')
    a=ap.parse_args()
    if a.cmd=='hash': print(json.dumps({'path':a.path,'sha256':sha256_file(a.path)},separators=(',',':')))
    elif a.cmd=='verify':
        e=json.load(open(a.path,encoding='utf-8')); ok,msg=verify_envelope(e); print(json.dumps({'ok':ok,'message':msg},separators=(',',':'))); raise SystemExit(0 if ok else 2)
    else: print(json.dumps(chunk_jsonl(a.path,a.outdir,a.prefix,a.max_bytes,a.type),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
