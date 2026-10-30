"""Extra exact A cases for packed-latency sentinel and overflow stream order."""
from datetime import datetime,timedelta
import random
import validate

def check():
    root=validate.ROOT
    values=[0,(1<<20)-2,(1<<20)-1,1<<20,(1<<20)+1,16777215,4294967295]
    base=datetime(2026,10,30,18)
    lines=[]
    for hour in range(72):
        stamp=(base+timedelta(hours=hour)).strftime('%Y-%m-%dT%H:00:00.000000Z')
        for count in [1,2,3,99,100,101,128,129,257]:
            for i in range(count):
                lines.append(f'{stamp} OPTIONS /threshold/hour{hour}/n{count} {[200,499,500,599][i%4]} {values[(i+hour)%len(values)]}\n')
    # All catalogue-sized endpoint IDs coexist with the threshold groups.
    # Keep total identities at the binding 1,842 entries.
    for i in range(1842-72*9):
        lines.append(f'2026-10-30T18:00:00.000000Z PUT /catalogue/key{i} 599 {values[i%len(values)]}\n')
    random.Random(1048575).shuffle(lines)
    data=root/'data/a/packed-latency-thresholds';data.mkdir(parents=True,exist_ok=True)
    (data/'requests.log').write_text(''.join(lines))
    validate.check('a','packed-latency-thresholds',data)
    data=root/'data/a/packed-wide-heavy';data.mkdir(parents=True,exist_ok=True)
    with (data/'requests.log').open('w') as stream:
        for i in range(60000):
            value=values[(i*13+i//31)%len(values)]
            stamp=['2026-10-30T18:00:00.000000Z','2026-11-02T17:59:59.999999Z'][i%2]
            stream.write(f'{stamp} DELETE /wide/key{i%1842} {[200,499,500,599][i%4]} {value}\n')
    validate.check('a','packed-wide-heavy',data)
