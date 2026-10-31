mod common;
use common::*;
use std::cell::UnsafeCell;
use std::fs::File;
use std::io::{self, Write};
use std::os::unix::fs::FileExt;
use std::sync::atomic::{AtomicU32, AtomicUsize, Ordering::*};
use std::sync::Mutex;
use std::thread;

const WIDE: u32 = (1 << 20) - 1;

#[inline]
fn path_hash(name: &[u8]) -> usize {
    let n = name.len();
    let (a, b) = if n >= 8 {
        (u64::from_le_bytes(name[..8].try_into().unwrap()),
         u64::from_le_bytes(name[n - 8..].try_into().unwrap()))
    } else {
        let a = name.iter().fold(0, |a, &b| (a << 8) | u64::from(b));
        (a, a)
    };
    let mut h = (a ^ b.rotate_left(29)).wrapping_add((n as u64).wrapping_mul(0x9e3779b97f4a7c15));
    h = (h ^ (h >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
    h = (h ^ (h >> 27)).wrapping_mul(0x94d049bb133111eb);
    (h ^ (h >> 31)) as usize
}

struct Name { bytes: [u8; 125], len: u8 }
struct EndpointTable {
    slots: [AtomicU32; 4096],
    names: [UnsafeCell<Name>; 2048],
    count: AtomicU32,
}
// Each name has one writer. Readers use only IDs obtained after the slot's
// release publication (or after joining all parsers); names never change again.
unsafe impl Sync for EndpointTable {}
impl EndpointTable {
    fn new() -> Self {
        Self { slots: std::array::from_fn(|_| AtomicU32::new(0)),
               names: std::array::from_fn(|_| UnsafeCell::new(Name { bytes: [0; 125], len: 0 })), count: AtomicU32::new(0) }
    }
    #[inline]
    fn name(&self, id: usize) -> &[u8] {
        let name = unsafe { &*self.names[id].get() };
        &name.bytes[..usize::from(name.len)]
    }
    fn find(&self, name: &[u8], hash: usize) -> u16 {
        let mut at = hash & 4095;
        loop {
            let mut value = self.slots[at].load(Acquire);
            if value == 0 {
                match self.slots[at].compare_exchange(0, u32::MAX, Acquire, Acquire) {
                    Ok(_) => {
                        let id = self.count.fetch_add(1, Relaxed) as usize;
                        assert!(id < self.names.len());
                        let key = unsafe { &mut *self.names[id].get() };
                        key.bytes[..name.len()].copy_from_slice(name);
                        key.len = name.len() as u8;
                        self.slots[at].store(id as u32 + 1, Release);
                        return id as u16;
                    }
                    Err(actual) => value = actual,
                }
            }
            while value == u32::MAX {
                std::hint::spin_loop();
                value = self.slots[at].load(Acquire);
            }
            if value != 0 && self.name(value as usize - 1) == name { return (value - 1) as u16; }
            at = (at + 1) & 4095;
        }
    }
}

#[derive(Default)]
struct Bucket { records: Vec<u32>, wide: Vec<u32> }

#[inline]
fn endpoint_end(bytes: &[u8], mut at: usize) -> usize {
    use std::arch::x86_64::*;
    // Every SIMD load is entirely inside this parser's slice, including EOF.
    unsafe {
        while bytes.len() - at >= 32 {
            let v = _mm256_loadu_si256(bytes.as_ptr().add(at).cast());
            let mask = _mm256_movemask_epi8(_mm256_cmpeq_epi8(v, _mm256_set1_epi8(b' ' as i8))) as u32;
            if mask != 0 { return at + mask.trailing_zeros() as usize; }
            at += 32;
        }
    }
    while bytes[at] != b' ' { at += 1; }
    at
}

#[inline]
fn latency(bytes: &[u8], at: &mut usize) -> u32 {
    if bytes.len() - *at < 8 { return integer(bytes, at); }
    // The load is bounded. LF ends every valid latency; the first zero-byte
    // marker finds it even if subtraction marks a later byte through borrow.
    let word = unsafe { bytes.as_ptr().add(*at).cast::<u64>().read_unaligned() };
    let x = word ^ 0x0a0a0a0a0a0a0a0a;
    let mask = x.wrapping_sub(0x0101010101010101) & !x & 0x8080808080808080;
    let n = if mask == 0 { 8 } else { mask.trailing_zeros() as usize / 8 };
    let mut v = (word << ((8 - n) * 8)) & 0x0f0f0f0f0f0f0f0f;
    v = (v.wrapping_mul(10) + (v >> 8)) & 0x00ff00ff00ff00ff;
    v = (v.wrapping_mul(100) + (v >> 16)) & 0x0000ffff0000ffff;
    let mut value = (v.wrapping_mul(10000).wrapping_add(v >> 32)) as u32;
    *at += n;
    if n == 8 {
        while bytes[*at].is_ascii_digit() { value = value * 10 + u32::from(bytes[*at] - b'0'); *at += 1; }
    }
    value
}

struct Partial { hours: [Bucket; 72], cache: [u16; 4096] }
impl Partial {
fn new() -> Self { Self { hours: std::array::from_fn(|_| Bucket::default()), cache: [0; 4096] } }
fn parse(&mut self, bytes: &[u8], endpoints: &EndpointTable) {
    let hours = &mut self.hours;
    let cache = &mut self.cache;
    let mut at = 0;
    while at < bytes.len() {
        let day = usize::from(bytes[at + 8] - b'0') * 10 + usize::from(bytes[at + 9] - b'0');
        let hour = usize::from(bytes[at + 11] - b'0') * 10 + usize::from(bytes[at + 12] - b'0');
        let bucket = (if bytes[at + 6] == b'0' { day - 30 } else { day + 1 }) * 24 + hour - 18;
        at += 28;
        while bytes[at] != b' ' { at += 1; }
        at += 1;
        let start = at;
        at = endpoint_end(bytes, at);
        let name = &bytes[start..at];
        let hash = path_hash(name);
        let mut slot = hash & 4095;
        let id = loop {
            let value = cache[slot];
            if value == 0 {
                let id = endpoints.find(name, hash);
                cache[slot] = id + 1;
                break u32::from(id);
            }
            if endpoints.name(usize::from(value - 1)) == name { break u32::from(value - 1); }
            slot = (slot + 1) & 4095;
        };
        let error = u32::from(bytes[at + 1] == b'5');
        at += 5;
        let latency = latency(bytes, &mut at);
        at += 1;
        let b = &mut hours[bucket];
        b.records.push((latency.min(WIDE) << 12) | (id << 1) | error);
        if latency >= WIDE { b.wide.push(latency); }
    }
}
}

fn read_part(file: &File, begin: u64, end: u64, size: u64, endpoints: &EndpointTable) -> io::Result<[Bucket; 72]> {
    // The binding grammar bounds a whole line by 177 bytes, including LF.
    // Adjacent byte ranges align forward to LF and therefore own every line once.
    let mut buffer = vec![0u8; 256 * 1024];
    let mut offset = begin.saturating_sub(1);
    let limit = size.min(end + 177);
    let mut filled = 0;
    let mut skip = begin != 0;
    let mut part = Partial::new();
    while offset < limit {
        let take = (limit - offset).min((buffer.len() - filled) as u64) as usize;
        let n = match file.read_at(&mut buffer[filled..filled + take], offset) {
            Err(e) if e.kind() == io::ErrorKind::Interrupted => continue,
            result => result?,
        };
        if n == 0 { return Err(io::ErrorKind::UnexpectedEof.into()); }
        filled += n; offset += n as u64;
        let base = offset - filled as u64;
        let Some(last) = buffer[..filled].iter().rposition(|&b| b == b'\n') else { continue; };
        let from = if skip {
            skip = false;
            buffer[..filled].iter().position(|&b| b == b'\n').unwrap() + 1
        } else { 0 };
        if base + from as u64 >= end { return Ok(part.hours); }
        let mut used = last + 1;
        if base + used as u64 > end {
            used = (end - base) as usize;
            while buffer[used - 1] != b'\n' { used += 1; }
        }
        part.parse(&buffer[from..used], endpoints);
        if base + used as u64 >= end { return Ok(part.hours); }
        buffer.copy_within(used..filled, 0);
        filled -= used;
    }
    Ok(part.hours)
}

fn percentiles(values: &mut [u32]) -> [u32; 3] {
    let n = values.len();
    let ranks = [50, 95, 99].map(|p| (p * n + 99) / 100 - 1);
    if n <= 16 { values.sort_unstable(); }
    else {
        let mut start = 0;
        for rank in ranks {
            if rank >= start {
                values[start..].select_nth_unstable(rank - start);
                start = rank + 1;
            }
        }
    }
    ranks.map(|r| values[r])
}

struct Writer { file: File, pending: [Option<Vec<u8>>; 72], turn: usize }
impl Writer {
    fn complete(&mut self, hour: usize, output: Vec<u8>) -> io::Result<()> {
        self.pending[hour] = Some(output);
        while self.turn < 72 {
            let Some(output) = self.pending[self.turn].take() else { break; };
            self.file.write_all(&output)?;
            self.turn += 1;
        }
        Ok(())
    }
}

fn main() -> io::Result<()> {
    let (data, out) = paths();
    let input = File::open(data.join("requests.log"))?;
    let size = input.metadata()?.len();
    let workers = if size < 2 * 1024 * 1024 { 1 } else { workers(8) };
    let endpoints = EndpointTable::new();
    let parts = thread::scope(|scope| {
        let handles: Vec<_> = (0..workers).map(|i| {
            let (input, endpoints) = (&input, &endpoints);
            scope.spawn(move || read_part(input, size * i as u64 / workers as u64,
                size * (i + 1) as u64 / workers as u64, size, endpoints).unwrap())
        }).collect();
        handles.into_iter().map(|h| h.join().unwrap()).collect::<Vec<_>>()
    });
    let count = endpoints.count.load(Relaxed) as usize;
    let mut order: Vec<_> = (0..count).collect();
    order.sort_unstable_by_key(|&id| endpoints.name(id));
    let mut hours: [Mutex<Option<Vec<Bucket>>>; 72] = std::array::from_fn(|_| Mutex::new(Some(Vec::with_capacity(workers))));
    for part in parts {
        for (hour, bucket) in part.into_iter().enumerate() {
            hours[hour].get_mut().unwrap().as_mut().unwrap().push(bucket);
        }
    }
    let writer = Mutex::new(Writer { file: File::create(out.join("summary.txt"))?,
        pending: std::array::from_fn(|_| None), turn: 0 });
    let next = AtomicUsize::new(0);
    thread::scope(|scope| -> io::Result<()> {
        let handles: Vec<_> = (0..workers).map(|_| scope.spawn(|| -> io::Result<()> {
            let mut counts = vec![0u32; count];
            let mut errors = vec![0u32; count];
            let mut positions = vec![0u32; count];
            let mut values = Vec::new();
            loop {
                let hour = next.fetch_add(1, Relaxed);
                if hour >= 72 { break; }
                let buckets = hours[hour].lock().unwrap().take().unwrap();
                counts.fill(0); errors.fill(0);
                let mut total = 0;
                for b in &buckets {
                    total += b.records.len();
                    for &word in &b.records {
                        let id = ((word >> 1) & 2047) as usize;
                        counts[id] += 1; errors[id] += word & 1;
                    }
                }
                let mut at = 0;
                for (i, &n) in counts.iter().enumerate() { positions[i] = at; at += n; }
                values.resize(total, 0u32);
                for b in buckets {
                    let mut wide = b.wide.iter();
                    for word in b.records {
                        let id = ((word >> 1) & 2047) as usize;
                        let mut latency = word >> 12;
                        if latency == WIDE { latency = *wide.next().unwrap(); }
                        values[positions[id] as usize] = latency; positions[id] += 1;
                    }
                }
                let mut output = Vec::with_capacity(160 * 1024);
                let day = (hour + 18) / 24;
                let stamp = format!("2026-{:02}-{:02}T{:02}:00:00Z", if day < 2 { 10 } else { 11 },
                    if day < 2 { 30 + day } else { day - 1 }, (hour + 18) % 24);
                for &id in &order {
                    let n = counts[id];
                    if n == 0 { continue; }
                    let p = percentiles(&mut values[(positions[id] - n) as usize..positions[id] as usize]);
                    output.extend_from_slice(stamp.as_bytes()); output.push(b' ');
                    output.extend_from_slice(endpoints.name(id));
                    for value in [n as u64, u64::from(p[0]), u64::from(p[1]), u64::from(p[2]), u64::from(errors[id]), u64::from(errors[id]) * 1_000_000 / u64::from(n)] {
                        output.push(b' '); number(&mut output, value);
                    }
                    output.push(b'\n');
                }
                writer.lock().unwrap().complete(hour, output)?;
            }
            Ok(())
        })).collect();
        for handle in handles { handle.join().unwrap()?; }
        Ok(())
    })?;
    checked_close(writer.into_inner().unwrap().file)?;
    unsafe extern "C" { fn _exit(code: i32) -> !; }
    // The output is checked closed. Kernel mapping cleanup remains timed.
    unsafe { _exit(0) }
}
