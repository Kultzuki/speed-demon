fn main() {
    for _ in 0..6 {
        let start = std::time::Instant::now();
        let workers = std::thread::available_parallelism().unwrap();
        eprintln!("available_parallelism={} ns={}", workers, start.elapsed().as_nanos());
    }
}
