//! Speed Demon 2026, Track D (Traverse): exact shortest-path distances.
//!
//! 1. mmap graph.txt and parse the edge lines on every thread at once.
//! 2. Build a compressed adjacency array (CSR).
//! 3. Renumber nodes in BFS order: input ids are a random shuffle, so without this
//!    almost every edge a search follows is a cache miss.
//! 4. Answer queries in parallel, one Dijkstra with a radix heap per query, stopping
//!    when the target is settled. s == t is 0; a target with no in-edges or a source
//!    with no out-edges is unreachable, so those never sweep the graph.
//! Distances are u64: a path can be longer than 2^32 - 1.

use std::fs::File;
use std::io::Write;
use std::os::fd::AsRawFd;
use std::sync::atomic::{AtomicU32, AtomicUsize, Ordering::Relaxed};

extern "C" {
    fn mmap(addr: *mut u8, len: usize, prot: i32, flags: i32, fd: i32, off: i64) -> *mut u8;
}

fn map_file(path: &str) -> &'static [u8] {
    let file = File::open(path).expect("open");
    let len = file.metadata().expect("stat").len() as usize;
    if len == 0 {
        return &[];
    }
    // PROT_READ = 1, MAP_PRIVATE = 2. Lives until exit.
    let ptr = unsafe { mmap(std::ptr::null_mut(), len, 1, 2, file.as_raw_fd(), 0) };
    assert!(ptr as isize != -1, "mmap failed");
    unsafe { std::slice::from_raw_parts(ptr, len) }
}

/// Reads a decimal number at `*p` and leaves `*p` on the byte after it.
#[inline(always)]
fn read_uint(s: &[u8], p: &mut usize) -> u64 {
    let mut v = 0;
    while s[*p] >= b'0' {
        v = v * 10 + (s[*p] - b'0') as u64;
        *p += 1;
    }
    v
}

#[derive(Clone, Copy, Default)]
struct Arc {
    head: u32,
    w: u32,
}

/// Monotone priority queue: a key is filed by the highest bit where it differs
/// from the last minimum popped; each item moves down at most 64 times.
struct RadixHeap {
    b: Vec<Vec<(u64, u32)>>,
    last: u64,
    size: usize,
}

impl RadixHeap {
    fn new() -> Self {
        RadixHeap {
            b: vec![Vec::new(); 65],
            last: 0,
            size: 0,
        }
    }
    #[inline(always)]
    fn bucket(k: u64, last: u64) -> usize {
        if k == last {
            0
        } else {
            64 - (k ^ last).leading_zeros() as usize
        }
    }
    #[inline(always)]
    fn push(&mut self, k: u64, v: u32) {
        self.b[Self::bucket(k, self.last)].push((k, v));
        self.size += 1;
    }
    fn pop(&mut self) -> (u64, u32) {
        if self.b[0].is_empty() {
            let i = (1..65).find(|&i| !self.b[i].is_empty()).unwrap();
            let items = std::mem::take(&mut self.b[i]);
            self.last = items.iter().map(|x| x.0).min().unwrap();
            for &x in &items {
                self.b[Self::bucket(x.0, self.last)].push(x);
            }
            self.b[i] = items;
            self.b[i].clear();
        }
        self.size -= 1;
        self.b[0].pop().unwrap()
    }
    fn clear(&mut self) {
        self.b.iter_mut().for_each(Vec::clear);
        self.last = 0;
        self.size = 0;
    }
}

/// Lets threads write disjoint slots of one array.
#[derive(Clone, Copy)]
struct Shared<T>(*mut T);
unsafe impl<T> Send for Shared<T> {}
unsafe impl<T> Sync for Shared<T> {}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let data = args.windows(2).find(|a| a[0] == "--data").map_or("/data", |a| a[1].as_str());
    let out = args.windows(2).find(|a| a[0] == "--out").map_or("/out", |a| a[1].as_str());
    let threads = std::thread::available_parallelism()
        .map_or(1, |n| n.get())
        .clamp(1, 12);

    // ---- Parse: header "n m", then one piece of edge lines per thread.
    let g = map_file(&format!("{data}/graph.txt"));
    let mut p = 0;
    let n = read_uint(g, &mut p) as usize;
    p += 1;
    let m = read_uint(g, &mut p) as usize;
    let body = p + 1;
    let mut cut = vec![g.len(); threads + 1];
    cut[0] = body;
    for t in 1..threads {
        let mut c = (body + (g.len() - body) * t / threads).max(cut[t - 1]);
        while c < g.len() && g[c - 1] != b'\n' {
            c += 1;
        }
        cut[t] = c;
    }
    let outdeg: Vec<AtomicU32> = (0..=n).map(|_| AtomicU32::new(0)).collect();
    let indeg: Vec<AtomicU32> = (0..n).map(|_| AtomicU32::new(0)).collect();
    let parts: Vec<Vec<[u32; 3]>> = std::thread::scope(|s| {
        let hs: Vec<_> = (0..threads)
            .map(|t| {
                let (cut, outdeg, indeg) = (&cut, &outdeg, &indeg);
                s.spawn(move || {
                    let mut e = Vec::with_capacity((cut[t + 1] - cut[t]) / 17 + 16);
                    let mut q = cut[t];
                    while q < cut[t + 1] {
                        let u = read_uint(g, &mut q) as u32;
                        q += 1;
                        let v = read_uint(g, &mut q) as u32;
                        q += 1;
                        let w = read_uint(g, &mut q) as u32;
                        q += 1;
                        outdeg[u as usize].fetch_add(1, Relaxed);
                        indeg[v as usize].fetch_add(1, Relaxed);
                        e.push([u, v, w]);
                    }
                    e
                })
            })
            .collect();
        hs.into_iter().map(|h| h.join().unwrap()).collect()
    });

    // ---- CSR: prefix sums of out-degree, then a parallel scatter.
    let mut first = vec![0u32; n + 1];
    let mut acc = 0;
    for u in 0..=n {
        first[u] = acc;
        acc += outdeg[u].load(Relaxed);
        outdeg[u].store(first[u], Relaxed); // reused as the write cursor
    }
    let mut arcs = vec![Arc::default(); m];
    let dst = Shared(arcs.as_mut_ptr());
    std::thread::scope(|s| {
        for part in parts {
            let cursor = &outdeg;
            s.spawn(move || {
                for [u, v, w] in part {
                    let k = cursor[u as usize].fetch_add(1, Relaxed) as usize;
                    // Each slot is claimed exactly once through the atomic cursor.
                    unsafe { *{ dst }.0.add(k) = Arc { head: v, w } };
                }
            });
        }
    });
    drop(outdeg);

    // ---- Renumber nodes in BFS order so neighbours sit close in memory.
    let mut order: Vec<u32> = Vec::with_capacity(n);
    let mut id = vec![u32::MAX; n];
    for root in 0..n {
        if id[root] != u32::MAX {
            continue;
        }
        id[root] = order.len() as u32;
        order.push(root as u32);
        let mut h = order.len() - 1;
        while h < order.len() {
            let u = order[h] as usize;
            for a in &arcs[first[u] as usize..first[u + 1] as usize] {
                if id[a.head as usize] == u32::MAX {
                    id[a.head as usize] = order.len() as u32;
                    order.push(a.head);
                }
            }
            h += 1;
        }
    }
    let mut first2 = vec![0u32; n + 1];
    let mut has_in = vec![false; n];
    let mut acc = 0;
    for i in 0..n {
        let u = order[i] as usize;
        first2[i] = acc;
        acc += first[u + 1] - first[u];
        has_in[i] = indeg[u].load(Relaxed) > 0;
    }
    first2[n] = m as u32;
    drop(indeg);
    let mut arcs2 = vec![Arc::default(); m];
    let out2 = Shared(arcs2.as_mut_ptr());
    let next = AtomicUsize::new(0);
    std::thread::scope(|s| {
        for _ in 0..threads {
            let (order, id, first, first2, arcs, next) =
                (&order, &id, &first, &first2, &arcs, &next);
            s.spawn(move || loop {
                let b = next.fetch_add(4096, Relaxed);
                if b >= n {
                    break;
                }
                for i in b..(b + 4096).min(n) {
                    let u = order[i] as usize;
                    let mut j = first2[i] as usize;
                    for a in &arcs[first[u] as usize..first[u + 1] as usize] {
                        // Node i owns slots first2[i]..first2[i+1], so writes never overlap.
                        unsafe {
                            *{ out2 }.0.add(j) = Arc {
                                head: id[a.head as usize],
                                w: a.w,
                            }
                        };
                        j += 1;
                    }
                }
            });
        }
    });
    let (first, arcs) = (first2, arcs2);

    // ---- Queries, translated to the new ids.
    let qs = map_file(&format!("{data}/queries.txt"));
    let mut queries = Vec::new();
    let mut q = 0;
    while q < qs.len() {
        let a = read_uint(qs, &mut q) as usize;
        q += 1;
        let b = read_uint(qs, &mut q) as usize;
        q += 1;
        queries.push((id[a] as usize, id[b] as usize));
    }
    let mut answer = vec![u64::MAX; queries.len()];
    let ans = Shared(answer.as_mut_ptr());
    let next = AtomicUsize::new(0);
    std::thread::scope(|s| {
        for _ in 0..threads {
            let (queries, first, arcs, has_in, next) = (&queries, &first, &arcs, &has_in, &next);
            s.spawn(move || {
                // Distance + 1, so 0 means "not reached". alloc_zeroed returns
                // untouched zero pages: only pages a search visits cost memory.
                let mut d: Vec<u64> = vec![0; n];
                let mut touched: Vec<u32> = Vec::new();
                let mut heap = RadixHeap::new();
                loop {
                    let i = next.fetch_add(1, Relaxed);
                    if i >= queries.len() {
                        break;
                    }
                    let (s, t) = queries[i];
                    let mut found = u64::MAX;
                    if s == t {
                        found = 0;
                    } else if has_in[t] && first[s + 1] > first[s] {
                        d[s] = 1;
                        touched.push(s as u32);
                        heap.push(0, s as u32);
                        while heap.size > 0 {
                            let (du, u) = heap.pop();
                            let u = u as usize;
                            if du + 1 > d[u] {
                                continue; // stale entry
                            }
                            if u == t {
                                found = du;
                                break;
                            }
                            for a in &arcs[first[u] as usize..first[u + 1] as usize] {
                                let (nd, v) = (du + a.w as u64, a.head as usize);
                                if d[v] == 0 || nd + 1 < d[v] {
                                    if d[v] == 0 {
                                        touched.push(v as u32);
                                    }
                                    d[v] = nd + 1;
                                    heap.push(nd, v as u32);
                                }
                            }
                        }
                        for &v in &touched {
                            d[v as usize] = 0;
                        }
                        touched.clear();
                        heap.clear();
                    }
                    // Each query index is taken by exactly one thread.
                    unsafe { *{ ans }.0.add(i) = found };
                }
            });
        }
    });

    // ---- Output: one line per query, -1 when unreachable.
    let mut text = Vec::with_capacity(answer.len() * 12);
    for a in answer {
        if a == u64::MAX {
            text.extend_from_slice(b"-1\n");
        } else {
            writeln!(text, "{a}").unwrap();
        }
    }
    File::create(format!("{out}/distances.txt"))
        .and_then(|mut f| f.write_all(&text))
        .expect("write");
    std::process::exit(0);
}
