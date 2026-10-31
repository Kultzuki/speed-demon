mod common;
use common::*;
use std::fs::File;
use std::io::{self, Write};
use std::sync::atomic::{AtomicI64, AtomicU32, AtomicUsize, Ordering::Relaxed};
use std::sync::Mutex;
use std::thread;

const INF: u64 = i64::MAX as u64;

struct EdgeStore {
    words: Vec<AtomicU32>,
    overflow: Mutex<Vec<(u32, u32)>>,
    shift: u32,
    mask: u32,
}
impl EdgeStore {
    fn new(n: u32, m: usize) -> Self {
        let bits = (32 - (n - 1).leading_zeros()).max(1);
        assert!(bits < 32);
        let shift = 32 - bits;
        Self { words: (0..m).map(|_| AtomicU32::new(0)).collect(),
               overflow: Mutex::new(Vec::new()), shift, mask: (1 << shift) - 1 }
    }
    fn set(&self, i: u32, node: u32, weight: u32) {
        self.words[i as usize].store((node << self.shift) | weight.min(self.mask), Relaxed);
        if weight >= self.mask { self.overflow.lock().unwrap().push((i, weight)); }
    }
    fn finish(&mut self) { self.overflow.get_mut().unwrap().sort_unstable(); }
    #[inline]
    fn edge(&self, i: u32, overflow: &[(u32, u32)]) -> (u32, u32) {
        let word = self.words[i as usize].load(Relaxed);
        let mut weight = word & self.mask;
        if weight == self.mask {
            weight = overflow[overflow.binary_search_by_key(&i, |&(index, _)| index).unwrap()].1;
        }
        (word >> self.shift, weight)
    }
}

struct Graph { offset: [Vec<u32>; 2], edges: [EdgeStore; 2], n: u32 }
impl Graph {
    fn open(path: &std::path::Path) -> io::Result<Self> {
        let input = MappedFile::open(path)?;
        let bytes = input.bytes();
        let mut at = 0;
        let n = integer(bytes, &mut at); at += 1;
        let m = integer(bytes, &mut at) as usize; at += 1;
        assert!(n != 0);
        let workers = if bytes.len() < 2 * 1024 * 1024 { 1 } else { workers(6) };
        let mut cuts = vec![at; workers + 1];
        cuts[workers] = bytes.len();
        for (i, cut) in cuts.iter_mut().enumerate().take(workers).skip(1) {
            *cut = at + (bytes.len() - at) * i / workers;
            while *cut < bytes.len() && bytes[*cut - 1] != b'\n' { *cut += 1; }
        }
        let mut degrees: [Vec<AtomicU32>; 2] = std::array::from_fn(|_| (0..=n).map(|_| AtomicU32::new(0)).collect());
        thread::scope(|scope| {
            for cut in cuts.windows(2) {
                let degrees = &degrees;
                scope.spawn(move || {
                    let mut p = cut[0];
                    while p < cut[1] {
                        let u = integer(bytes, &mut p) as usize; p += 1;
                        let v = integer(bytes, &mut p) as usize; p += 1;
                        integer(bytes, &mut p); p += 1;
                        degrees[0][u + 1].fetch_add(1, Relaxed);
                        degrees[1][v + 1].fetch_add(1, Relaxed);
                    }
                });
            }
        });
        let offset = std::array::from_fn(|d| {
            let mut sum = 0u32;
            let result = degrees[d].iter_mut().map(|x| { sum += *x.get_mut(); sum }).collect();
            assert_eq!(sum as usize, m);
            result
        });
        let mut edges = std::array::from_fn(|_| EdgeStore::new(n, m));
        for d in 0..2 {
            for (cursor, &start) in degrees[d].iter_mut().zip(&offset[d]) { *cursor.get_mut() = start; }
        }
        thread::scope(|scope| {
            for cut in cuts.windows(2) {
                let (degrees, edges) = (&degrees, &edges);
                scope.spawn(move || {
                    let mut p = cut[0];
                    while p < cut[1] {
                        let u = integer(bytes, &mut p); p += 1;
                        let v = integer(bytes, &mut p); p += 1;
                        let w = integer(bytes, &mut p); p += 1;
                        let a = degrees[0][u as usize].fetch_add(1, Relaxed);
                        let b = degrees[1][v as usize].fetch_add(1, Relaxed);
                        edges[0].set(a, v, w); edges[1].set(b, u, w);
                    }
                });
            }
        });
        for side in &mut edges { side.finish(); }
        Ok(Self { offset, edges, n })
    }
}

// Radix heap adapted from the user's Rust work. Entries retain aligned u64 keys.
struct RadixHeap { buckets: [Vec<(u64, u32)>; 65], last: u64, size: usize }
impl RadixHeap {
    fn new() -> Self { Self { buckets: std::array::from_fn(|_| Vec::new()), last: 0, size: 0 } }
    fn clear(&mut self) { for b in &mut self.buckets { b.clear(); } self.last = 0; self.size = 0; }
    #[inline]
    fn push(&mut self, key: u64, node: u32) {
        self.buckets[(64 - (key ^ self.last).leading_zeros()) as usize].push((key, node));
        self.size += 1;
    }
    fn top(&mut self) -> (u64, u32) {
        if self.buckets[0].is_empty() {
            let i = (1..65).find(|&i| !self.buckets[i].is_empty()).unwrap();
            let mut items = std::mem::take(&mut self.buckets[i]);
            self.last = items.iter().map(|x| x.0).min().unwrap();
            for item in items.drain(..) {
                self.buckets[(64 - (item.0 ^ self.last).leading_zeros()) as usize].push(item);
            }
            self.buckets[i] = items;
        }
        *self.buckets[0].last().unwrap()
    }
    fn pop(&mut self) -> (u64, u32) {
        let item = self.top(); self.buckets[0].pop(); self.size -= 1; item
    }
}

// Full u64 distances and naturally aligned u32 node/generation tags. Node width
// comes from n; exhausting the remaining epoch bits clears every old tag safely.
struct SparseState { distance: Vec<u64>, tags: Vec<u32>, bits: u32, epoch: u32, used: usize }
impl SparseState {
    fn new(n: u32) -> Self {
        let bits = (32 - (n - 1).leading_zeros()).max(1);
        assert!(bits < 32);
        Self { distance: vec![0; 1024], tags: vec![0; 1024], bits, epoch: 0, used: 0 }
    }
    fn clear(&mut self) {
        self.used = 0;
        if self.epoch == u32::MAX >> self.bits { self.tags.fill(0); self.epoch = 1; }
        else { self.epoch += 1; }
    }
    #[inline]
    fn get(&self, node: u32) -> u64 {
        let mut at = node.wrapping_mul(2654435761) as usize & (self.tags.len() - 1);
        let wanted = (self.epoch << self.bits) | node;
        while self.tags[at] >> self.bits == self.epoch {
            if self.tags[at] == wanted { return self.distance[at]; }
            at = (at + 1) & (self.tags.len() - 1);
        }
        INF
    }
    fn set(&mut self, node: u32, distance: u64) {
        if (self.used + 1) * 2 >= self.tags.len() {
            let mut tags = vec![0u32; self.tags.len() * 2];
            let mut values = vec![0u64; tags.len()];
            for (i, &tag) in self.tags.iter().enumerate() {
                if tag >> self.bits != self.epoch { continue; }
                let key = tag & ((1 << self.bits) - 1);
                let mut at = key.wrapping_mul(2654435761) as usize & (tags.len() - 1);
                while tags[at] >> self.bits == self.epoch { at = (at + 1) & (tags.len() - 1); }
                tags[at] = tag; values[at] = self.distance[i];
            }
            self.tags = tags; self.distance = values;
        }
        let wanted = (self.epoch << self.bits) | node;
        let mut at = node.wrapping_mul(2654435761) as usize & (self.tags.len() - 1);
        while self.tags[at] >> self.bits == self.epoch && self.tags[at] != wanted {
            at = (at + 1) & (self.tags.len() - 1);
        }
        if self.tags[at] >> self.bits != self.epoch { self.used += 1; }
        self.tags[at] = wanted; self.distance[at] = distance;
    }
}

struct Search { state: [SparseState; 2], heap: [RadixHeap; 2] }
impl Search {
    fn new(n: u32) -> Self { Self { state: std::array::from_fn(|_| SparseState::new(n)), heap: std::array::from_fn(|_| RadixHeap::new()) } }
    fn run(&mut self, graph: &Graph, overflow: [&[(u32, u32)]; 2], s: u32, t: u32) -> i64 {
        if s == t { return 0; }
        if graph.offset[0][s as usize] == graph.offset[0][s as usize + 1]
            || graph.offset[1][t as usize] == graph.offset[1][t as usize + 1] { return -1; }
        for h in &mut self.heap { h.clear(); }
        for state in &mut self.state { state.clear(); }
        self.state[0].set(s, 0); self.state[1].set(t, 0);
        self.heap[0].push(0, s); self.heap[1].push(0, t);
        let mut best = INF;
        loop {
            for d in 0..2 {
                while self.heap[d].size != 0 {
                    let (key, node) = self.heap[d].top();
                    if key == self.state[d].get(node) { break; }
                    self.heap[d].pop();
                }
            }
            if self.heap[0].size == 0 || self.heap[1].size == 0 { break; }
            if self.heap[0].top().0 + self.heap[1].top().0 >= best { break; }
            let dir = usize::from(self.heap[0].size > self.heap[1].size);
            let (du, u) = self.heap[dir].pop();
            best = best.min(du + self.state[1 - dir].get(u));
            for i in graph.offset[dir][u as usize]..graph.offset[dir][u as usize + 1] {
                let (v, w) = graph.edges[dir].edge(i, overflow[dir]);
                let nd = du + u64::from(w);
                if nd < self.state[dir].get(v) {
                    self.state[dir].set(v, nd); self.heap[dir].push(nd, v);
                    best = best.min(nd + self.state[1 - dir].get(v));
                }
            }
        }
        if best == INF { -1 } else { best as i64 }
    }
}

fn main() -> io::Result<()> {
    let (data, out) = paths();
    let mut graph = Graph::open(&data.join("graph.txt"))?;
    // Freeze the overflow vectors before sharing the graph; searches never lock.
    let overflow = std::array::from_fn::<_, 2, _>(|d| std::mem::take(graph.edges[d].overflow.get_mut().unwrap()));
    let overflow = [&overflow[0][..], &overflow[1][..]];
    let file = MappedFile::open(&data.join("queries.txt"))?;
    let bytes = file.bytes();
    let mut queries = Vec::new();
    let mut at = 0;
    while at < bytes.len() {
        let s = integer(bytes, &mut at); at += 1;
        let t = integer(bytes, &mut at); at += 1;
        queries.push((s, t));
    }
    let answers: Vec<_> = (0..queries.len()).map(|_| AtomicI64::new(0)).collect();
    let next = AtomicUsize::new(0);
    let workers = if queries.len() < 100 { 1 } else { workers(12) };
    thread::scope(|scope| {
        for _ in 0..workers {
            scope.spawn(|| {
                let mut search = Search::new(graph.n);
                loop {
                    let q = next.fetch_add(1, Relaxed);
                    if q >= queries.len() { break; }
                    answers[q].store(search.run(&graph, overflow, queries[q].0, queries[q].1), Relaxed);
                }
            });
        }
    });
    let mut output = Vec::with_capacity(answers.len() * 12);
    for answer in answers {
        let value = answer.into_inner();
        if value < 0 { output.extend_from_slice(b"-1"); }
        else { number(&mut output, value as u64); }
        output.push(b'\n');
    }
    let mut file = File::create(out.join("distances.txt"))?;
    file.write_all(&output)?;
    checked_close(file)
}
