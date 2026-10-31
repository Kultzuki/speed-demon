include!(concat!(env!("SPEED_DEMON_ROOT"), "/track-a/main.rs"));

#[test]
fn exact_publication() {
    let names: Vec<_> = (0..1842).map(|i| format!("/publication/endpoint_{i}").into_bytes()).collect();
    let table = EndpointTable::new();
    let elected: Vec<_> = (0..names.len()).map(|_| AtomicU32::new(u32::MAX)).collect();
    thread::scope(|scope| {
        for t in 0..12 {
            let (table, elected, names) = (&table, &elected, &names);
            scope.spawn(move || {
                for _ in 0..8 {
                    for j in 0..names.len() {
                        let i = (j + t * 131) % names.len();
                        let id = u32::from(table.find(&names[i], path_hash(&names[i])));
                        if let Err(old) = elected[i].compare_exchange(u32::MAX, id, Relaxed, Relaxed) { assert_eq!(old, id); }
                        assert_eq!(table.name(id as usize), &names[i]);
                    }
                }
            });
        }
    });
    assert_eq!(table.count.load(Relaxed), 1842);
    let mut ids: Vec<_> = elected.iter().map(|id| id.load(Relaxed)).collect();
    ids.sort_unstable(); ids.dedup(); assert_eq!(ids.len(), names.len());
}

#[test]
fn bounded_simd_and_exact_overflow() {
    unsafe extern "C" {
        #[link_name = "mmap"] fn guard_map(p: *mut u8, n: usize, prot: i32, flags: i32, fd: i32, offset: i64) -> *mut u8;
        fn mprotect(p: *mut u8, n: usize, prot: i32) -> i32;
        #[link_name = "munmap"] fn guard_unmap(p: *mut u8, n: usize) -> i32;
    }
    unsafe {
        let page = guard_map(std::ptr::null_mut(), 8192, 3, 0x22, -1, 0);
        assert_ne!(page as isize, -1); assert_eq!(mprotect(page.add(4096), 4096, 0), 0);
        for n in 1..=125 {
            for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"] {
                for value in [0, WIDE - 1, WIDE, WIDE + 1, u32::MAX] {
                    let endpoint = format!("/{}", "x".repeat(n - 1));
                    let line = format!("2026-11-02T17:59:59.999999Z {method} {endpoint} 599 {value}\n");
                    let p = page.add(4096 - line.len());
                    std::ptr::copy_nonoverlapping(line.as_ptr(), p, line.len());
                    let table = EndpointTable::new();
                    let mut part = Partial::new();
                    part.parse(std::slice::from_raw_parts(p, line.len()), &table);
                    let b = &part.hours[71]; assert_eq!(b.records.len(), 1);
                    let word = b.records[0];
                    let latency = if word >> 12 == WIDE { b.wide[0] } else { word >> 12 };
                    assert_eq!(latency, value); assert_eq!(word & 1, 1);
                    assert_eq!(table.name(((word >> 1) & 2047) as usize), endpoint.as_bytes());
                }
            }
        }
        assert_eq!(guard_unmap(page, 8192), 0);
    }
}

#[test]
fn percentile_duplicate_ranks() {
    for n in 1..=1100 {
        let mut values: Vec<_> = (0..n).map(|i| ((i * 701 + n) % 193) as u32).collect();
        let mut sorted = values.clone(); sorted.sort_unstable();
        assert_eq!(percentiles(&mut values), [50, 95, 99].map(|p| sorted[(p * n + 99) / 100 - 1]));
    }
}

#[test]
fn exact_decimal_lengths_and_terminated_tails() {
    let mut state = 4135u32;
    let mut values = vec![0, 1, u32::MAX];
    for digits in 1..=9 {
        let power = 10u32.pow(digits);
        values.extend([power - 1, power, power + 1]);
    }
    for _ in 0..100000 {
        state = state.wrapping_mul(1664525).wrapping_add(1013904223);
        values.push(state);
    }
    for value in values {
        for tail in ["", "2026-11-02T17:59:59.999999Z GET / 200 0\n"] {
            let text = format!("{value}\n{tail}");
            let mut at = 0;
            assert_eq!(integer(text.as_bytes(), &mut at), value);
            assert_eq!(text.as_bytes()[at], b'\n');
        }
    }
}

#[test]
fn buffered_range_alignment_owns_each_line_once() {
    let path = std::env::temp_dir().join(format!("rust8-a-range-{}", std::process::id()));
    let mut text = Vec::new();
    for n in 1..=125 {
        writeln!(text, "2026-11-02T17:59:59.999999Z OPTIONS /{} 599 4294967295", "x".repeat(n - 1)).unwrap();
    }
    let mut file = File::create(&path).unwrap(); file.write_all(&text).unwrap(); drop(file);
    let file = File::open(&path).unwrap();
    let size = text.len() as u64;
    for offset in 0..=size {
        let expected = if offset == 0 || offset == size { offset }
            else { offset + text[offset as usize - 1..].iter().position(|&b| b == b'\n').unwrap() as u64 };
        assert_eq!(align_line(&file, offset, size).unwrap(), expected);
    }
    for workers in 1..=19 {
        let table = EndpointTable::new();
        let mut seen = 0;
        for i in 0..workers {
            let hours = read_part(&file, size * i / workers, size * (i + 1) / workers, size, &table).unwrap();
            for bucket in hours {
                seen += bucket.records.len();
                assert_eq!(bucket.records.len(), bucket.wide.len());
                assert!(bucket.wide.iter().all(|&x| x == u32::MAX));
            }
        }
        assert_eq!(seen, 125);
    }
    std::fs::remove_file(path).unwrap();
}
