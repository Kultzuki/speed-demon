use std::fs::File;
use std::io;
use std::os::fd::{AsRawFd, IntoRawFd};
use std::path::{Path, PathBuf};

unsafe extern "C" {
    fn mmap(addr: *mut u8, size: usize, prot: i32, flags: i32, fd: i32, offset: i64) -> *mut u8;
    fn munmap(addr: *mut u8, size: usize) -> i32;
    fn close(fd: i32) -> i32;
}

pub struct MappedFile {
    pointer: *mut u8,
    size: usize,
}
impl MappedFile {
    pub fn open(path: &Path) -> io::Result<Self> {
        let file = File::open(path)?;
        let size = usize::try_from(file.metadata()?.len()).unwrap();
        assert!(size <= isize::MAX as usize);
        let mut pointer = std::ptr::NonNull::<u8>::dangling().as_ptr();
        if size != 0 {
            // The read-only mapping remains owned until all scoped borrowers join.
            pointer = unsafe { mmap(std::ptr::null_mut(), size, 1, 2, file.as_raw_fd(), 0) };
            if pointer as isize == -1 {
                return Err(io::Error::last_os_error());
            }
        }
        Ok(Self { pointer, size })
    }
    pub fn bytes(&self) -> &[u8] {
        // Empty mappings use a non-null aligned dangling pointer.
        unsafe { std::slice::from_raw_parts(self.pointer, self.size) }
    }
}
impl Drop for MappedFile {
    fn drop(&mut self) {
        if self.size != 0 {
            unsafe { munmap(self.pointer, self.size); }
        }
    }
}

pub fn paths() -> (PathBuf, PathBuf) {
    let (mut data, mut out) = (PathBuf::from("/data"), PathBuf::from("/out"));
    let mut args = std::env::args_os().skip(1);
    while let Some(option) = args.next() {
        let value = PathBuf::from(args.next().expect("Missing option value"));
        match option.to_str().unwrap() {
            "--data" => data = value,
            "--out" => out = value,
            _ => panic!("Unknown argument"),
        }
    }
    (data, out)
}

#[inline]
pub fn integer(bytes: &[u8], at: &mut usize) -> u32 {
    let mut value = 0u32;
    // Every contracted number has a space or LF terminator in this slice.
    // Callers enter only at the start of a complete field, including at EOF.
    while unsafe { *bytes.get_unchecked(*at) }.is_ascii_digit() {
        value = value * 10 + u32::from(unsafe { *bytes.get_unchecked(*at) } - b'0');
        *at += 1;
    }
    value
}

#[inline]
pub fn number(out: &mut Vec<u8>, mut value: u64) {
    let mut buffer = [0u8; 20];
    let mut at = buffer.len();
    loop {
        at -= 1;
        buffer[at] = b'0' + (value % 10) as u8;
        value /= 10;
        if value == 0 { break; }
    }
    out.extend_from_slice(&buffer[at..]);
}

pub fn checked_close(file: File) -> io::Result<()> {
    if unsafe { close(file.into_raw_fd()) } == 0 { Ok(()) }
    else { Err(io::Error::last_os_error()) }
}

pub fn workers(limit: usize) -> usize {
    std::thread::available_parallelism().map_or(1, usize::from).min(limit)
}
