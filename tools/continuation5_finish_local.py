"""Finish new regression checks, then benchmark the two pending D/C originals."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
for name in ['continuation5-release','continuation5-sanitized']:
    subprocess.run([sys.executable,str(ROOT/'tools/continuation5_extra.py'),'--name',name],check=True)
for track in 'dc':
    subprocess.run([sys.executable,str(ROOT/'tools/paired_trials.py'),track,
                    f'baseline=research/prototypes/continuation5-start-{track}.cpp',
                    f'supplied=research/prototypes/supplied-fifth-{track}.cpp',
                    '--v3','supplied','--flags=-mpclmul','--name',f'{track}-supplied-fifth5-paired','--runs','3'],check=True)
