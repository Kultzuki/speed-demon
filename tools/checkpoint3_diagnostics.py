"""Current B index cardinalities and diagnostic timings, not promotion evidence."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'research/prototypes/checkpoint3-b.cpp').read_text()
source=source.replace('Lookup lookup(dictionary, terms);','Lookup lookup(dictionary, terms);\n        fprintf(stderr,"B terms=%zu bool=%u lookup_bytes=%zu\\n",terms.size(),boolean_count,lookup.slots.capacity()*sizeof(Lookup::Slot));')
source=source.replace('block.count = stop - block.base;','block.count = stop - block.base;\n            uint64_t scanned=0,found=0,anchored=0,booleans=0;')
source=source.replace('if (id == NONE) continue;','++scanned;if (id == NONE) continue;++found;')
source=source.replace('if (term.boolean != NONE) {','if (term.boolean != NONE) {\n                        ++booleans;')
source=source.replace('if (term.anchor != NONE) {','if (term.anchor != NONE) {\n                        ++anchored;')
source=source.replace('''                ++current;
            }
        });''','''                ++current;
            }
            size_t dense=0,sparse=0,occs=0;
            for (auto& list:block.postings) if (list.dense()) ++dense;else sparse+=list.count;
            for (auto& list:block.occurrences) occs+=list.offsets.size();
            fprintf(stderr,"B worker=%u docs=%u scanned=%llu found=%llu boolean=%llu anchor=%llu dense=%zu sparse=%zu occurrences=%zu\\n",worker,block.count,(unsigned long long)scanned,(unsigned long long)found,(unsigned long long)booleans,(unsigned long long)anchored,dense,sparse,occs);
        });''')
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory);(path/'main.cpp').write_text(source)
    subprocess.run(['g++','-std=c++20','-O3','-pthread','-static','-s','-I',str(ROOT/'track-b'),str(path/'main.cpp'),'-o',str(path/'b')],check=True)
    run=subprocess.run([str(path/'b'),'--data','/benchdata/b','--out',directory],capture_output=True,text=True,check=True)
    print(run.stderr)
    (ROOT/'research/results/checkpoint3-b-counts.txt').write_text(run.stderr)
