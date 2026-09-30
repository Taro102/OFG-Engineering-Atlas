#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from ofg_current import load_context,resolve_instance,effective,output_path,read
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a.add_argument('--thread',required=True,choices=['1','2','4','5']);a.add_argument('--generation',type=int);a.add_argument('--candidate',action='store_true');a.add_argument('--output');n=a.parse_args()
 c=load_context(n.root,n.candidate);expected='T1-G3' if n.thread=='1' else 'T'+n.thread+'-G2';name=expected if n.generation is None else 'T'+n.thread+'-G'+str(n.generation);b=resolve_instance(c,name)
 w=effective(c,'working');roles=effective(c,'roles');capsule={'schema':'OFG-EA-DERIVED-RECOVERY-CAPSULE-V1','authority_effect':'NONE','source_state_root':c['state']['state_root_hash'],'physical_instance':name,'master_instance':'T1-G3','master_epoch':3,'binding':b,'role':roles['T'+n.thread],'engineering_pin':b['engineering_pin'],'active_cycle':effective(c,'active'),'critical_state':w['critical_state'] if n.thread=='1' else {'status':'RETRIEVE_BY_ROLE_DEPENDENCY'},'compatibility_reference':'state/root_manifest.json','accepted_C011_returns':0}
 txt=json.dumps(capsule,ensure_ascii=False,indent=2)
 if n.output:
  p=output_path(c,n.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt,encoding='utf-8')
 else:print(txt)
if __name__=='__main__':main()
