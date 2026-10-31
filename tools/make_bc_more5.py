"""Independent later B two-pass layout and bounded decimal C trials."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/prototypes'

# Reuse the checked-width transformation against the newer two-pass B source.
generator=(ROOT/'tools/make_b_csr5.py').read_text()
generator=generator.replace("research/supplied-fifth/track-b.cpp","research/supplied-sixth/track-b.cpp")
generator=generator.replace("b-csr5.cpp","b-twopass5.cpp")
generator=generator.replace("source=source.replace('struct Index {',", "source=source.replace('struct Index {',")
generator=generator.replace("source=source.replace('std::unique_ptr<uint16_t[]> post;', 'std::unique_ptr<Doc[]> post;')", "source=source.replace('std::unique_ptr<uint16_t[]> post;', 'std::unique_ptr<Doc[]> post;')\nsource=source.replace('std::unique_ptr<uint16_t[]> seg_len;', 'std::unique_ptr<Doc[]> seg_len;')\nsource=source.replace('new uint16_t[size_t(nthreads) * nterms]', 'new Doc[size_t(nthreads) * nterms]')\nsource=source.replace('static_cast<uint16_t>(c)', 'static_cast<Doc>(c)')\nsource=source.replace('static_cast<uint16_t>(doc - first)', 'static_cast<Doc>(doc - first)')")
# The later main writes directly and exits; use checked stdio and return so
# all instantiations retain the shared test interface and proper destruction.
generator=generator.replace("source=source.replace('    return 0;\\n}', '    return;\\n}')", "source=source.replace('open(\"/out/results.txt\", O_WRONLY | O_CREAT | O_TRUNC, 0666)', 'open((paths.out+\"/results.txt\").c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0666)')\nsource=source.replace('    _exit(0);', '    return;')")
exec(compile(generator,str(ROOT/'tools/make_b_csr5.py'),'exec'),{'__file__':str(ROOT/'tools/make_b_csr5.py')})

DECIMAL=r'''
// Up to eight digits use an exact SIMD length and SWAR decimal reduction.
// Longer integers and short tails retain the original uint64 parser.
uint64_t decimal(const char*& p,const char* end) {
    if(end-p>=8) {
        auto bytes=_mm_loadl_epi64(reinterpret_cast<const __m128i*>(p));
        auto digits=_mm_and_si128(_mm_cmpgt_epi8(bytes,_mm_set1_epi8('0'-1)),_mm_cmpgt_epi8(_mm_set1_epi8('9'+1),bytes));
        uint32_t mask=uint32_t(_mm_movemask_epi8(digits))&255;
        unsigned n=std::countr_zero((~mask&255)|256);
        if(n && (n<8 || end-p==8 || unsigned(p[8]-'0')>=10)) {
            uint64_t v=uint64_t(_mm_cvtsi128_si64(bytes))<<((8-n)*8);
            v&=0x0F0F0F0F0F0F0F0FULL;
            v=(v*10+(v>>8))&0x00FF00FF00FF00FFULL;
            v=(v*100+(v>>16))&0x0000FFFF0000FFFFULL;
            p+=n;return (v*10000+(v>>32))&0xFFFFFFFF;
        }
    }
    return integer(p);
}
'''
for piped in [False,True]:
    source=(OUT/('c-prefetch5.cpp' if piped else 'continuation5-start-c.cpp')).read_text()
    source=source.replace('struct Field {',DECIMAL+'\nstruct Field {')
    start=source.index('struct Partial {');stop=source.index('// Section 2.2:',start)
    source=source[:start]+source[start:stop].replace('integer(p)','decimal(p,end)')+source[stop:]
    (OUT/('c-decimal-prefetch5.cpp' if piped else 'c-decimal5.cpp')).write_text(source,encoding='utf-8',newline='\n')
