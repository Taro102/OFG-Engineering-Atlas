#!/usr/bin/env python3
"""Generate bounded deterministic thread activation/rehydration capsules."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT_DEFAULT=Path(__file__).resolve().parents[1]
KEYWORDS={
 '1':[],
 '2':['RHR','CHW','CRY','CWS','TRITIUM','VAC','BHT401_FLOW','PROCUREMENT','VENDOR'],
 '4':['BHT401_SUPPORT','PENETRATION','UG01','SURV','RTE','E103','E104','E105','FOUNDATION','ASBUILT','CRS01'],
 '5':['M88217','CRS01','PMT','ASLEFT','CUSTODY','RTE003','RTE007','RTE008','EXECUTION','TURNOVER','COMMISSIONING']}

def load_json(p): return json.load(open(p,encoding='utf-8'))
def lines(p): return [json.loads(x) for x in open(p,encoding='utf-8') if x.strip()]
def relevant(text,keys): return not keys or any(k.lower() in text.lower() for k in keys)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',default=str(ROOT_DEFAULT)); ap.add_argument('--thread',required=True,choices=['1','2','4','5']); ap.add_argument('--generation',type=int,default=2); ap.add_argument('--output'); a=ap.parse_args(); root=Path(a.root)
 w=load_json(root/'state/current_working_state.json'); ref=load_json(root/'state/reference_state.json'); active=load_json(root/'state/active_cycle_c011.json'); roles=load_json(root/'state/thread_role_profiles.json'); keys=KEYWORDS[a.thread]
 conflicts=[x for x in lines(root/'state/conflicts.jsonl') if relevant(json.dumps(x),keys)]
 opens=[x for x in lines(root/'state/open_frontiers.jsonl') if relevant(json.dumps(x),keys)]
 ids=[x for x in lines(root/'state/identity_registry_seed.jsonl') if relevant(json.dumps(x),keys)]
 prov=[x for x in lines(root/'state/provenance_bindings.jsonl') if relevant(json.dumps(x),keys)]
 capsule={'schema':'OFG_EA_REHYDRATION_CAPSULE_V2','logical_thread':int(a.thread),'physical_instance':f'T{a.thread}-G{a.generation}','master_epoch':2,'baseline_id':w['baseline_id'],'staging':w['latest_integrated_staging'],'working_view':w['working_view'],'configuration_cut':w['configuration_cut'],'role':roles['T'+a.thread],'global_guards':ref['methodology']['semantic_guards'],'thread3_state':w['thread3_state'],'rev4_source_state':w['rev4_source_state'],'active_cycle':active,'relevant_conflicts':conflicts,'relevant_open_frontiers':opens,'relevant_identities':ids,'relevant_provenance':prov,'critical_state':w['critical_state'] if a.thread=='1' else {k:v for k,v in w['critical_state'].items() if relevant(k,keys) or relevant(json.dumps(v),keys)}}
 txt=json.dumps(capsule,ensure_ascii=False,indent=2)
 if a.output: Path(a.output).write_text(txt,encoding='utf-8')
 else: print(txt)
if __name__=='__main__':main()
