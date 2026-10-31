"""Additional independent width and exact-overflow regressions for this batch."""
import argparse
import json
from pathlib import Path
import subprocess

import validate

ROOT=validate.ROOT
parser=argparse.ArgumentParser();parser.add_argument('--name',required=True);args=parser.parse_args()
validate.BINARY_DIR=ROOT/'build'/args.name
data=ROOT/'data/b/continuation5-wide-domain';data.mkdir(parents=True,exist_ok=True)
with (data/'docs.txt').open('w') as stream:
    for i in range(70000):stream.write(f'{i}\tcommon '+('boundary phrase' if i in [0,32767,32768,65535,65536,69999] else 'other')+'\n')
    stream.write('70000\t'+'-'*(24*1024*1024)+'\n')
(data/'queries.txt').write_text('BOOL common\nBOOL absent OR common NOT other\nPHRASE "boundary phrase"\nBOOL other AND common\nBOOL absent\n')
validate.check('b','continuation5-wide-domain',data)
# Disallow accidental narrowing of labels, including the narrow sentinel itself.
data=ROOT/'data/d/continuation5-wide-labels';data.mkdir(parents=True,exist_ok=True)
(data/'graph.txt').write_text('9 12\n0 1 4294967294\n1 2 1\n2 3 1\n3 4 4294967295\n4 5 0\n0 6 3\n6 7 0\n7 6 0\n0 1 4294967295\n5 5 0\n1 1 0\n6 2 4294967295\n')
(data/'queries.txt').write_text(''.join(f'{s} {t}\n' for s in range(9) for t in range(9)))
validate.check('d','continuation5-wide-labels',data)
# A prefetch ring must retire each escaped name before its scratch is reused.
data=ROOT/'data/c/continuation5-ring-reuse';data.mkdir(parents=True,exist_ok=True)
(data/'regions.csv').write_text('region_id,country\n1,AAA\n2,BBB\n')
with (data/'records.csv').open('w') as stream:
    stream.write('id,name,note,region_id,amount\n')
    for i in range(10000):
        name=['"A ""quote"""','"A ""quote"" "','""','', '"Long '+('x'*5000)+'"'][i%5]
        stream.write(f'{i+1},{name},"line\nword",{i%3+1},-0.01'+('' if i==9999 else '\n'))
validate.check('c','continuation5-ring-reuse',data)
data=ROOT/'data/a/continuation5-crc-collision'
validate.check('a','continuation5-crc-collision',data)
(ROOT/f'validation/{args.name}-additional.json').write_text(json.dumps({'results':validate.REPORT},indent=2)+'\n')
print('PASS additional real wide-document dispatch, uint32 label sentinel, escaped-name ring reuse, and exact CRC-collision endpoint identities',flush=True)
