from pathlib import Path
for bits,name in [(10,'b-bucket10-6'),(11,'b-bucket11-6')]:
    p=Path(f'research/prototypes/{name}.cpp'); s=p.read_text()
    s=s.replace('constexpr u32 BUCKET_BITS = 9;',f'constexpr u32 BUCKET_BITS = {bits};')
    p.write_text(s)
