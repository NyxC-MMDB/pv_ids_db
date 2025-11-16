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

# Puede venir vacío, string, None, lista o dict, así que nos aseguramos:
posts = data.get("posts", {})
reserved_pvs = data.get("reserved_pvs", {})
uploaded_pvs = data.get("uploaded_pvs", {})
users = data.get("users", {})

# Aseguramos que "users" sea un dict
if not isinstance(users, dict):
    users = {}

reserved_slim = {}
used_slim = {}

# ============ PROCESAR RESERVADOS ============
for pv_id_str, info in reserved_pvs.items():
    try:
        pv_id = int(pv_id_str)
    except:
        continue

    if not (MIN_PV_ID <= pv_id <= MAX_PV_ID):
        continue

    user_id = info.get("user")
    username = ""

    if user_id is not None:
        ukey = str(user_id)
        if ukey in users:
            uinfo = users[ukey]
            username = uinfo.get("display_name") or uinfo.get("name") or ""

    reserved_slim[pv_id] = {"username": username}


# ============ PROCESAR USADOS ============
# Caso 1: uploaded_pvs es dict (formato viejo)
# ============ PROCESAR USADOS ============
if isinstance(uploaded_pvs, dict):
    for pv_id_str, entries in uploaded_pvs.items():
        try:
            pv_id = int(pv_id_str)
        except:
            continue

        if not entries or not isinstance(entries, list):
            continue

        entry = entries[0]

        title = entry.get("name") or entry.get("name_en") or ""

        # --- NUEVO: obtener usuario desde posts ---
        username = ""
        post_id = entry.get("post")

        if post_id and str(post_id) in posts:
            author_list = posts[str(post_id)].get("authors", [])
            if author_list:
                author = author_list[0]
                username = author.get("display_name") or author.get("name") or ""

        used_slim[pv_id] = {
            "title": title,
            "username": username
        }

elif isinstance(uploaded_pvs, list):
    for entry in uploaded_pvs:
        if not isinstance(entry, dict):
            continue

        pv_id = entry.get("id")
        if not isinstance(pv_id, int):
            continue

        title = entry.get("name") or entry.get("name_en") or ""

        # --- NUEVO: obtener usuario desde posts ---
        username = ""
        post_id = entry.get("post")

        if post_id and str(post_id) in posts:
            author_list = posts[str(post_id)].get("authors", [])
            if author_list:
                author = author_list[0]
                username = author.get("display_name") or author.get("name") or ""

        used_slim[pv_id] = {
            "title": title,
            "username": username
        }


# ============ GUARDAR ============
with open("pv_ids/reserved_slim.json", "w", encoding="utf8") as f:
    json.dump(reserved_slim, f, indent=2, ensure_ascii=False)

with open("pv_ids/used_slim.json", "w", encoding="utf8") as f:
    json.dump(used_slim, f, indent=2, ensure_ascii=False)

print("✔️ Saved slim PV metadata (ID + title + username)")
