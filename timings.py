from datetime import datetime
from typing import Dict


times: Dict[int, int] = {}

with open(r"hopperbot-run3.log", "r") as f:
    last = datetime.strptime("09:29:25", "%H:%M:%S")
    for line in f:
        if "ERROR" in line or "Recieved keep alive" in line:
            time_str = line[7:15]
            curr = datetime.strptime(time_str, "%H:%M:%S")
            duration = int((curr - last).total_seconds())
            last = curr
            if duration in times:
                times[duration] += 1
            else:
                times[duration] = 1

for (time, count) in sorted(times.items()):
    print(f"{time}: {count}")
