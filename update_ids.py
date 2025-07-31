import requests
import json
from pathlib import Path

Path("pv_ids").mkdir(exist_ok=True)

url = "https://divamodarchive.com/api/v1/ids/all_pvs"
resp = requests.get(url)
resp.raise_for_status()
data = resp.json()

reserved = set(map(int, data["reserved_pvs"].keys()))
used = set(map(int, data["uploaded_pvs"].keys()))

all = set(range(1, 10001))

free = sorted(list(all - reserved - used))

with open("pv_ids/reserved.json", "w") as f:
    json.dump(sorted(list(reserved)), f, indent=2)

with open("pv_ids/used.json", "w") as f:
    json.dump(sorted(list(used)), f, indent=2)

with open("pv_ids/free.json", "w") as f:
    json.dump(free, f, indent=2)

print("✔️ Updated PV IDs database")
