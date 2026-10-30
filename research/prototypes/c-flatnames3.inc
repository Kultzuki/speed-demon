// Inline short names and membership share one cache line. Tables may grow;
// old tables and name pages remain alive until every parser has joined.
struct SharedNames {
    struct alignas(64) Node {
        size_t length=0;
        union Bytes {char small[24]{};const char* large;} bytes;
        std::atomic<uint64_t> membership[4]{};
        std::string_view name() const {return {length<=24?bytes.small:bytes.large,length};}
    };
    static_assert(sizeof(Node)==64);
    struct Table {
        size_t capacity;
        std::unique_ptr<std::atomic<Node*>[]> slots;
        explicit Table(size_t n):capacity(n),slots(std::make_unique<std::atomic<Node*>[]>(n)) {}
        Node* find(std::string_view name,size_t hash) const {
            for (size_t i=hash&(capacity-1);;i=(i+1)&(capacity-1)) {
                Node* node=slots[i].load(std::memory_order_acquire);
                if (!node || node->name()==name) return node;
            }
        }
        void publish(Node* node,size_t hash) {
            size_t i=hash&(capacity-1);
            while (slots[i].load(std::memory_order_relaxed)) i=(i+1)&(capacity-1);
            slots[i].store(node,std::memory_order_release);
        }
    };
    struct alignas(64) Shard {
        std::mutex mutex;
        std::vector<std::unique_ptr<Table>> tables;
        std::atomic<Table*> current;
        std::vector<std::unique_ptr<Node[]>> pages;
        std::vector<std::unique_ptr<char[]>> strings;
        size_t count=0,used=128;
        Shard() {tables.push_back(std::make_unique<Table>(512));current.store(tables.back().get());}
        Node* insert(std::string_view name,size_t hash) {
            Table* table=current.load(std::memory_order_relaxed);
            if (Node* node=table->find(name,hash)) return node;
            if ((count+1)*10>=table->capacity*7) {
                auto grown=std::make_unique<Table>(table->capacity*2);
                for (size_t i=0;i<table->capacity;++i) if (Node* node=table->slots[i].load(std::memory_order_relaxed))
                    grown->publish(node,std::hash<std::string_view>()(node->name()));
                table=grown.get();tables.push_back(std::move(grown));
                current.store(table,std::memory_order_release);
            }
            if (used==128) {pages.push_back(std::make_unique<Node[]>(128));used=0;}
            Node* node=&pages.back()[used++];node->length=name.size();
            if (name.size()<=24) memcpy(node->bytes.small,name.data(),name.size());
            else {
                auto text=std::make_unique<char[]>(name.size());memcpy(text.get(),name.data(),name.size());
                node->bytes.large=text.get();strings.push_back(std::move(text));
            }
            ++count;table->publish(node,hash);return node;
        }
    };
    std::array<Shard,256> shards;
    bool add(std::string_view name,uint16_t country) {
        size_t hash=std::hash<std::string_view>()(name);
        auto& shard=shards[(hash>>32)&255];
        Node* node=shard.current.load(std::memory_order_acquire)->find(name,hash);
        if (!node) {std::lock_guard<std::mutex> lock(shard.mutex);node=shard.insert(name,hash);}
        uint64_t bit=uint64_t(1)<<(country%64);
        auto& word=node->membership[country/64];
        if (word.load(std::memory_order_relaxed)&bit) return false;
        return !(word.fetch_or(bit,std::memory_order_relaxed)&bit);
    }
};

