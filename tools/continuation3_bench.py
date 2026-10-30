"""Compare each exact selected source to its preserved d069bfd kernel."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
for track in 'abcd':
    subprocess.run([sys.executable,str(ROOT/'tools/paired_trials.py'),track,
                    f'checkpoint=research/prototypes/checkpoint3-{track}.cpp',
                    f'selected=track-{track}/main.cpp','--name',f'continuation3-paired-{track}','--runs','5'],check=True)
