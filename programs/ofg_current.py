#!/usr/bin/env python3
"""Verified configuration resolver. Candidate verification never activates authority."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,unicodedata
from pathlib import Path
BASE='879390336f430ab22f25d117de110614a278f466'
PARENT='031c48775775f331e40724bed0b49392d66b2442cf95abd3bad6fcf0469e66e6'
LEGACY='b8723daf6230116df28442e011342ded5de9480766b4ce40aed6a662853bf6bb'
MODIFIED=['PROGRAM_USAGE.json','README_MACHINE.json','START_HERE.json','README.md','programs/bootstrap.sh','programs/ofg_codec.py','programs/ofg_rehydrate.py','programs/ofg_transport.py','programs/ofg_retrieve.py','programs/ofg_index.py','programs/ofg_verify.py','programs/ofg_ingest.py']
ADDED=['control/master_recovery_cutover.json','state/current_root.json','state/master_recovery_root_e3_r1.json','schemas/master_recovery_cutover_v1.json','threads/T1-G3/state.json','threads/T2-G2/bindings/master_epoch_3.json','threads/T4-G2/bindings/master_epoch_3.json','threads/T5-G2/bindings/master_epoch_3.json','programs/ofg_current.py','manifests/t1_g3_master_recovery_cutover_manifest.json','control/master_context_policy.json','control/post_cutover_infrastructure_plan.json']
ROOT_PATH='state/master_recovery_root_e3_r1.json'
CONTROL_PATH='control/master_recovery_cutover.json'
SCHEMA_PATH='schemas/master_recovery_cutover_v1.json'
MANIFEST_PATH='manifests/t1_g3_master_recovery_cutover_manifest.json'
def require(ok,msg):
 if not ok: raise ValueError(msg)
def sha(b): return hashlib.sha256(b).hexdigest()
def blob_sha(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def pairs(items):
 d={}; seen=set()
 for k,v in items:
  n=unicodedata.normalize('NFC',k)
  require(n not in seen,'duplicate_or_NFC_colliding_key'); seen.add(n); d[k]=v
 return d
def loads(b):
 require(not b.startswith(b'\xef\xbb\xbf'),'BOM_prohibited')
 return json.loads(b.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite_number')))
def read(root,path): return loads((Path(root)/path).read_bytes())
def canonical(v):
 require(unicodedata.unidata_version=='15.0.0','Unicode_15_runtime_required')
 def norm(x):
  if isinstance(x,str):
   require(all(unicodedata.category(c)!='Cn' and not 0xD800<=ord(c)<=0xDFFF for c in x),'invalid_Unicode_scalar')
   return unicodedata.normalize('NFC',x)
  if x is None or isinstance(x,bool): return x
  if isinstance(x,int): require(abs(x)<=9007199254740991,'integer_range'); return x
  if isinstance(x,float): raise ValueError('noninteger_JSON_number')
  if isinstance(x,list): return [norm(y) for y in x]
  require(isinstance(x,dict),'invalid_JSON_type'); out={}
  for k,y in x.items():
   nk=norm(k); require(nk not in out,'NFC_key_collision'); out[nk]=norm(y)
  return dict(sorted(out.items(),key=lambda item:item[0].encode('utf-8')))
 return json.dumps(norm(v),ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
def semantic_hash(v,field): return sha(canonical({k:x for k,x in v.items() if k!=field}))
def checked_ref(root,r):
 p=Path(r['path']); require(not p.is_absolute() and '..' not in p.parts and '\\' not in r['path'],'unsafe_reference_path')
 b=(Path(root)/p).read_bytes(); require(len(b)==r['byte_count'] and sha(b)==r['sha256'],'object_hash_mismatch:'+str(p)); return b
def base_tree(root):
 raw=subprocess.check_output(['git','-C',str(root),'ls-tree','-rz',BASE])
 rows=[]
 for rec in raw.split(b'\0'):
  if not rec: continue
  meta,p=rec.split(b'\t',1); mode,typ,h=meta.decode().split(); require(typ=='blob','unexpected_tree_type'); rows.append({'path':p.decode('utf-8'),'git_blob_sha':h})
 return rows
def historical(root):
 root=Path(root); rows=base_tree(root); require(len(rows)==216,'parent_count')
 for r in rows:
  b=subprocess.check_output(['git','-C',str(root),'cat-file','blob',BASE+':'+r['path']]); require(blob_sha(b)==r['git_blob_sha'],'historical_blob_hash')
 old=loads(subprocess.check_output(['git','-C',str(root),'show',BASE+':state/root_manifest.json']))
 require(semantic_hash(old,'state_root_hash')==PARENT,'historical_root_hash')
 for r in old['legacy_inputs']:
  b=subprocess.check_output(['git','-C',str(root),'show',BASE+':'+r['repository_relative_path']]); require(sha(b)==r['sha256'] and len(b)==r['byte_count'],'historical_legacy_input')
 return {'status':'PASS','authority_class':'HISTORICAL_ONLY','master_instance':'T1-G2','master_epoch':2,'parent_blobs_verified':216,'compatibility_inputs_verified':30,'scope':'Published Phase8A Git compatibility bundle. Original pre-Git migration ZIP generated SQLite, pycache and LFS source materialization are outside this verification.'}
def load_context(root,allow_candidate=False):
 root=Path(root).resolve()
 if os.name=='nt' and not str(root).startswith('\\\\?\\'): root=Path('\\\\?\\'+str(root))
 selector=read(root,'state/current_root.json'); require(selector['schema']=='OFG-EA-CURRENT-ROOT-SELECTOR-V1','selector_schema')
 require(selector['root_ref']['path']==ROOT_PATH and selector['control_ref']['path']==CONTROL_PATH and selector['schema_ref']['path']==SCHEMA_PATH,'selector_targets')
 checked_ref(root,selector['root_ref']); checked_ref(root,selector['control_ref']); checked_ref(root,selector['schema_ref'])
 state=read(root,ROOT_PATH); require(state['schema']=='OFG-EA-MASTER-RECOVERY-ROOT-V1','root_schema')
 require(state['base_head']==BASE and state['parent_state_root']==PARENT and state['legacy_inputs_root_sha256']==LEGACY and state['legacy_input_count']==30,'parent_identity')
 require(state['master_instance']=='T1-G3' and state['master_epoch']==3,'root_master_binding')
 require(semantic_hash(state,'state_root_hash')==state['state_root_hash']==selector['expected_target_root_hash'],'successor_root_hash')
 for r in state['objects']: checked_ref(root,r)
 require(set(r['path'] for r in state['objects'])==set(MODIFIED+ADDED)-{'state/current_root.json',ROOT_PATH,MANIFEST_PATH},'root_object_closure')
 require(len(state['preserved_inputs'])==204 and len(set(r['path'] for r in state['preserved_inputs']))==204,'preserved_count')
 for r in state['preserved_inputs']:
  b=checked_ref(root,r); require(blob_sha(b)==r['parent_git_blob_sha'],'preserved_blob:'+r['path'])
 old=read(root,'state/root_manifest.json'); require(semantic_hash(old,'state_root_hash')==PARENT,'parent_root_changed')
 require(old['legacy_inputs_root_sha256']==LEGACY and old['legacy_input_file_count']==30,'legacy_root_changed')
 for r in old['legacy_inputs']:
  b=(root/r['repository_relative_path']).read_bytes(); require(sha(b)==r['sha256'] and len(b)==r['byte_count'],'legacy_input_changed')
 control=read(root,CONTROL_PATH); require(control['base_head']==BASE and control['parent_state_root']==PARENT,'control_parent')
 require(control['master_instance']=='T1-G3' and control['master_epoch']==3,'control_master')
 require(control['predecessor_state']=='PERMANENTLY_FENCED_RETIRED_FAILED_EXECUTION_CHANNEL','predecessor_fence')
 guards={'c011_integrated':False,'c012_created':False,'WF3_ACTIVE':False,'MRE3_ACTIVE':False,'accepted_C011_returns':0,'containerization_implemented':False}
 require(control['guards']==guards and state['guards']==guards,'forbidden_activation_or_return')
 require(control['C011_state']=='ACTIVE_UNINTEGRATED_IMPLEMENTATION_HOLD','C011_hold')
 require(control['T3_state']=='PERMANENTLY_RETIRED_READ_ONLY_NO_SUCCESSOR_NO_DEPENDENCY' and control['Rev4_state']=='QUARANTINED_OUT_OF_BASELINE','T3_Rev4')
 require(control['Phase8B_published'] is False,'Phase8B_publication')
 pin=control['engineering_pin']; require(pin==state['engineering_pin']==old['engineering_pin'],'engineering_pin_changed')
 bindings={}
 for name,path in control['bindings'].items():
  b=read(root,path); require(b['physical_instance']==name and b['master_instance']=='T1-G3' and b['master_epoch']==3,'thread_binding:'+name)
  require(b['accepted_c011_return_refs']==[] and b['WF3_ACTIVE'] is False and b['MRE3_ACTIVE'] is False,'binding_guard')
  require(b['engineering_pin']==pin,'binding_pin')
  if name!='T1-G3':
   original=read(root,'threads/'+name+'/state.json'); dispatch=read(root,b['dispatch_ref']); require(b['outstanding_assignments']==original['outstanding_assignments'],'task_changed')
   require(b['predecessor_instance']==original['predecessor_instance'] and b['predecessor_fence_state']==original['predecessor_fence_state'] and b['writer_authority']==original['writer_authority'] and b['global_write_authority']==original['global_write_authority'],'worker_scope_changed')
   require(dispatch['SOURCE_INSTANCE']=='T1-G2' and dispatch['MASTER_EPOCH']==2 and dispatch['TARGET_INSTANCE']==name,'issuer_provenance')
   a=b['outstanding_assignments'][0]; require(a['dispatch_id']==dispatch['PACKAGE_ID'] and a['task_id']==dispatch['TASK_ID'] and a['expected_return_packet_id']==dispatch['EXPECTED_RETURN_PACKET_ID'],'dispatch_assignment_changed')
  else: require(b['generation_state']=='SOLE_ACTIVE_MASTER_EPOCH_3' and b['role']=='THIN_MASTER_CONTROL_PLANE','master_role')
  bindings[name]=b
 require(set(bindings)=={'T1-G3','T2-G2','T4-G2','T5-G2'},'generation_set')
 policy=read(root,'control/master_context_policy.json'); require(policy['contract']=='OFG-EA-MASTER-MINIMAL-CONTEXT-V1' and policy['master_instance']=='T1-G3' and policy['role']=='THIN_MASTER_CONTROL_PLANE','thin_master_policy')
 require(policy['normal_packet_target_bytes']==20480 and policy['exceptional_packet_target_bytes']==102400 and policy['continuation_critical_conversation_only_state']=='PROHIBITED' and policy['AUX_rotation_changes_master_epoch'] is False and policy['MASTER_CONTEXT_POLICY_ACTIVE_AFTER_CUTOVER'] is True,'thin_master_limits')
 roadmap=read(root,'control/post_cutover_infrastructure_plan.json'); require(roadmap['phase_order'][0]=='8B.0_CONTAINER_FOUNDATION' and roadmap['containerization_implemented'] is False and roadmap['CONTAINERIZATION_CHANGES_CURRENT_CUTOVER_SCOPE'] is False and roadmap['ENGINEERING_STATE_EFFECT']=='NONE','roadmap_scope')
 manifest=read(root,MANIFEST_PATH); require(manifest['base_head']==BASE and manifest['candidate_state_root']==state['state_root_hash'],'manifest_identity')
 require(set(x['path'] for x in manifest['write_set'])==set(MODIFIED+ADDED) and len(manifest['write_set'])==24,'unexpected_25th_path')
 for r in manifest['files']: checked_ref(root,r)
 require(set(r['path'] for r in manifest['files'])==set(MODIFIED+ADDED)-{MANIFEST_PATH},'manifest_file_closure')
 if (root/'.git').exists():
  parent=base_tree(root); require({x['path']:x['git_blob_sha'] for x in parent if x['path'] not in MODIFIED}=={x['path']:x['parent_git_blob_sha'] for x in state['preserved_inputs']},'preservation_inventory_not_parent_tree')
  head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
  changed=set(subprocess.check_output(['git','-C',str(root),'diff','--name-only',BASE,'--'],text=True).splitlines())
  untracked=set(subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard'],text=True).splitlines())
  untracked={p for p in untracked if not p.startswith('generated/')}
  require(changed|untracked<=set(MODIFIED+ADDED),'unexpected_25th_path')
  if not allow_candidate:
   require(head!=BASE,'candidate_not_published')
   remote=subprocess.check_output(['git','-C',str(root),'ls-remote','origin','refs/heads/main'],text=True).split()[0]; require(remote==head,'remote_publication_not_observed')
   receipt_path=os.environ.get('OFG_INDEPENDENT_READBACK_RECEIPT'); require(bool(receipt_path),'independent_postpublication_receipt_required')
   receipt=loads(Path(receipt_path).read_bytes()); require(receipt.get('RESULT')=='PASS' and receipt.get('independent') is True and receipt.get('observed_head')==head and receipt.get('state_root')==state['state_root_hash'] and receipt.get('validator_instance') not in (None,'','AUX-XFER-CFG-01'),'invalid_independent_readback_receipt')
 else: require(allow_candidate,'candidate_mode_required_without_git_publication_context')
 return {'root':root,'state':state,'control':control,'bindings':bindings,'policy':policy,'manifest':manifest,'candidate_mode':allow_candidate}
def resolve_instance(ctx,name):
 require(name!='T1-G2','STALE_MASTER_GENERATION'); require(name in ctx['bindings'],'UNKNOWN_GENERATION_UNVERIFIED'); return ctx['bindings'][name]
def effective(ctx,section='working'):
 root=ctx['root']; c=ctx['control']
 if section=='working':
  w=read(root,'state/current_working_state.json'); w['current_master_instance']='T1-G3'; w['master_epoch_source']=3; w['successor_master_instance']=None; w['successor_master_epoch']=None
  w['thread_instances']['T1-G2']={'state':c['predecessor_state'],'writer':False}; w['thread_instances']['T1-G3']={'state':'SOLE_ACTIVE_MASTER_EPOCH_3','writer':True}; return w
 if section=='reference':
  w=read(root,'state/reference_state.json'); w['logical_threads']['1']['state']='SOLE_ACTIVE_MASTER_EPOCH_3'
  for t in ['2','4','5']:w['logical_threads'][t]['state']='SOLE_C011_EXECUTION_GENERATION'
  return w
 if section=='active':
  w=read(root,'state/active_cycle_c011.json'); w['current_master_binding']={'master_instance':'T1-G3','master_epoch':3}; return w
 if section=='roles':
  w=read(root,'state/thread_role_profiles.json'); w['T1']['generation_target']='T1-G3'; w['T1']['generation_state']='SOLE_ACTIVE_MASTER_EPOCH_3'; return w
 raise ValueError('unknown_section')
def output_path(ctx,target):
 p=Path(target).resolve()
 if os.name=='nt' and not str(p).startswith('\\\\?\\'):p=Path('\\\\?\\'+str(p))
 generated=(ctx['root']/'generated').resolve(); require(p.is_relative_to(generated) and p!=generated,'protected_compatibility_output'); return p
def classify_origin(name):
 if name=='T1-G2':return 'STALE_MASTER_GENERATION'
 if name in ('T1-G3','T2-G2','T4-G2','T5-G2'):return 'CURRENT_GENERATION_CANDIDATE_NOT_ACCEPTED'
 return 'UNKNOWN_GENERATION_UNVERIFIED'
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a.add_argument('--candidate',action='store_true');a.add_argument('--historical',action='store_true');a.add_argument('--instance',default='T1-G3');n=a.parse_args()
 if n.historical: result=historical(n.root)
 else:
  c=load_context(n.root,n.candidate);b=resolve_instance(c,n.instance);result={'status':'PASS','authority_effect':'NONE','candidate_mode':n.candidate,'instance':b['physical_instance'],'master_instance':b['master_instance'],'master_epoch':b['master_epoch'],'state_root':c['state']['state_root_hash']}
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
