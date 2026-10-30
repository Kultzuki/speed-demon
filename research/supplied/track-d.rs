use std::cmp::Ordering;
use std::collections::BinaryHeap;
use std::fs::File;
use std::io::{BufWriter, Read, Write};
use std::path::PathBuf;
use std::thread;

#[derive(Copy, Clone, Eq, PartialEq)]
struct HeapItem {
    dist: u64,
    node: u32,
}

impl Ord for HeapItem {
    #[inline(always)]
    fn cmp(&self, other: &Self) -> Ordering {
        other.dist.cmp(&self.dist)
    }
}

impl PartialOrd for HeapItem {
    #[inline(always)]
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Copy, Clone)]
struct Edge {
    u: u32,
    v: u32,
    w: u32,
}

#[inline(always)]
fn parse_u32(buf: &[u8], pos: &mut usize) -> u32 {
    while *pos < buf.len() && buf[*pos] <= b' ' {
        *pos += 1;
    }
    let mut v = 0u32;
    while *pos < buf.len() && buf[*pos] >= b'0' && buf[*pos] <= b'9' {
        v = v * 10 + (buf[*pos] - b'0') as u32;
        *pos += 1;
    }
    v
}

fn append_i64(buf: &mut [u8], val: i64, mut pos: usize) -> usize {
    if val == -1 {
        buf[pos] = b'-';
        buf[pos + 1] = b'1';
        return pos + 2;
    }
    if val == 0 {
        buf[pos] = b'0';
        return pos + 1;
    }
    let mut temp = [0u8; 24];
    let mut len = 0;
    let mut uval = val as u64;
    while uval > 0 {
        temp[len] = b'0' + (uval % 10) as u8;
        uval /= 10;
        len += 1;
    }
    while len > 0 {
        len -= 1;
        buf[pos] = temp[len];
        pos += 1;
    }
    pos
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut data_dir = PathBuf::from("/data");
    let mut out_dir = PathBuf::from("/out");

    let args: Vec<String> = std::env::args().collect();
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--data" && i + 1 < args.len() {
            data_dir = PathBuf::from(&args[i + 1]);
            i += 2;
        } else if args[i] == "--out" && i + 1 < args.len() {
            out_dir = PathBuf::from(&args[i + 1]);
            i += 2;
        } else {
            i += 1;
        }
    }

    if let Ok(env_data) = std::env::var("DATA_DIR") {
        if !env_data.is_empty() {
            data_dir = PathBuf::from(env_data);
        }
    }
    if let Ok(env_out) = std::env::var("OUT_DIR") {
        if !env_out.is_empty() {
            out_dir = PathBuf::from(env_out);
        }
    }

    let graph_path = data_dir.join("graph.txt");
    let queries_path = data_dir.join("queries.txt");
    let out_path = out_dir.join("distances.txt");

    if !graph_path.exists() || !queries_path.exists() {
        File::create(&out_path)?;
        return Ok(());
    }

    // 1. Read graph.txt into memory
    let mut graph_bytes = Vec::new();
    File::open(&graph_path)?.read_to_end(&mut graph_bytes)?;

    let mut gpos = 0;
    let n = parse_u32(&graph_bytes, &mut gpos) as usize;
    let m = parse_u32(&graph_bytes, &mut gpos) as usize;

    let mut deg = vec![0u32; n];
    let mut has_in = vec![false; n];
    let mut raw_edges = Vec::with_capacity(m);

    // Single-pass ASCII parsing of all edges
    for _ in 0..m {
        let u = parse_u32(&graph_bytes, &mut gpos);
        let v = parse_u32(&graph_bytes, &mut gpos);
        let w = parse_u32(&graph_bytes, &mut gpos);
        if u != v {
            deg[u as usize] += 1;
            has_in[v as usize] = true;
            raw_edges.push(Edge { u, v, w });
        }
    }
    drop(graph_bytes);

    // Compute prefix sums (offsets)
    let mut offsets = vec![0u32; n + 1];
    let mut cur = 0u32;
    for i in 0..n {
        offsets[i] = cur;
        cur += deg[i];
    }
    offsets[n] = cur;
    let total_valid = cur as usize;

    let mut cursor = offsets[..n].to_vec();
    let mut edges_to = vec![0u32; total_valid];
    let mut edges_weight = vec![0u32; total_valid];

    // Fast in-memory scatter into CSR arrays
    for e in raw_edges {
        let u = e.u as usize;
        let idx = cursor[u] as usize;
        cursor[u] += 1;
        edges_to[idx] = e.v;
        edges_weight[idx] = e.w;
    }
    drop(cursor);
    drop(deg);

    // 2. Read queries.txt
    let mut query_bytes = Vec::new();
    File::open(&queries_path)?.read_to_end(&mut query_bytes)?;

    let mut qpos = 0;
    let mut queries = Vec::new();
    while qpos < query_bytes.len() {
        while qpos < query_bytes.len() && query_bytes[qpos] <= b' ' {
            qpos += 1;
        }
        if qpos >= query_bytes.len() {
            break;
        }
        let s = parse_u32(&query_bytes, &mut qpos);
        let t = parse_u32(&query_bytes, &mut qpos);
        queries.push((s, t));
    }
    drop(query_bytes);

    let num_queries = queries.len();
    let mut answers = vec![-1i64; num_queries];

    // 3. Parallel query execution across 6 worker threads using Forward Dijkstra
    const NUM_THREADS: usize = 6;
    let chunk_size = (num_queries + NUM_THREADS - 1) / NUM_THREADS;

    thread::scope(|s| {
        for (t_idx, ans_chunk) in answers.chunks_mut(chunk_size).enumerate() {
            let start_q = t_idx * chunk_size;
            let q_slice = &queries[start_q..start_q + ans_chunk.len()];
            let offsets_ref = &offsets;
            let edges_to_ref = &edges_to;
            let edges_weight_ref = &edges_weight;
            let has_in_ref = &has_in;

            s.spawn(move || {
                let mut heap = BinaryHeap::with_capacity(32768);
                let mut visited_epoch = vec![0u32; n];
                let mut dist = vec![0u64; n];
                let mut cur_epoch = 0u32;

                for (out_ans, &(sq, tq)) in ans_chunk.iter_mut().zip(q_slice) {
                    if sq == tq {
                        *out_ans = 0;
                        continue;
                    }
                    if offsets_ref[sq as usize] == offsets_ref[sq as usize + 1] {
                        *out_ans = -1;
                        continue;
                    }
                    if !has_in_ref[tq as usize] {
                        *out_ans = -1;
                        continue;
                    }

                    cur_epoch += 1;
                    heap.clear();

                    dist[sq as usize] = 0;
                    visited_epoch[sq as usize] = cur_epoch;
                    heap.push(HeapItem { dist: 0, node: sq });

                    let mut found = -1i64;

                    while let Some(HeapItem { dist: d, node: u }) = heap.pop() {
                        let u_idx = u as usize;
                        if d > dist[u_idx] {
                            continue;
                        }
                        if u == tq {
                            found = d as i64;
                            break;
                        }
                        let start = offsets_ref[u_idx] as usize;
                        let end = offsets_ref[u_idx + 1] as usize;
                        for e_idx in start..end {
                            let v = edges_to_ref[e_idx];
                            let v_idx = v as usize;
                            let nd = d + edges_weight_ref[e_idx] as u64;

                            if visited_epoch[v_idx] != cur_epoch || nd < dist[v_idx] {
                                dist[v_idx] = nd;
                                visited_epoch[v_idx] = cur_epoch;
                                heap.push(HeapItem { dist: nd, node: v });
                            }
                        }
                    }
                    *out_ans = found;
                }
            });
        }
    });

    // 4. Output answers to distances.txt
    let mut writer = BufWriter::with_capacity(1024 * 1024, File::create(&out_path)?);
    let mut line_buf = [0u8; 32];
    for &ans in &answers {
        let pos = append_i64(&mut line_buf, ans, 0);
        line_buf[pos] = b'\n';
        writer.write_all(&line_buf[..pos + 1])?;
    }
    writer.flush()?;

    Ok(())
}