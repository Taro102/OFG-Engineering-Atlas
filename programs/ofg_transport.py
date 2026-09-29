#!/usr/bin/env python3
"""Create deterministic MRE2 transport envelopes for successor master/worker activation."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT_DEFAULT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT_DEFAULT/'programs'))
from ofg_codec import envelope, canonical_bytes

def load(p): return json.load(open(p,encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=str(ROOT_DEFAULT)); ap.add_argument('--thread',required=True,choices=['1','2','4','5']); ap.add_argument('--generation',type=int,default=2); ap.add_argument('--outdir',required=True); a=ap.parse_args()
    root=Path(a.root).resolve(); out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    capsule=load(root/'state'/f'T{a.thread}-G{a.generation}_REHYDRATION_CAPSULE.json')
    pieces=[
      ('CTRL',load(root/'state/migration_control.json')),
      ('ENCODING',load(root/'state/encoding_retrieval_spec.json')),
      ('CAPSULE',capsule),
      ('ACTIVE',load(root/'state/active_cycle_c011.json')),
      ('DISPATCH',load(root/'state/c011_dispatches.json'))
    ]
    prev=None; manifest=[]; total=len(pieces)
    for i,(typ,payload) in enumerate(pieces,1):
        sid=f'T{a.thread}-G{a.generation}-{typ}-{i:02d}'
        e=envelope(payload,sid,typ,master_epoch=2,logical_scope=f'T{a.thread}',generation_scope=f'T{a.thread}-G{a.generation}',sequence=i,sequence_total=total,depends_on=[] if i==1 else [manifest[-1]['shard_id']],previous_hash=prev)
        p=out/(sid+'.json'); p.write_bytes(canonical_bytes(e));
        import hashlib
        h=hashlib.sha256(p.read_bytes()).hexdigest(); prev=h
        manifest.append({'shard_id':sid,'path':p.name,'sha256':h,'payload_hash':e['payload_hash'],'sequence':i})
    (out/'transport_manifest.json').write_text(json.dumps({'schema':'OFG_EA_MRE2_TRANSPORT_MANIFEST_V2','thread':int(a.thread),'generation':a.generation,'master_epoch':2,'shards':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'PASS','outdir':str(out),'shards':len(manifest)},ensure_ascii=False))
if __name__=='__main__':main()
