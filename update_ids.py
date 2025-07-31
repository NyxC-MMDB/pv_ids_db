import requests
import json
from pathlib import Path

MIN_PV_ID = 1
MAX_PV_ID = 10000

Path("pv_ids").mkdir(exist_ok=True)

url = "https://divamodarchive.com/api/v1/ids/all_pvs"
resp = requests.get(url)
resp.raise_for_status()
data = resp.json()

reserved = set(int(k) for k in data["reserved_pvs"].keys() if MIN_PV_ID <= int(k) <= MAX_PV_ID)
used = set(int(k) for k in data["uploaded_pvs"].keys() if MIN_PV_ID <= int(k) <= MAX_PV_ID)

with open("pv_ids/reserved.json", "w") as f:
    json.dump(sorted(reserved), f, indent=2)

with open("pv_ids/used.json", "w") as f:
    json.dump(sorted(used), f, indent=2)

print(f"✔️ Updated PV IDs list (range {MIN_PV_ID}–{MAX_PV_ID}))
