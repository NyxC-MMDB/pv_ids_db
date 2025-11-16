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

# Normalizar valores
posts = data.get("posts", {})
reserved_pvs = data.get("reserved_pvs", {})
uploaded_pvs = data.get("uploaded_pvs", {})
users = data.get("users", {})

if not isinstance(users, dict):
    users = {}

reserved_slim = {}
used_slim = {}

# ======================================================
#                  PROCESAR RESERVADOS
# ======================================================
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

    reserved_slim[pv_id] = {
        "username": username
    }


# ======================================================
#                  PROCESAR USADOS
# ======================================================

def get_authors_from_post(post_id):
    """Devuelve string con todos los autores, o 'MM+'"""
    if post_id and str(post_id) in posts:
        authors_list = posts[str(post_id)].get("authors", [])
        if authors_list:
            names = [
                (a.get("display_name") or a.get("name") or "")
                for a in authors_list
            ]
            cleaned = [n for n in names if n]
            if cleaned:
                return ", ".join(cleaned)
    return "MM+"  # fallback


# Caso 1 — Formato dict (API vieja)
if isinstance(uploaded_pvs, dict):
    for pv_id_str, entries in uploaded_pvs.items():
        try:
            pv_id = int(pv_id_str)
        except:
            continue

        if not entries or not isinstance(entries, list):
            continue

        entry = entries[0]

        title = entry.get("name") or ""
        title_en = entry.get("name_en") or ""

        # obtener autores
        post_id = entry.get("post")
        username = get_authors_from_post(post_id)

        used_slim[pv_id] = {
            "title": title,
            "title_en": title_en,
            "username": username
        }

# Caso 2 — Formato lista (API nueva)
elif isinstance(uploaded_pvs, list):
    for entry in uploaded_pvs:
        if not isinstance(entry, dict):
            continue

        pv_id = entry.get("id")
        if not isinstance(pv_id, int):
            continue

        title = entry.get("name") or ""
        title_en = entry.get("name_en") or ""

        # obtener autores
        post_id = entry.get("post")
        username = get_authors_from_post(post_id)

        used_slim[pv_id] = {
            "title": title,
            "title_en": title_en,
            "username": username
        }


# ======================================================
#                      GUARDAR
# ======================================================
with open("pv_ids/reserved_slim.json", "w", encoding="utf8") as f:
    json.dump(reserved_slim, f, indent=2, ensure_ascii=False)

with open("pv_ids/used_slim.json", "w", encoding="utf8") as f:
    json.dump(used_slim, f, indent=2, ensure_ascii=False)

print("✔️ Saved slim PV metadata (ID + title + title_en + username)")