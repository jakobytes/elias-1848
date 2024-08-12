# Takes a CSV file containing poems (poem_id pos line).
# Sorts the poems from the longest to the shortest.

import csv
import sys

reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(sys.stdout, reader.fieldnames)
data = []
for r in reader:
    if data and data[-1][-1]['poem_id'] == r['poem_id']:
        data[-1].append(r)
    else:
        data.append([r])
data.sort(reverse=True, key=len)
for d in data:
    writer.writerows(d)

