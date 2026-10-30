"""Append exact official b30392c results and the A rejection decision."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
snapshot=json.loads((ROOT/'validation/leaderboard-refinement-b30392c.json').read_text())
team=snapshot['codescythe']
assert all(v['latest']['commit'].startswith('b30392c') and v['latest']['ok'] for v in team['tracks'].values())
for track,item in team['tracks'].items():
    run=item['latest'];path=ROOT/f'track-{track}/PERF.md'
    text=path.read_text();marker='## Official b30392c measurement and promotion decision'
    assert marker not in text
    text+='\n\n'+marker+'\n\n'
    text+=f"Commit `{run['commit']}`, run `{run['run_id']}`: T={run['T_s']:.6f}s, M={run['M_bytes']} bytes, S={run['S']}, D={run['D']}, K={run['K']:.6f}, points={run['points']:.6f}. All official gates passed.\n\n"
    if track=='a':
        text+='The candidate is rejected: faster runtime did not offset higher official memory and source cost. Its K=18.583948 is below the prior 19.851814. Production is restored byte-for-byte to the stronger `0c89c6e` A source; the packed-record and allocator/parser experiments remain in research.\n'
    else:
        text+='This improves the previous best coefficient and is retained. Exact board/team data is in `validation/leaderboard-refinement-b30392c.json`.\n'
        if track=='c':text+='A further isolated record-boundary shortcut from the second supplied set is being validated separately; it is not included in this score.\n'
    path.write_text(text)
path=ROOT/'research/REFINEMENT_2026-10-31.md'
text=path.read_text()+'''

## Official b30392c outcome

All gates passed. A: 63.456899 points, K=18.583948, T=0.085539s,
M=75,784,192, S=319; B: 55.158259, K=12.681341, T=0.734635s,
M=87,310,336, S=570; C: 62.012380, K=17.387919, T=0.117573s,
M=15,142,912, S=377; D: 56.356919, K=13.401036, T=0.513979s,
M=95,133,696, S=384. Run IDs are in each track's PERF log.

B/C/D improve and are retained. A's memory/source cost loses coefficient despite
being faster; its runtime source is restored to the stronger measured 0c89c6e
version. The board retains that older A best. Aggregate becomes 60.981929 from
58.007574, using A/C/D. The captured rank remains 22 as other teams improved too;
ALL STAR is 73.212358 in that snapshot. These are public best-three machine points,
not final hidden-seed/judging results.

The second supplied set and its reproduced faults are recorded separately in
`SUPPLIED_SECOND_REVIEW.md`. Its contract-backed C boundary shortcut is faster in
an alternating local trial and is going through the final gate. A's additional
parser and allocator controls do not establish enough gain to override its
official rejection and remain unpromoted.
'''
path.write_text(text)
print('Recorded all official run IDs, coefficients, A rejection and aggregate')
