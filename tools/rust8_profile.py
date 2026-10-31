"""Generate separate monotonic-clock sources; never submit instrumentation."""
from pathlib import Path
import argparse
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(); ap.add_argument('--name', default='rust8-profile'); args = ap.parse_args()
dest = ROOT / 'research/prototypes' / args.name
dest.mkdir(exist_ok=False)
for track in 'ad':
    folder = dest / track
    folder.mkdir()
    (folder / 'common.rs').write_bytes((ROOT / f'track-{track}/common.rs').read_bytes())
    text = (ROOT / f'track-{track}/main.rs').read_text()
    text = text.replace('let (data, out) = paths();', 'let profile_start = std::time::Instant::now();\n    let (data, out) = paths();')
    if track == 'a':
        text = text.replace('cache: [u16; 4096] }', 'cache: [u16; 4096], seen: u64, lookup_ns: u128, lookup_samples: u64 }')
        text = text.replace('cache: [0; 4096] } }', 'cache: [0; 4096], seen: 0, lookup_ns: 0, lookup_samples: 0 } }')
        text = text.replace('let hash = path_hash(name);',
            'let lookup_start = if self.seen & 1023 == 0 { Some(std::time::Instant::now()) } else { None };\n        let hash = path_hash(name);')
        text = text.replace('let error = u32::from(bytes[at + 1]',
            'self.seen += 1; if let Some(start) = lookup_start { self.lookup_ns += start.elapsed().as_nanos(); self.lookup_samples += 1; }\n        let error = u32::from(bytes[at + 1]')
        text = text.replace('let mut part = Partial::new();', 'let mut part = Partial::new(); let mut read_ns = 0;')
        text = text.replace('file.read_exact_at(&mut buffer[..n], offset)?;',
            'let pr = std::time::Instant::now(); file.read_exact_at(&mut buffer[..n], offset)?; read_ns += pr.elapsed().as_nanos();')
        text = text.replace('Ok(part.hours)',
            '{ eprintln!("A_INPUT_WORKER read_ns={} lookup_sample_ns={} samples={} records={}", read_ns, part.lookup_ns, part.lookup_samples, part.seen); Ok(part.hours) }')
        text = text.replace('let count = endpoints.count.load(Relaxed) as usize;',
            'eprintln!("A_PARSE_NS {}", profile_start.elapsed().as_nanos());\n    let count = endpoints.count.load(Relaxed) as usize;')
        text = text.replace('let mut values = Vec::new();',
            'let mut values = Vec::new(); let mut gather_ns = 0; let mut select_ns = 0; let mut format_ns = 0; let mut output_ns = 0;')
        text = text.replace('let buckets = hours[hour]', 'let pg = std::time::Instant::now();\n                let buckets = hours[hour]')
        text = text.replace('let mut output = Vec::with_capacity(160 * 1024);',
            'gather_ns += pg.elapsed().as_nanos(); let pf = std::time::Instant::now(); let mut this_select = 0;\n                let mut output = Vec::with_capacity(160 * 1024);')
        text = text.replace('let p = percentiles(', 'let ps = std::time::Instant::now(); let p = percentiles(')
        text = text.replace('output.extend_from_slice(stamp.as_bytes());',
            'this_select += ps.elapsed().as_nanos(); output.extend_from_slice(stamp.as_bytes());')
        text = text.replace('writer.lock().unwrap().complete(hour, output)?;',
            'let elapsed = pf.elapsed().as_nanos(); select_ns += this_select; format_ns += elapsed - this_select;\n'
            '                let po = std::time::Instant::now(); writer.lock().unwrap().complete(hour, output)?; output_ns += po.elapsed().as_nanos();')
        text = text.replace('            Ok(())\n        })).collect();',
            '            eprintln!("A_WORKER gather={} select={} format={} output={}", gather_ns, select_ns, format_ns, output_ns);\n            Ok(())\n        })).collect();')
        text = text.replace('checked_close(writer.into_inner().unwrap().file)',
            'eprintln!("A_BEFORE_CLOSE_NS {}", profile_start.elapsed().as_nanos());\n    checked_close(writer.into_inner().unwrap().file)')
    else:
        text = text.replace('let input = MappedFile::open(path)?;', 'let pg = std::time::Instant::now();\n        let input = MappedFile::open(path)?;')
        text = text.replace('let offset = std::array::from_fn(|d| {',
            'eprintln!("D_COUNT_NS {}", pg.elapsed().as_nanos()); let pp = std::time::Instant::now();\n        let offset = std::array::from_fn(|d| {')
        text = text.replace('        thread::scope(|scope| {\n            for cut in cuts.windows(2) {\n                let (degrees, edges)',
            '        eprintln!("D_PREFIX_NS {}", pp.elapsed().as_nanos()); let ps = std::time::Instant::now();\n        thread::scope(|scope| {\n            for cut in cuts.windows(2) {\n                let (degrees, edges)')
        text = text.replace('        Ok(Self { offset, edges, n })',
            '        eprintln!("D_SCATTER_NS {}", ps.elapsed().as_nanos());\n        Ok(Self { offset, edges, n })')
        text = text.replace('    let answers: Vec<_>',
            '    eprintln!("D_BEFORE_QUERY_NS {}", profile_start.elapsed().as_nanos()); let pq = std::time::Instant::now();\n    let answers: Vec<_>')
        text = text.replace('    let mut output = Vec::with_capacity(answers.len() * 12);',
            '    eprintln!("D_QUERY_NS {}", pq.elapsed().as_nanos());\n    let mut output = Vec::with_capacity(answers.len() * 12);')
    source = folder / 'main.rs'
    source.write_text(text)
    subprocess.run(['docker', 'exec', 'codescythe-rust8', 'rustc', '--edition=2021', '-O', '-C', 'lto=fat',
        '-C', 'panic=abort', '-C', 'target-feature=+crt-static', '-C', 'target-cpu=x86-64-v3',
        '/work/' + source.relative_to(ROOT).as_posix(), '-o', f'/work/build/rust8-bench/{track}-{args.name}'], check=True)
print('Built isolated profile sources')
