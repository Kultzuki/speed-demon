"""Stage a deterministic generator-trained build of the unchanged retained kernel."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
training = json.loads((ROOT / 'validation/trackb9-pgo-full-training.json').read_text())
active = ROOT / 'track-b/main.cpp'
assert hashlib.sha256(active.read_bytes()).hexdigest() == training['source_sha256']
archive = ROOT / '.out/trackb9-pgo-submit'
archive.mkdir(exist_ok=False)
for name in ['Dockerfile', 'README.md']:
    shutil.copy2(ROOT / 'track-b' / name, archive / name)
selection_path = ROOT / 'research/trackb9-selection.json'
shutil.copy2(selection_path, archive / 'prior-selection.json')
generator = subprocess.check_output(['git', '-C', str(ROOT / '.competition/official'), 'show', 'HEAD:generators/b_index.py'])
assert hashlib.sha256(generator).hexdigest() == training['generator_sha256']
(ROOT / 'track-b/b_index_generator.py').write_bytes(generator)
shutil.copy2(ROOT / 'build/trackb9-pgo-full/Dockerfile', ROOT / 'track-b/Dockerfile')
selection = json.loads(selection_path.read_text())
selection.update({'phase': 'trackb9-pgo', 'build_training': training,
    'official_status': 'Unchanged exact source; PGO training uses fresh organizer-generated seeds only. Official measurement pending.'})
selection_path.write_text(json.dumps(selection, indent=2) + '\n')
readme = ROOT / 'track-b/README.md'
text = readme.read_text().replace('The build is offline;',
    'The offline build trains GCC profiles on full organizer-generated seeds\n60773 and 284911 using a byte-identical copy of the published generator. Neither\nscoring input nor answer data is present during the build. Python is used only\nin the build stage; the runtime contains the static C++ executable.\nThe build is offline;')
readme.write_text(text)
entry = '''

## Generator-only profile-guided build trial

Keep the exact retained twelve-builder runtime source and standard-library-only
static executable. The offline Docker build runs GCC instrumentation on full
organizer-generator seeds 60773 and 284911, then recompiles using those profiles.
The scoring inputs and validation seed are never build-time training inputs.
The generator is copied byte-for-byte from the frozen official Git blob (SHA
370ae0d056e3f6d1cf9cd1bf59f5d2ccc0ebcf5745481f904aa55f466850bcdd).
The published rules allow this build-time training and exempt that exact file
from source size. Python is a build-stage dependency only; runtime D remains 1.

The first uncached offline image build completed in 269.032 seconds, below the
600-second limit. Frozen executable SHA-256:
ed29c3aef54ef37b02387f43c7a0114a66902b3e882177c78096c0d2cfd24538.
Local public K ratio=1.034789 and independent full-seed K ratio=1.019043 including
the Dockerfile source-size increase from S=960 to S=970. These are local tests,
not an official gain. The exact PGO binary is separately checked against all
36 datasets; existing ASan/UBSan/direct gates identify this unchanged source.
Official retention remains pending. Evidence: validation/trackb9-pgo-full-* and
validation/trackb9-pgo-production-release.json.
'''
for name in ['track-b/PERF.md', 'research/CONTINUATION9_TRACK_B.md']:
    with (ROOT / name).open('a') as stream: stream.write(entry)
print('Staged generator-only PGO Dockerfile; exact retained runtime source unchanged.')
