from pathlib import Path
s=Path('track-b/main.cpp').read_text().replace('constexpr u32 BUCKET_BITS = 9;','constexpr u32 BUCKET_BITS = 8;')
Path('research/prototypes/b-bucket8-6.cpp').write_text(s)
