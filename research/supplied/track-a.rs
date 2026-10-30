use std::fs::File;
use std::io::{BufWriter, Read, Seek, SeekFrom, Write};
use std::path::Path;
use std::sync::Mutex;

#[derive(Default)]
struct ThreadGroup {
    count: u32,
    errors: u32,
    latencies: Vec<u32>,
}

#[inline(always)]
fn parse_hour_idx(ts: &[u8]) -> usize {
    let month = (ts[5] - b'0') * 10 + (ts[6] - b'0');
    let day = (ts[8] - b'0') * 10 + (ts[9] - b'0');
    let hour = (ts[11] - b'0') * 10 + (ts[12] - b'0');
    if month == 10 {
        if day == 30 { (hour - 18) as usize } else { (6 + hour) as usize }
    } else if day == 1 {
        (30 + hour) as usize
    } else {
        (54 + hour) as usize
    }
}

fn get_hour_string(h: usize) -> String {
    let (m, d, hr) = if h < 6 { (10, 30, 18 + h) }
    else if h < 30 { (10, 31, h - 6) }
    else if h < 54 { (11, 1, h - 30) }
    else { (11, 2, h - 54) };
    format!("2026-{m:02}-{d:02}T{hr:02}:00:00Z")
}

#[inline(always)]
fn fxhash(bytes: &[u8]) -> usize {
    let mut h: u64 = 0x517cc1b727220a95;
    for &b in bytes {
        h = (h.rotate_left(5) ^ (b as u64)).wrapping_mul(0x517cc1b727220a95);
    }
    h as usize
}

struct GlobalRegistry {
    slots: Vec<u16>,
    endpoints: Vec<Vec<u8>>,
}

impl GlobalRegistry {
    fn new() -> Self {
        Self { slots: vec![0; 8192], endpoints: Vec::with_capacity(2048) }
    }
    fn get_or_insert(&mut self, ep: &[u8]) -> u16 {
        let mut idx = fxhash(ep) & 8191;
        loop {
            let slot = self.slots[idx];
            if slot == 0 {
                let id = self.endpoints.len() as u16;
                self.slots[idx] = id + 1;
                self.endpoints.push(ep.to_vec());
                return id;
            } else if self.endpoints[(slot - 1) as usize] == ep {
                return slot - 1;
            }
            idx = (idx + 1) & 8191;
        }
    }
}

struct LocalCache<'a> {
    slots: Vec<u16>,
    registry: &'a Mutex<GlobalRegistry>,
}

impl<'a> LocalCache<'a> {
    fn new(registry: &'a Mutex<GlobalRegistry>) -> Self {
        Self { slots: vec![0; 8192], registry }
    }
    #[inline(always)]
    fn get_or_insert(&mut self, ep: &[u8], store: &[Vec<u8>]) -> u16 {
        let mut idx = fxhash(ep) & 8191;
        loop {
            let slot = self.slots[idx];
            if slot == 0 {
                let id = self.registry.lock().unwrap().get_or_insert(ep);
                self.slots[idx] = id + 1;
                return id;
            } else {
                let id = (slot - 1) as usize;
                if id < store.len() && store[id] == ep {
                    return id as u16;
                }
            }
            idx = (idx + 1) & 8191;
        }
    }
}

#[inline(always)]
fn append_num(buf: &mut [u8], mut val: u64, mut pos: usize) -> usize {
    if val == 0 { buf[pos] = b'0'; return pos + 1; }
    let mut temp = [0u8; 20];
    let mut len = 0;
    while val > 0 { temp[len] = b'0' + (val % 10) as u8; val /= 10; len += 1; }
    while len > 0 { len -= 1; buf[pos] = temp[len]; pos += 1; }
    pos
}

#[inline(always)]
fn calc_percentiles(lats: &mut [u32], n: usize) -> (u32, u32, u32) {
    if n == 1 { (lats[0], lats[0], lats[0]) }
    else if n == 2 {
        let (v0, v1) = (lats[0], lats[1]);
        if v0 <= v1 { (v0, v1, v1) } else { (v1, v0, v0) }
    } else {
        let r50 = (50 * n + 99) / 100 - 1;
        let r95 = (95 * n + 99) / 100 - 1;
        let r99 = (99 * n + 99) / 100 - 1;
        if n <= 32 {
            lats.sort_unstable();
            (lats[r50], lats[r95], lats[r99])
        } else {
            lats.select_nth_unstable(r99);
            let p99 = lats[r99];
            let p95 = if r95 == r99 { p99 } else {
                lats[..r99].select_nth_unstable(r95);
                lats[r95]
            };
            let p50 = if r50 == r95 { p95 } else {
                lats[..r95].select_nth_unstable(r50);
                lats[r50]
            };
            (p50, p95, p99)
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let data_dir = std::env::var("DATA_DIR").unwrap_or_else(|_| "/data".into());
    let out_dir = std::env::var("OUT_DIR").unwrap_or_else(|_| "/out".into());
    let in_path = Path::new(&data_dir).join("requests.log");
    let out_path = Path::new(&out_dir).join("summary.txt");

    if !in_path.exists() { File::create(&out_path)?; return Ok(()); }
    let mut file = File::open(&in_path)?;
    let file_len = file.metadata()?.len() as usize;
    if file_len == 0 { File::create(&out_path)?; return Ok(()); }

    const NUM_THREADS: usize = 6;
    let mut thread_starts = vec![file_len; NUM_THREADS];
    let mut thread_ends = vec![file_len; NUM_THREADS];
    thread_starts[0] = 0; thread_ends[0] = file_len;

    if NUM_THREADS > 1 && file_len > 1024 * 1024 {
        let chunk_size = file_len / NUM_THREADS;
        let mut probe = [0u8; 4096];
        for i in 1..NUM_THREADS {
            let target = i * chunk_size;
            file.seek(SeekFrom::Start(target as u64))?;
            let n = file.read(&mut probe)?;
            if let Some(pos) = probe[..n].iter().position(|&b| b == b'\n') {
                let split = target + pos + 1;
                thread_starts[i] = split;
                thread_ends[i - 1] = split;
            }
        }
    }

    let global_reg = Mutex::new(GlobalRegistry::new());
    let mut thread_results: Vec<Vec<ThreadGroup>> = Vec::with_capacity(NUM_THREADS);

    std::thread::scope(|s| {
        let mut handles = Vec::with_capacity(NUM_THREADS);
        for t in 0..NUM_THREADS {
            let (start, end) = (thread_starts[t], thread_ends[t]);
            let (in_p, reg_ref) = (&in_path, &global_reg);
            handles.push(s.spawn(move || -> Vec<ThreadGroup> {
                let mut groups: Vec<ThreadGroup> = (0..72 * 2048).map(|_| ThreadGroup::default()).collect();
                if start >= end { return groups; }
                let mut f = match File::open(in_p) { Ok(f) => f, Err(_) => return groups };
                if f.seek(SeekFrom::Start(start as u64)).is_err() { return groups; }

                let mut cache = LocalCache::new(reg_ref);
                let mut ep_store: Vec<Vec<u8>> = Vec::with_capacity(2048);
                const BUF_CAP: usize = 1024 * 1024;
                let mut buf = vec![0u8; BUF_CAP];
                let mut tail = 0;
                let mut offset = start;

                while offset < end {
                    let to_read = (end - offset).min(BUF_CAP - tail);
                    if to_read == 0 { break; }
                    let nread = match f.read(&mut buf[tail..tail + to_read]) { Ok(n) if n > 0 => n, _ => break };
                    offset += nread;
                    let total = tail + nread;

                    let last_nl = match buf[..total].iter().rposition(|&b| b == b'\n') {
                        Some(p) => p,
                        None => if offset >= end { total } else { tail = total; continue; }
                    };

                    let mut cur = 0;
                    while cur <= last_nl {
                        let (l_start, mut l_end) = (cur, cur);
                        while l_end <= last_nl && buf[l_end] != b'\n' { l_end += 1; }
                        cur = l_end + 1;
                        if l_end <= l_start + 28 { continue; }

                        let h_idx = parse_hour_idx(&buf[l_start..l_end]);
                        let mut p = l_start + 28;
                        while p < l_end && buf[p] != b' ' { p += 1; }
                        p += 1;

                        let ep_start = p;
                        while p < l_end && buf[p] != b' ' { p += 1; }
                        let ep = &buf[ep_start..p];
                        p += 1;

                        let is_err = p < l_end && buf[p] == b'5';
                        p += 4;

                        let mut lat: u32 = 0;
                        while p < l_end && buf[p].is_ascii_digit() {
                            lat = lat * 10 + (buf[p] - b'0') as u32;
                            p += 1;
                        }

                        let ep_id = cache.get_or_insert(ep, &ep_store);
                        if (ep_id as usize) >= ep_store.len() {
                            ep_store = reg_ref.lock().unwrap().endpoints.clone();
                        }

                        let g = &mut groups[(h_idx << 11) | (ep_id as usize)];
                        g.count += 1;
                        if is_err { g.errors += 1; }
                        g.latencies.push(lat);
                    }
                    let rem = total - cur;
                    if rem > 0 { buf.copy_within(cur..total, 0); }
                    tail = rem;
                }
                groups
            }));
        }
        for h in handles { thread_results.push(h.join().unwrap()); }
    });

    let reg = global_reg.into_inner().unwrap();
    let num_ep = reg.endpoints.len();
    let mut sorted_ep: Vec<u16> = (0..num_ep as u16).collect();
    sorted_ep.sort_unstable_by(|&a, &b| reg.endpoints[a as usize].cmp(&reg.endpoints[b as usize]));

    let hour_strings: Vec<String> = (0..72).map(get_hour_string).collect();
    let mut writer = BufWriter::with_capacity(1024 * 1024, File::create(&out_path)?);
    let mut line_buf = [0u8; 512];
    let mut lats: Vec<u32> = Vec::with_capacity(4096);

    for h_idx in 0..72 {
        let hr_b = hour_strings[h_idx].as_bytes();
        for &ep_id in &sorted_ep {
            let slot = (h_idx << 11) | (ep_id as usize);
            let mut count = 0u32;
            let mut errors = 0u32;
            lats.clear();

            for t in 0..NUM_THREADS {
                let g = &mut thread_results[t][slot];
                count += g.count;
                errors += g.errors;
                if g.count > 0 { lats.append(&mut g.latencies); }
            }
            if count == 0 { continue; }

            let n = count as usize;
            let (p50, p95, p99) = calc_percentiles(&mut lats, n);
            let ppm = (errors as u64 * 1_000_000) / (n as u64);
            let ep_b = &reg.endpoints[ep_id as usize];

            let mut pos = 0;
            line_buf[pos..pos + 20].copy_from_slice(hr_b); pos += 20;
            line_buf[pos] = b' '; pos += 1;
            line_buf[pos..pos + ep_b.len()].copy_from_slice(ep_b); pos += ep_b.len();
            line_buf[pos] = b' '; pos += 1;
            pos = append_num(&mut line_buf, n as u64, pos); line_buf[pos] = b' '; pos += 1;
            pos = append_num(&mut line_buf, p50 as u64, pos); line_buf[pos] = b' '; pos += 1;
            pos = append_num(&mut line_buf, p95 as u64, pos); line_buf[pos] = b' '; pos += 1;
            pos = append_num(&mut line_buf, p99 as u64, pos); line_buf[pos] = b' '; pos += 1;
            pos = append_num(&mut line_buf, errors as u64, pos); line_buf[pos] = b' '; pos += 1;
            pos = append_num(&mut line_buf, ppm, pos); line_buf[pos] = b'\n'; pos += 1;

            writer.write_all(&line_buf[..pos])?;
        }
    }
    writer.flush()?;
    Ok(())
}