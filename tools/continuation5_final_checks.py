"""Compile and validate the final mix after D's official rollback."""
import subprocess
import sys
for suffix,extra in [('release',[]),('sanitized',['--sanitized'])]:
    name='continuation5-final-'+suffix
    subprocess.run([sys.executable,'tools/refinement_checks.py','--name',name,'--packed-a',*extra],check=True)
    subprocess.run([sys.executable,'tools/continuation5_extra.py','--name',name],check=True)
