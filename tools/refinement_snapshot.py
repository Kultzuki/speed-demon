"""Save current official results and a ranked best-three feed summary."""
import argparse
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
URL='https://s3.amazonaws.com/raptors.dev/speeddemon.dev/2026/board/board.json'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--name',required=True)
    args=parser.parse_args()
    request=urllib.request.Request(URL,headers={'User-Agent':'CodeScythe-refinement/1.0'})
    with urllib.request.urlopen(request,timeout=25) as response:board=json.load(response)
    teams=[]
    for team in board['teams']:
        best={k:(v.get('best') or {}) for k,v in team.get('tracks',{}).items()}
        points=sorted([float(v.get('points') or 0) for v in best.values()],reverse=True)
        aggregate=math.prod(points[:3])**(1/3) if len(points)>=3 else 0
        teams.append({'team':team.get('team'),'aggregate':aggregate,'best':best})
    teams.sort(key=lambda x:-x['aggregate'])
    for rank,team in enumerate(teams,1):team['rank']=rank
    own=next(t for t in board['teams'] if t.get('team','').lower()=='codescythe')
    summary={'fetched_at':datetime.now(timezone.utc).isoformat(),'rules':board.get('rules'),
             'ranking':teams,'codescythe':own}
    path=ROOT/'validation'/(args.name+'.json')
    path.write_text(json.dumps(summary,indent=2)+'\n')
    for item in [teams[0],next(t for t in teams if t['team'].lower()=='codescythe')]:
        print(json.dumps({k:v for k,v in item.items() if k!='best'}),flush=True)
        for track,run in item['best'].items():
            print(track,{k:run.get(k) for k in ['commit','run_id','points','K','T_s','M_bytes','S']},flush=True)
    print(path)

if __name__=='__main__':
    main()
