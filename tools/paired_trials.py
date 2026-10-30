"""Alternate full-hash-checked local runs of explicitly compiled candidates."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("track",choices=list("abcd"))
    parser.add_argument("sources",nargs="+",help="label=source.cpp")
    parser.add_argument("--name",required=True)
    parser.add_argument("--runs",type=int,default=5)
    parser.add_argument("--flags",default="")
    parser.add_argument("--v3",action="append",default=[],help="Compile this label with x86-64-v3")
    args=parser.parse_args()
    manifest=json.loads((ROOT/".competition/SHA256SUMS.json").read_text())["tracks"][args.track]
    data=Path("/benchdata")/args.track
    for name,digest in manifest["inputs_sha256"].items():
        with (data/name).open("rb") as stream:
            assert hashlib.file_digest(stream,"sha256").hexdigest()==digest
    flags=["-std=c++20","-O3","-DNDEBUG","-pthread","-static","-s",*args.flags.split()]
    results={}
    with tempfile.TemporaryDirectory() as directory:
        temp=Path(directory)
        for arg in args.sources:
            label,source=arg.split("=",1)
            path=ROOT/source
            binary=temp/label
            candidate_flags=flags+(['-march=x86-64-v3'] if label in args.v3 else [])
            subprocess.run(["g++",*candidate_flags,"-I",str(ROOT/f"track-{args.track}"),str(path),"-o",str(binary)],check=True)
            results[label]={"source":source,"flags":candidate_flags,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"walls_s":[],"rss_bytes":[]}
        labels=list(results)
        for run in range(args.runs):
            for label in (labels if run%2==0 else labels[::-1]):
                command=[str(temp/label),"--data",str(data),"--out",directory]
                start=time.perf_counter()
                pid=os.posix_spawn(command[0],command,os.environ)
                _,status,usage=os.wait4(pid,0)
                elapsed=time.perf_counter()-start
                assert os.waitstatus_to_exitcode(status)==0
                with (temp/manifest["output"]).open("rb") as stream:
                    digest=hashlib.file_digest(stream,"sha256").hexdigest()
                assert digest==manifest["expected_output_sha256"][0],label
                result=results[label]
                result["walls_s"].append(elapsed)
                result["rss_bytes"].append(usage.ru_maxrss*1024)
                print(f"{label} {run+1}: {elapsed:.6f}s {usage.ru_maxrss/1024:.1f}MiB PASS",flush=True)
    for label,result in results.items():
        ordered=sorted(result["walls_s"])
        result["trimmed_mean_s"]=statistics.mean(ordered[1:-1] if len(ordered)>=3 else ordered)
        print(f"{label}: {result['trimmed_mean_s']:.6f}s",flush=True)
    report={"track":args.track,"flags":flags,"environment":"Local WSL2 paired runs; RSS is not official cgroup memory", "results":results}
    (ROOT/"research/results"/(args.name+".json")).write_text(json.dumps(report,indent=2)+"\n")

if __name__=="__main__":
    main()
