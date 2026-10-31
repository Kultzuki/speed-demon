"""Update only documentation after the first official Rust result."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'HANDOVER_NEXT.md'
text = path.read_text()
text = text.replace('Last submitted/officially validated HEAD is\ne9deec07fa38f9abf0c167d6768c41c388e37ba5. The current working Rust A/D bundle is\nfully locally validated and ready for its first commit/push; it has not yet been\nofficially measured. Record the new exact commit and wait for all four tracks.',
'''The latest source-changing, pushed and officially scored checkpoint is
0ca1987477223527268d60911e073ff334feb8bd. All five gates passed on all four tracks.
The next commit records official evidence and fixes the local source-counter
bookkeeping only; submitted kernels are unchanged. Wait for its official rerun
before another kernel change, then record the exact final checkpoint.''')
text = text.replace('S=449', 'S=437').replace('S=485', 'S=473')
text = text.replace('validation/rust8-final-artifact-provenance.json,',
                    'validation/rust8-final-artifact-provenance-corrected.json,')
text = text.replace('Local complete K ratios against matched C++: A 1.0046 public / 1.0578 fresh;\nD 1.0373 / 1.0207.',
                    'Corrected local complete K ratios against matched C++: A 1.0087 public / 1.0621 fresh;\nD 1.0412 / 1.0246. The original counter included 12 TOML data lines per track;\nvalidation/rust8-canonical-source-correction.json preserves that correction.')
text = text.replace('First commit/push the frozen bundle, wait for every official gate and measurement,\nthen reject actual coefficient regressions.',
'''First official Rust: A K=30.827569, D K=14.542976. Both exceed the incoming
e9deec0 latest rerun (29.654383/14.469309) but do not beat historical bests
(33.234541/15.399979). validation/rust8-candidate-official-summary.json and
validation/leaderboard-rust8-candidate.json retain every gate and run ID.
One unchanged-source rerun accompanies the genuine source-counter correction
and official-evidence commit. Compare it before final retention; do not claim
a stable performance gain from these first measurements.''')
path.write_text(text)
(ROOT / 'NEXT_CHAT_PROMPT.md').write_text('''Read HANDOVER_NEXT.md completely and continue the existing private Speed Demon
entry in C:/Users/kultzuki/Coding/Speed-demon. Inspect git status first. Do not
restart, re-register, reset, force-push or spawn agents.

The last source-changing checkpoint is 0ca1987477223527268d60911e073ff334feb8bd
on the existing watched speed-demon branch. A/D are fully validated Rust; B/C
submitted sources are unchanged. A source-counter/evidence-only commit follows
with identical kernels. Read the latest handover for its exact final SHA/status.

Read research/CONTINUATION8_RUST.md, research/rust8-selection.json and the latest
official snapshots. Current Rust builds are build/rust8-final-{release,asan,checked}.
Each passes 97 comparisons, both full seeds and direct tests; all rebuilt image
executables match exactly, including Git-normalized LF sources. Actual canonical
S is A=437, D=473, with D=1. Initial raw local reports included TOML data; corrected
evidence is validation/rust8-canonical-source-correction.json and
validation/rust8-final-artifact-provenance-corrected.json.

The entire original user folder track-d-rust/track-d is unchanged and preserved.
Current Rust sources/configs are also in research/rust8-validated/, established
C++ sources in research/baseline8/. Preserve all logs, snapshots and dirty handover
updates. Do not blindly rerun one-shot rust8 scripts or earlier selectors.

All five official gates passed at 0ca1987: Rust A K=30.827569 and D K=14.542976.
These exceed the exact incoming HEAD's last rerun but not the historical peaks.
An unchanged-source rerun is being collected with the documentation correction;
wait for all tracks and compare complete coefficients before another kernel change.
B/C differences are unchanged-source variation. Refresh standings before quoting.
First place remains outstanding; retain exact equality and every width/epoch fallback.
''')
print('Updated handover and next-chat prompt; no submitted source changed.')
