include!(concat!(env!("SPEED_DEMON_ROOT"), "/track-d/main.rs"));

#[test]
fn sparse_growth_and_width_derived_epoch_wrap() {
    for n in [2, 65536, 65537, 100001, 1740512, 2147483648] {
        let mut state = SparseState::new(n);
        state.clear();
        let count = n.min(100000);
        for i in 0..count { state.set(i, 8589934590 + u64::from(i)); }
        for i in 0..count { assert_eq!(state.get(i), 8589934590 + u64::from(i)); }
        state.clear();
        for i in 0..count { assert_eq!(state.get(i), INF); }
        state.epoch = u32::MAX >> state.bits;
        let old = (1 << state.bits) | 1;
        state.tags.fill(old);
        state.clear();
        assert_eq!(state.epoch, 1); assert_eq!(state.get(1), INF);
        let wide = 1740511u64 * u64::from(u32::MAX);
        state.set(1, wide); assert_eq!(state.get(1), wide);
    }
}

#[test]
fn exact_compact_weight_fallbacks() {
    for n in [1, 2, 65536, 65537, 1740512] {
        let mut store = EdgeStore::new(n, 5);
        let weights = [0, store.mask - 1, store.mask, store.mask + 1, u32::MAX];
        for (i, &w) in weights.iter().enumerate() { store.set(i as u32, n - 1, w); }
        store.finish();
        let overflow = store.overflow.lock().unwrap();
        for (i, &w) in weights.iter().enumerate() { assert_eq!(store.edge(i as u32, &overflow), (n - 1, w)); }
    }
}

#[test]
fn complete_parallel_csr_against_independent_text_parser() {
    for n in [2, 65537] {
        let path = std::path::PathBuf::from(env!("SPEED_DEMON_ROOT")).join(format!("data/d/continuation7-parallel-wide-{n}/graph.txt"));
        let mut graph = Graph::open(&path).unwrap();
        let text = std::fs::read_to_string(path).unwrap();
        let mut expected: [Vec<(u32, u32, u32)>; 2] = std::array::from_fn(|_| Vec::new());
        for line in text.lines().skip(1) {
            let nums: Vec<u32> = line.split_whitespace().map(|s| s.parse().unwrap()).collect();
            expected[0].push((nums[0], nums[1], nums[2]));
            expected[1].push((nums[1], nums[0], nums[2]));
        }
        for dir in 0..2 {
            let overflow = std::mem::take(graph.edges[dir].overflow.get_mut().unwrap());
            let mut actual = Vec::new();
            for node in 0..graph.n {
                for i in graph.offset[dir][node as usize]..graph.offset[dir][node as usize + 1] {
                    let (other, weight) = graph.edges[dir].edge(i, &overflow);
                    actual.push((node, other, weight));
                }
            }
            actual.sort_unstable(); expected[dir].sort_unstable();
            assert_eq!(actual, expected[dir]);
        }
    }
}

#[test]
fn repeated_wide_zero_and_unreachable_paths() {
    let path = std::path::PathBuf::from(env!("SPEED_DEMON_ROOT")).join("data/d/worked-example/graph.txt");
    let mut graph = Graph::open(&path).unwrap();
    let wide = std::array::from_fn::<_, 2, _>(|d| std::mem::take(graph.edges[d].overflow.get_mut().unwrap()));
    let overflow = [&wide[0][..], &wide[1][..]];
    let mut search = Search::new(graph.n);
    for _ in 0..100 {
        for (s, t, expected) in [(0,2,7), (4,4,0), (3,4,0), (4,6,8589934590), (6,0,-1), (0,6,8589934594), (7,7,0)] {
            assert_eq!(search.run(&graph, overflow, s, t), expected);
        }
    }
}
