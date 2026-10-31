import csv, collections, sys
path = r'data/c/full-seed1/records.csv'
names = collections.Counter()
lens = collections.Counter()
prev = None
rep = 0
n = 0
with open(path, newline='', encoding='utf-8-sig') as f:
    r = csv.reader(f)
    header = next(r)
    for row in r:
        n += 1
        name = row[1]
        names[name] += 1
        lens[len(name)] += 1
        if name == prev: rep += 1
        prev = name
print('records', n)
print('distinct', len(names))
print('top', names.most_common(5))
print('consecutive_repeats', rep)
print('len_min_max_avg', min(lens), max(lens), sum(k*v for k,v in lens.items())/n)
print('len_hist', sorted(lens.items())[:12])
