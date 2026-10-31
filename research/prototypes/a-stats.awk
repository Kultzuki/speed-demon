{ n+=length($3); c[$3]++ }
END { print "avg_path_len", n/NR; print "unique_paths", length(c) }
