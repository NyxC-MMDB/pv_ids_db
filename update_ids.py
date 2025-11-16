import requests
import json
from pathlib import Path

MIN_PV_ID = 1
MAX_PV_ID = 4294967296

Path("pv_ids").mkdir(exist_ok=True)

url = "https://divamodarchive.com/api/v1/ids/all_pvs"
resp = requests.get(url)
resp.raise_for_status()
data = resp.json()

reserved_slim = {}
for k, v in data["reserved_pvs"].items():
    pv = int(k)
    if MIN_PV_ID <= pv <= MAX_PV_ID:
        title = v[0] if len(v) > 0 else ""
        username = v[1] if len(v) > 1 else ""
        reserved_slim[pv] = {
            "title": title,
            "username": username
        }

used_slim = {}
for k, v in data["uploaded_pvs"].items():
    pv = int(k)
    if MIN_PV_ID <= pv <= MAX_PV_ID:
        title = v[0] if len(v) > 0 else ""
        username = v[1] if len(v) > 1 else ""
        used_slim[pv] = {
            "title": title,
            "username": username
        }

with open("pv_ids/reserved_slim.json", "w", encoding="utf8") as f:
    json.dump(reserved_slim, f, indent=2, ensure_ascii=False)

with open("pv_ids/used_slim.json", "w", encoding="utf8") as f:
    json.dump(used_slim, f, indent=2, ensure_ascii=False)

print("✔️ Saved slim PV metadata (id/title/username only)")
