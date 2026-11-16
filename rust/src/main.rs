use std::env;
use std::fs::File;
use std::io::{BufReader, Read};

fn main() -> std::io::Result<()> {
    let path = env::args().nth(1).unwrap_or_else(|| ".".into());
    let f = File::open(&path)?;
    let mut r = BufReader::new(f);
    let mut buf = [0u8; 65536];
    let mut h: u64 = 0xcbf29ce484222325;
    loop {
        let n = r.read(&mut buf)?;
        if n == 0 {
            break;
        }
        for b in &buf[..n] {
            h ^= *b as u64;
            h = h.wrapping_mul(0x100000001b3);
        }
    }
    println!("fnv64: {:016x}", h);
    Ok(())
}
