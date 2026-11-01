"""Track B-only differential, full-seed, sanitizer and width provenance gate."""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import tempfile

import validate

ROOT = validate.ROOT


def prepare():
    fixtures = ROOT / 'data/b'
    case = fixtures / 'trackb9-exhaustive-fold'
    case.mkdir(exist_ok=True)
    words = ['a', 'b', 'c', 'd', 'e', 'f']
    (case / 'docs.txt').write_text(''.join(f'{i}\t' + ' '.join(
        word for bit, word in enumerate(words) if i >> bit & 1) + '\n' for i in range(64)))
    queries = []
    for n in range(1, 7):
        for ops in itertools.product(['AND', 'OR', 'NOT'], repeat=n - 1):
            for variant in [words, list(reversed(words)), ['a'] * 6, ['a', 'absent', 'a', 'b', 'absent', 'c']]:
                q = 'BOOL ' + variant[0]
                for op, term in zip(ops, variant[1:n]):
                    q += ' ' + op + ' ' + term
                queries.append(q)
    (case / 'queries.txt').write_text('\n'.join(queries) + '\n')

    case = fixtures / 'trackb9-selective-folds'
    case.mkdir(exist_ok=True)
    with (case / 'docs.txt').open('w') as stream:
        for i in range(4096):
            words = ['hot']
            if 100 <= i < 164:
                mask = i - 100
                words += [chr(ord('a') + bit) for bit in range(6) if mask >> bit & 1]
                words += [f'needle{mask}', 'tail']
            stream.write(f'{i}\t' + ' '.join(words) + '\n')
    queries = []
    for ops in itertools.product(['AND', 'OR', 'NOT'], repeat=4):
        for mask in range(64):
            q = 'BOOL hot'
            for op, term in zip(ops, ['a', 'b', 'c', 'd']):
                q += ' ' + op + ' ' + term
            queries.append(q + f' AND needle{mask}')
    for mask in range(64):
        queries += [f'PHRASE "needle{mask} tail"', f'PHRASE "needle{mask} needle{mask}"',
                    f'PHRASE "a b needle{mask}"', f'BOOL needle{mask} NOT hot']
    (case / 'queries.txt').write_text('\n'.join(queries) + '\n')

    case = fixtures / 'trackb9-keys-windows'
    case.mkdir(exist_ok=True)
    tokens = ['a' * n for n in range(1, 33)] + [
        'abcdefghijklmnop' + 'qrstuvwx' + 'aaaaaaaz',
        'abcdefghijklmnop' + 'qrstuvwx' + 'aaaaaaay',
        'abcdefghijklmnop' + 'zzzzzzzz' + 'aaaaaaaz',
        '007', '7', 'z', 'rich', 'stanbul', '273', 'a0b1c2d3e4f5g6h7']
    texts = []
    for shift in range(64):
        for token in tokens:
            texts.append('.' * shift + token.upper() + ' / ' + token + ' -- tail')
    texts += ['a' * n + ' tail' for n in [33, 63, 64, 65, 127, 128, 129, 4097]]
    texts += ['Zürich İSTANBUL 273K', '', '---', 'a a a a a a a a', 'tail']
    (case / 'docs.txt').write_text(''.join(f'{i}\t{text}\n' for i, text in enumerate(texts)), encoding='utf-8')
    queries = ['BOOL ' + t for t in tokens]
    queries += ['PHRASE "' + t + ' ' + t + ' tail"' for t in tokens]
    queries += ['PHRASE "' + t + ' tail"' for t in tokens]
    queries += ['PHRASE "a a a a a a a a"', 'PHRASE "z rich"',
                'BOOL zurich OR rich NOT z', 'BOOL 7 NOT 007', 'BOOL absent']
    (case / 'queries.txt').write_text('\n'.join(queries) + '\n')

    for label, docs, queries in [
        ('empty', b'', b'BOOL absent\nPHRASE "a a"\n'),
        ('no-queries', b'0\ta\n', b''),
        ('mapped-page-end', b'0\t' + b'.' * 4085 + b'a a a a\n', b'BOOL a\nPHRASE "a a a a"\n'),
    ]:
        case = fixtures / ('trackb9-' + label)
        case.mkdir(exist_ok=True)
        (case / 'docs.txt').write_bytes(docs)
        (case / 'queries.txt').write_bytes(queries)

    # A long final document puts the entire id domain in the first worker's
    # byte range. Exercise exactly 65536 local ids and the next, wider domain.
    for n in [65536, 65537]:
        case = fixtures / f'trackb9-domain-{n}'
        case.mkdir(exist_ok=True)
        docs_path = case / 'docs.txt'
        if not docs_path.exists():
            with docs_path.open('w') as stream:
                for i in range(n):
                    text = 'common ' + ('boundary phrase' if i in [0, 32767, 32768, 65535, n - 1] else 'other')
                    stream.write(f'{i}\t{text}' + ('-' * (12 * 1024 * 1024) if i == n - 1 else '') + '\n')
        (case / 'queries.txt').write_text('BOOL boundary\nPHRASE "boundary phrase"\nBOOL common NOT other\nBOOL absent OR boundary\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--source', default='track-b/main.cpp')
    parser.add_argument('--sanitized', action='store_true')
    args = parser.parse_args()
    prepare()
    name = args.name + ('-sanitized' if args.sanitized else '-release')
    binary_dir = ROOT / 'build' / name
    binary_dir.mkdir(parents=True, exist_ok=True)
    validate.BINARY_DIR = binary_dir
    source = ROOT / args.source
    flags = ['-std=c++20', '-pthread', '-march=x86-64-v3']
    flags += ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if args.sanitized else ['-O3', '-DNDEBUG', '-static', '-s']
    command = ['g++', *flags, '-I', str(ROOT / 'track-b'), str(source), '-o', str(binary_dir / 'track-b')]
    subprocess.run(command, check=True)
    report = {'source': args.source, 'source_sha256': validate.digest(source),
              'common_sha256': validate.digest(ROOT / 'track-b/common.hpp'), 'flags': flags,
              'binary_sha256': validate.digest(binary_dir / 'track-b'), 'inputs': {}}
    for case in sorted((ROOT / 'data/b').iterdir()):
        if case.name == 'full-seed1' or not (case / 'docs.txt').is_file():
            continue
        report['inputs'][case.name] = {p.name: validate.digest(p) for p in case.iterdir() if p.is_file()}
        validate.check('b', case.name, case)

    public = json.loads((ROOT / '.competition/SHA256SUMS.json').read_text())['tracks']['b']
    fresh = json.loads((ROOT / 'validation/fresh-full-seed20261031.json').read_text())
    for label, data, inputs, expected in [
        ('public-full-seed1', Path('/benchdata/b'), public['inputs_sha256'], public['expected_output_sha256'][0]),
        ('fresh-full-seed20261031', Path('/benchfresh/seed20261031/b'), fresh['provenance']['b']['inputs_sha256'],
         next(r['sha256'] for r in fresh['results'] if r['track'] == 'b')),
    ]:
        actual_inputs = {f: validate.digest(data / f) for f in inputs}
        assert actual_inputs == inputs
        report['inputs'][label] = actual_inputs
        validate.check('b', label, data, expected)

    # Force the uint64 offset instantiation on the same complete public data.
    text = source.read_text()
    if 'solve<uint16_t,uint32_t>(paths)' in text:
        with tempfile.TemporaryDirectory() as temp:
            wide_source = Path(temp) / 'wide.cpp'
            wide_source.write_text(text.replace('solve<uint16_t,uint32_t>(paths)', 'solve<uint16_t,uint64_t>(paths)'))
            wide = binary_dir / 'track-b-wide'
            subprocess.run(['g++', *flags, '-I', str(ROOT / 'track-b'), str(wide_source), '-o', str(wide)], check=True)
            out = Path(temp) / 'out'
            out.mkdir()
            subprocess.run([str(wide), '--data', '/benchdata/b', '--out', str(out)], check=True)
            assert validate.digest(out / 'results.txt') == public['expected_output_sha256'][0]
            report['forced_uint64_offset'] = {'binary_sha256': validate.digest(wide), 'full_public_hash': public['expected_output_sha256'][0]}
    report['results'] = validate.REPORT
    (ROOT / f'validation/{name}.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS {name}: {len(validate.REPORT)} Track B comparisons, both full seeds and width provenance', flush=True)


if __name__ == '__main__':
    main()
