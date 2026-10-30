"""Serialized conservative ISA-target comparison on the selected sources."""
import subprocess
import sys
for track in 'abcd':
    subprocess.run([sys.executable,'tools/paired_trials.py',track,
                    f'base=track-{track}/main.cpp',f'v3=track-{track}/main.cpp',
                    '--v3','v3','--runs','5','--name',f'{track}-v3-paired'],check=True)
