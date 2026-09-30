#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from ofg_current import load_context,resolve_instance,output_path,read,sha,require
from ofg_codec import envelope,canonical_bytes
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a.add_argument('--thread',required=True,choices=['1','2','4','5']);a.add_argument('--generation',type=int);a.add_argument('--candidate',action='store_true');a.add_argument('--capsule',required=True);a.add_argument('--outdir',required=True);n=a.parse_args()
 c=load_context(n.root,n.candidate);name=('T1-G3' if n.thread=='1' else 'T'+n.thread+'-G2') if n.generation is None else 'T'+n.thread+'-G'+str(n.generation);b=resolve_instance(c,name);out=output_path(c,n.outdir)
 capsule=json.loads(Path(n.capsule).read_text(encoding='utf-8'));require(capsule['source_state_root']==c['state']['state_root_hash'] and capsule['physical_instance']==name,'stale_capsule');out.mkdir(parents=True,exist_ok=True)
 pieces=[('CONTROL',c['control']),('BINDING',b),('CAPSULE',capsule)];prev=None;entries=[]
 for i,(kind,payload) in enumerate(pieces,1):
  sid=name+'-'+kind+'-'+str(i).zfill(2);e=envelope(payload,sid,kind,master_epoch=3,generation_scope=name,sequence=i,sequence_total=len(pieces),previous_hash=prev);raw=canonical_bytes(e);p=out/(sid+'.json');p.write_bytes(raw);prev=sha(raw);entries.append({'path':p.name,'sha256':prev})
 (out/'transport_manifest.json').write_text(json.dumps({'schema':'OFG-EA-DERIVED-MRE2-TRANSPORT-V1','authority_effect':'NONE','master_epoch':3,'source_state_root':c['state']['state_root_hash'],'physical_instance':name,'shards':entries},indent=2),encoding='utf-8');print(json.dumps({'status':'PASS','authority_effect':'NONE','shards':len(entries)}))
if __name__=='__main__':main()
