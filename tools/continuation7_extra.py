"""Adversarial exact-identity and parallel compact-construction regressions."""
import argparse
import json
from pathlib import Path
import random
import subprocess

import validate

ROOT = validate.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--prepare-only', action='store_true')
    args = ap.parse_args()
    validate.BINARY_DIR = ROOT / 'build' / args.name
    for n in [2, 65537]:
        data = ROOT / f'data/d/continuation7-parallel-wide-{n}'
        data.mkdir(parents=True, exist_ok=True)
        rng = random.Random(7281 + n)
        nodes = [0, 1] if n == 2 else [0, 1, 1023, 1024, 32767, 32768, 65535, 65536]
        weights = [0, 1, 2046, 2047, 2048, 2147483646, 2147483647, 2147483648, 4294967295]
        edges = [(rng.choice(nodes), rng.choice(nodes), rng.choice(weights)) for _ in range(200000)]
        with (data / 'graph.txt').open('w') as f:
            f.write(f'{n} {len(edges)}\n')
            for u, v, w in edges:
                f.write(f'{u} {v} {w}\n')
        assert (data / 'graph.txt').stat().st_size > 2 * 1024 * 1024
        (data / 'queries.txt').write_text(''.join(f'{u} {v}\n' for u in nodes for v in nodes)
                                         + (f'2 0\n0 2\n' if n > 2 else ''))
        if not args.prepare_only:
            validate.check('d', f'continuation7-parallel-wide-{n}', data)
    data = ROOT / 'data/a/continuation7-partial-hash-collision'
    data.mkdir(parents=True, exist_ok=True)
    paths = ['/prefix/AAA/endtail', '/prefix/BBB/endtail', '/prefix/CCC/endtail']
    assert len({(p[:8], p[-8:], len(p)) for p in paths}) == 1
    (data / 'requests.log').write_text(''.join(
        f'2026-10-30T18:00:00.000001Z GET {p} {500 if i % 2 else 200} {4294967295 - i}\n'
        for i in range(120) for p in paths))
    if not args.prepare_only:
        validate.check('a', 'continuation7-partial-hash-collision', data)
    data = ROOT / 'data/c/continuation7-partial-hash-collision'
    data.mkdir(parents=True, exist_ok=True)
    (data / 'regions.csv').write_text('region_id,country\n1,AAA\n2,BBB\n')
    names = ['abcdefgh X yzabcdef', 'abcdefgh Y yzabcdef', 'abcdefgh Z yzabcdef']
    assert len({(n[:8], n[-8:], len(n)) for n in names}) == 1
    (data / 'records.csv').write_text('id,name,note,region_id,amount\n' + ''.join(
        f'{i + 1},"{names[i % 3]}","note\nword",{i % 2 + 1},-0.01\n' for i in range(900)))
    if not args.prepare_only:
        validate.check('c', 'continuation7-partial-hash-collision', data)
        for n in [2, 65537]:
            subprocess.run([str(validate.BINARY_DIR / 'd-csr-contents7'),
                str(ROOT / f'data/d/continuation7-parallel-wide-{n}/graph.txt')], check=True)
        (ROOT / f'validation/{args.name}-new.json').write_text(json.dumps({
            'results': validate.REPORT, 'direct': ['d-csr-contents7: 200000 edges, n=2',
                                               'd-csr-contents7: 200000 edges, n=65537']}, indent=2) + '\n')
        print('PASS new exact partial-hash identities, wide temporary streams and every forward/reverse CSR edge.', flush=True)


if __name__ == '__main__':
    main()
