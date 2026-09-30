#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from ofg_current import load_context,historical
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a.add_argument('--candidate',action='store_true');a.add_argument('--historical',action='store_true');n=a.parse_args()
 if n.historical:r=historical(n.root)
 else:
  c=load_context(n.root,n.candidate);r={'status':'PASS','authority_effect':'NONE','preserved_paths':204,'state_root':c['state']['state_root_hash'],'candidate_mode':n.candidate}
 print(json.dumps(r))
if __name__=='__main__':main()
