use std::collections::HashSet;
use std::fs::File;
use std::io::{BufWriter, Read, Write};
use std::path::PathBuf;

#[inline(always)]
fn hash128(bytes: &[u8]) -> (u64, u64) {
    let mut h1: u64 = 0x517cc1b727220a95;
    let mut h2: u64 = 0x9e3779b97f4a7c15;
    for &b in bytes {
        h1 = (h1.rotate_left(5) ^ (b as u64)).wrapping_mul(0x517cc1b727220a95);
        h2 = (h2.rotate_left(7) ^ (b as u64)).wrapping_mul(0x9e3779b97f4a7c15);
    }
    (h1, h2)
}

struct CountryAgg {
    count: u64,
    id_sum: u64,
    amount_sum: i64,
    amount_min: i64,
    amount_max: i64,
    names: HashSet<(u64, u64)>,
    name_bytes: u64,
    note_bytes: u64,
}

impl Default for CountryAgg {
    fn default() -> Self {
        Self {
            count: 0,
            id_sum: 0,
            amount_sum: 0,
            amount_min: i64::MAX,
            amount_max: i64::MIN,
            names: HashSet::new(),
            name_bytes: 0,
            note_bytes: 0,
        }
    }
}

fn format_cents(buf: &mut [u8], cents: i64, mut pos: usize) -> usize {
    if cents == 0 {
        buf[pos..pos + 4].copy_from_slice(b"0.00");
        return pos + 4;
    }
    let ucents = if cents < 0 {
        buf[pos] = b'-';
        pos += 1;
        (-cents) as u64
    } else {
        cents as u64
    };

    let whole = ucents / 100;
    let frac = ucents % 100;

    pos = append_u64(buf, whole, pos);
    buf[pos] = b'.';
    pos += 1;
    buf[pos] = b'0' + (frac / 10) as u8;
    buf[pos + 1] = b'0' + (frac % 10) as u8;
    pos + 2
}

fn append_u64(buf: &mut [u8], mut val: u64, mut pos: usize) -> usize {
    if val == 0 {
        buf[pos] = b'0';
        return pos + 1;
    }
    let mut temp = [0u8; 24];
    let mut len = 0;
    while val > 0 {
        temp[len] = b'0' + (val % 10) as u8;
        val /= 10;
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

    let records_path = data_dir.join("records.csv");
    let regions_path = data_dir.join("regions.csv");
    let out_path = out_dir.join("aggregates.txt");

    if !records_path.exists() || !regions_path.exists() {
        File::create(&out_path)?;
        return Ok(());
    }

    // 1. Load regions.csv into direct lookup table
    let mut regions_file = File::open(&regions_path)?;
    let reg_len = regions_file.metadata()?.len() as usize;
    let mut regions_bytes = Vec::with_capacity(reg_len + 8);
    regions_file.read_to_end(&mut regions_bytes)?;

    let mut region_to_country = vec![0u8; 10_000_000];
    let mut country_names: Vec<String> = vec!["_UNMATCHED".to_string()];

    let mut rpos = 0;
    while rpos < regions_bytes.len() && regions_bytes[rpos] != b'\n' {
        rpos += 1;
    }
    if rpos < regions_bytes.len() {
        rpos += 1;
    }

    while rpos < regions_bytes.len() {
        if regions_bytes[rpos] == b'\r' || regions_bytes[rpos] == b'\n' {
            rpos += 1;
            continue;
        }
        let mut reg_id = 0usize;
        while rpos < regions_bytes.len() && regions_bytes[rpos] >= b'0' && regions_bytes[rpos] <= b'9' {
            reg_id = reg_id * 10 + (regions_bytes[rpos] - b'0') as usize;
            rpos += 1;
        }
        if rpos < regions_bytes.len() && regions_bytes[rpos] == b',' {
            rpos += 1;
        }
        let code_start = rpos;
        while rpos < regions_bytes.len() && regions_bytes[rpos] >= b'A' && regions_bytes[rpos] <= b'Z' {
            rpos += 1;
        }
        let code_bytes = &regions_bytes[code_start..rpos];
        let code_str = std::str::from_utf8(code_bytes)?.to_string();

        let country_id = match country_names.iter().position(|c| c == &code_str) {
            Some(idx) => idx as u8,
            None => {
                country_names.push(code_str);
                (country_names.len() - 1) as u8
            }
        };

        if reg_id < region_to_country.len() {
            region_to_country[reg_id] = country_id;
        }

        while rpos < regions_bytes.len() && regions_bytes[rpos] != b'\n' {
            rpos += 1;
        }
        if rpos < regions_bytes.len() {
            rpos += 1;
        }
    }
    drop(regions_bytes);

    let num_countries = country_names.len();
    let mut aggs: Vec<CountryAgg> = (0..num_countries).map(|_| CountryAgg::default()).collect();

    // 2. Stream records.csv in a 2 MB sliding window buffer (Peak RSS < 50 MB)
    let mut file = File::open(&records_path)?;
    const CHUNK_SIZE: usize = 2 * 1024 * 1024;
    const MAX_RECORD_LEN: usize = 64 * 1024;
    let mut buffer = vec![0u8; CHUNK_SIZE + MAX_RECORD_LEN];

    let mut buf_len = file.read(&mut buffer[..CHUNK_SIZE])?;
    let mut pos = 0;

    // Check optional leading BOM at file start
    if pos + 3 <= buf_len && buffer[pos..pos + 3] == [0xEF, 0xBB, 0xBF] {
        pos += 3;
    }

    // Skip header line
    while pos < buf_len && buffer[pos] != b'\n' {
        pos += 1;
    }
    if pos < buf_len {
        pos += 1;
    }

    let mut name_buf = Vec::with_capacity(256);

    loop {
        // If close to buffer end and not EOF, slide remaining bytes to front and read more
        if pos + MAX_RECORD_LEN > buf_len {
            let rem = buf_len - pos;
            buffer.copy_within(pos..buf_len, 0);
            pos = 0;
            let n = file.read(&mut buffer[rem..rem + CHUNK_SIZE])?;
            buf_len = rem + n;
            if buf_len == 0 {
                break;
            }
        }

        // Optional BOM at record boundary
        if pos + 3 <= buf_len && buffer[pos..pos + 3] == [0xEF, 0xBB, 0xBF] {
            pos += 3;
        }
        if pos >= buf_len {
            break;
        }

        // 1. Field 1: id
        let mut id = 0u64;
        while pos < buf_len && buffer[pos] >= b'0' && buffer[pos] <= b'9' {
            id = id * 10 + (buffer[pos] - b'0') as u64;
            pos += 1;
        }
        if pos < buf_len && buffer[pos] == b',' {
            pos += 1;
        }

        // 2. Field 2: name
        name_buf.clear();
        if pos < buf_len && buffer[pos] == b'"' {
            pos += 1;
            loop {
                if pos >= buf_len {
                    break;
                }
                if buffer[pos] == b'"' {
                    if pos + 1 < buf_len && buffer[pos + 1] == b'"' {
                        name_buf.push(b'"');
                        pos += 2;
                    } else {
                        pos += 1;
                        break;
                    }
                } else {
                    name_buf.push(buffer[pos]);
                    pos += 1;
                }
            }
        }
        if pos < buf_len && buffer[pos] == b',' {
            pos += 1;
        }

        // 3. Field 3: note
        let mut note_len = 0u64;
        if pos < buf_len && buffer[pos] == b'"' {
            pos += 1;
            loop {
                if pos >= buf_len {
                    break;
                }
                if buffer[pos] == b'"' {
                    if pos + 1 < buf_len && buffer[pos + 1] == b'"' {
                        note_len += 1;
                        pos += 2;
                    } else {
                        pos += 1;
                        break;
                    }
                } else {
                    note_len += 1;
                    pos += 1;
                }
            }
        }
        if pos < buf_len && buffer[pos] == b',' {
            pos += 1;
        }

        // 4. Field 4: region_id
        let mut region_id = 0usize;
        while pos < buf_len && buffer[pos] >= b'0' && buffer[pos] <= b'9' {
            region_id = region_id * 10 + (buffer[pos] - b'0') as usize;
            pos += 1;
        }
        if pos < buf_len && buffer[pos] == b',' {
            pos += 1;
        }

        // 5. Field 5: amount
        let mut neg = false;
        if pos < buf_len && buffer[pos] == b'-' {
            neg = true;
            pos += 1;
        }
        let mut whole = 0i64;
        while pos < buf_len && buffer[pos] >= b'0' && buffer[pos] <= b'9' {
            whole = whole * 10 + (buffer[pos] - b'0') as i64;
            pos += 1;
        }
        let mut frac = 0i64;
        if pos < buf_len && buffer[pos] == b'.' {
            pos += 1;
            if pos < buf_len && buffer[pos] >= b'0' && buffer[pos] <= b'9' {
                frac = (buffer[pos] - b'0') as i64 * 10;
                pos += 1;
            }
            if pos < buf_len && buffer[pos] >= b'0' && buffer[pos] <= b'9' {
                frac += (buffer[pos] - b'0') as i64;
                pos += 1;
            }
        }
        let mut cents = whole * 100 + frac;
        if neg {
            cents = -cents;
        }

        // Skip record terminator (CRLF or LF)
        if pos < buf_len && buffer[pos] == b'\r' {
            pos += 1;
        }
        if pos < buf_len && buffer[pos] == b'\n' {
            pos += 1;
        }

        // Lookup country
        let country_id = if region_id < region_to_country.len() {
            region_to_country[region_id] as usize
        } else {
            0
        };

        let target = &mut aggs[country_id];
        target.count += 1;
        target.id_sum += id;
        target.amount_sum += cents;
        if cents < target.amount_min {
            target.amount_min = cents;
        }
        if cents > target.amount_max {
            target.amount_max = cents;
        }
        target.name_bytes += name_buf.len() as u64;
        target.note_bytes += note_len;

        let h128 = hash128(&name_buf);
        target.names.insert(h128);
    }

    // 3. Collect and sort output groups by country code ascending
    let mut order: Vec<usize> = (0..num_countries).filter(|&k| aggs[k].count > 0).collect();
    order.sort_unstable_by(|&a, &b| country_names[a].cmp(&country_names[b]));

    // 4. Write aggregates.txt
    let mut writer = BufWriter::with_capacity(1024 * 1024, File::create(&out_path)?);
    let mut line_buf = [0u8; 512];

    for idx in order {
        let code = country_names[idx].as_bytes();
        let item = &aggs[idx];

        let mut p = 0;
        line_buf[p..p + code.len()].copy_from_slice(code);
        p += code.len();
        line_buf[p] = b' ';
        p += 1;

        p = append_u64(&mut line_buf, item.count, p);
        line_buf[p] = b' ';
        p += 1;

        p = append_u64(&mut line_buf, item.id_sum, p);
        line_buf[p] = b' ';
        p += 1;

        p = format_cents(&mut line_buf, item.amount_sum, p);
        line_buf[p] = b' ';
        p += 1;

        p = format_cents(&mut line_buf, item.amount_min, p);
        line_buf[p] = b' ';
        p += 1;

        p = format_cents(&mut line_buf, item.amount_max, p);
        line_buf[p] = b' ';
        p += 1;

        p = append_u64(&mut line_buf, item.names.len() as u64, p);
        line_buf[p] = b' ';
        p += 1;

        p = append_u64(&mut line_buf, item.name_bytes, p);
        line_buf[p] = b' ';
        p += 1;

        p = append_u64(&mut line_buf, item.note_bytes, p);
        line_buf[p] = b'\n';
        p += 1;

        writer.write_all(&line_buf[..p])?;
    }
    writer.flush()?;

    Ok(())
}