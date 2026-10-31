from pathlib import Path
p=Path('research/tests/cgroup-monitor6.cpp')
s=p.read_text()
s=s.replace('#include <sys/wait.h>','#include <sys/wait.h>\n#include <sys/resource.h>')
s=s.replace('''    double elapsed=end.tv_sec-begin.tv_sec+(end.tv_nsec-begin.tv_nsec)*1e-9;
    printf("METRIC {\\"T_s\\":%.9f,\\"M_bytes\\":%llu}\\n",elapsed,peak);fflush(stdout);''','''    double elapsed=end.tv_sec-begin.tv_sec+(end.tv_nsec-begin.tv_nsec)*1e-9;
    rusage usage{};
    getrusage(RUSAGE_CHILDREN,&usage);
    double cpu=usage.ru_utime.tv_sec+usage.ru_utime.tv_usec*1e-6+usage.ru_stime.tv_sec+usage.ru_stime.tv_usec*1e-6;
    printf("METRIC {\\"T_s\\":%.9f,\\"M_bytes\\":%llu,\\"CPU_s\\":%.9f}\\n",elapsed,peak,cpu);fflush(stdout);''')
p.write_text(s)
