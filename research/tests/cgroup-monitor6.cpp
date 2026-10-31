#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <sys/wait.h>
#include <sys/resource.h>
#include <unistd.h>

int main(int argc,char** argv) {
    if(argc<2)return 2;
    timespec begin,end;
    clock_gettime(CLOCK_MONOTONIC_RAW,&begin);
    pid_t pid=fork();
    if(pid==0) {execv(argv[1],argv+1);_exit(127);}
    int status=0;
    if(pid<0 || waitpid(pid,&status,0)!=pid || !WIFEXITED(status) || WEXITSTATUS(status))return 3;
    clock_gettime(CLOCK_MONOTONIC_RAW,&end);
    unsigned long long peak=0;
    FILE* file=fopen("/sys/fs/cgroup/memory.peak","r");
    if(!file || fscanf(file,"%llu",&peak)!=1)return 4;
    fclose(file);
    double elapsed=end.tv_sec-begin.tv_sec+(end.tv_nsec-begin.tv_nsec)*1e-9;
    rusage usage{};
    getrusage(RUSAGE_CHILDREN,&usage);
    double cpu=usage.ru_utime.tv_sec+usage.ru_utime.tv_usec*1e-6+usage.ru_stime.tv_sec+usage.ru_stime.tv_usec*1e-6;
    printf("METRIC {\"T_s\":%.9f,\"M_bytes\":%llu,\"CPU_s\":%.9f}\n",elapsed,peak,cpu);fflush(stdout);
    const char* output=getenv("OUTPUT_FILE");
    if(!output)return 5;
    execlp("sha256sum","sha256sum",output,nullptr);
    return 6;
}
