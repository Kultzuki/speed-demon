from pathlib import Path
s=Path('research/prototypes/c-fasthash6.cpp').read_text()
s=s.replace('''        uint64_t bit=uint64_t(1)<<(country%64);
        auto& word=node->membership[country/64];
        if (word.load(std::memory_order_relaxed)&bit) return false;
        return !(word.fetch_or(bit,std::memory_order_relaxed)&bit);''','''        (void)country;(void)node;
        return true;''')
Path('research/prototypes/c-nomember6.cpp').write_text(s)
