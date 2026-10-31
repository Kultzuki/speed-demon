{ if ($3==prev) rep++; else { if (NR>1) { runs++; sum+=run } run=1 } prev=$3 }
END { print "total", NR, "repeat_next", rep, "runs", runs+1, "avg_run", (NR)/(runs+1) }
