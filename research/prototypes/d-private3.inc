    // Each parser owns small relative CSR cursors. Prefixing them across
    // parsers gives disjoint write ranges, without atomic degree/edge updates.
    // Any degree too large for the cursor type restarts with a wider type.
    template<class Count> bool build(const std::vector<const char*>& cuts,uint32_t m) {
        unsigned workers=cuts.size()-1;
        std::vector<std::vector<Count>> counts[2];
        for (auto& side:counts) {
            side.resize(workers);
            for (auto& row:side) row.resize(n);
        }
        std::atomic<bool> overflow{false};
        std::vector<std::thread> threads;
        for (unsigned t=0;t<workers;++t) threads.emplace_back([&,t] {
            const char* p=cuts[t];
            while (p<cuts[t+1]) {
                uint32_t u=integer(p);++p;
                uint32_t v=integer(p);++p;
                integer(p);++p;
                for (auto* at:{&counts[0][t][u],&counts[1][t][v]}) {
                    if (*at==std::numeric_limits<Count>::max()) overflow.store(true,std::memory_order_relaxed);
                    else ++*at;
                }
            }
        });
        for (auto& thread:threads) thread.join();
        if (overflow.load()) return false;
        for (unsigned d=0;d<2;++d) {
            offset[d].assign(size_t(n)+1,0);
            for (uint32_t u=0;u<n;++u) {
                uint64_t total=0;
                for (unsigned t=0;t<workers;++t) {
                    auto& cursor=counts[d][t][u];
                    uint64_t degree=cursor;
                    if (total>std::numeric_limits<Count>::max()) return false;
                    cursor=total;total+=degree;
                }
                if (total>std::numeric_limits<Count>::max()) return false;
                offset[d][u+1]=total;
            }
            std::partial_sum(offset[d].begin(),offset[d].end(),offset[d].begin());
            edges[d].configure(n);edges[d].resize(m);
        }
        threads.clear();
        for (unsigned t=0;t<workers;++t) threads.emplace_back([&,t] {
            const char* p=cuts[t];
            while (p<cuts[t+1]) {
                uint32_t u=integer(p);++p;
                uint32_t v=integer(p);++p;
                uint32_t w=integer(p);++p;
                uint32_t a=offset[0][u]+counts[0][t][u]++;
                uint32_t b=offset[1][v]+counts[1][t][v]++;
                edges[0].set(a,{v,w});edges[1].set(b,{u,w});
            }
        });
        for (auto& thread:threads) thread.join();
        for (auto& side:edges) side.finish();
        return true;
    }

