#!/usr/bin/env python3
# coding: utf-8
"""
Script robusto para descargar / procesar / normalizar el endpoint:
  GET https://divamodarchive.com/api/v1/ids/all_pvs

Genera:
  pv_ids/reserved_slim.json  -> { pv_id: { "username": ... } }
  pv_ids/used_slim.json      -> { pv_id: { "title", "title_en", "username" } }

Diseñado para manejar respuestas donde las claves externas no son los ids numéricos,
y donde uploaded_pvs puede venir como dict (clave externa -> [entries]) o list.
"""

import requests
import json
from pathlib import Path
from typing import Any, Dict, Optional

MIN_PV_ID = 1
MAX_PV_ID = 4294967296

OUTDIR = Path("pv_ids")
OUTDIR.mkdir(exist_ok=True)

URL = "https://divamodarchive.com/api/v1/ids/all_pvs"

def safe_int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except Exception:
        return None

def fetch_json(url: str) -> Dict[str, Any]:
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def normalize_posts_and_users(data: Dict[str, Any], referenced_post_ids: Optional[set] = None):
    """
    Returns (posts_raw, posts_by_id, users_raw, users_by_id)
    posts_raw / users_raw = original dict from API (possibly keys like additionalProp1)
    posts_by_id / users_by_id = dict indexed by numeric id (int) when available
    """
    posts_raw = data.get("posts", {}) or {}
    users_raw = data.get("users", {}) or {}

    posts_by_id: Dict[int, Dict[str, Any]] = {}
    # 1) index by inner 'id' if present
    for outer_k, v in posts_raw.items():
        if isinstance(v, dict):
            pid = safe_int(v.get("id"))
            if pid is not None:
                posts_by_id[pid] = v

    # 2) If referenced_post_ids provided, search for missing ones by scanning values
    if referenced_post_ids:
        missing = [pid for pid in referenced_post_ids if pid not in posts_by_id]
        if missing:
            for outer_k, v in posts_raw.items():
                if not isinstance(v, dict):
                    continue
                pid = safe_int(v.get("id"))
                if pid is not None and pid in referenced_post_ids and pid not in posts_by_id:
                    posts_by_id[pid] = v

    # 3) Fallback: try to interpret outer key as int
    for outer_k, v in posts_raw.items():
        if isinstance(v, dict) and safe_int(outer_k) is not None:
            key_int = int(outer_k)
            if key_int not in posts_by_id:
                posts_by_id[key_int] = v

    # Normalize users similarly
    users_by_id: Dict[int, Dict[str, Any]] = {}
    for outer_k, v in users_raw.items():
        if isinstance(v, dict):
            uid = safe_int(v.get("id"))
            if uid is not None:
                users_by_id[uid] = v
            else:
                # try outer key as int
                ok = safe_int(outer_k)
                if ok is not None:
                    users_by_id[ok] = v

    return posts_raw, posts_by_id, users_raw, users_by_id

def collect_referenced_post_ids_from_uploaded(uploaded_pvs: Any) -> set:
    referenced = set()
    if isinstance(uploaded_pvs, dict):
        for outer_k, entries in uploaded_pvs.items():
            if isinstance(entries, list):
                for e in entries:
                    if isinstance(e, dict) and e.get("post") is not None:
                        pid = safe_int(e.get("post"))
                        if pid is not None:
                            referenced.add(pid)
            elif isinstance(entries, dict):
                pid = safe_int(entries.get("post"))
                if pid is not None:
                    referenced.add(pid)
    elif isinstance(uploaded_pvs, list):
        for e in uploaded_pvs:
            if isinstance(e, dict) and e.get("post") is not None:
                pid = safe_int(e.get("post"))
                if pid is not None:
                    referenced.add(pid)
    return referenced

def get_post_by_id(pid: Any, posts_raw: Dict[str, Any], posts_by_id: Dict[int, Dict[str, Any]]):
    if pid is None:
        return None
    pid_int = safe_int(pid)
    if pid_int is None:
        return None
    if pid_int in posts_by_id:
        return posts_by_id[pid_int]
    # fallback: search values
    for outer_k, v in posts_raw.items():
        if isinstance(v, dict) and safe_int(v.get("id")) == pid_int:
            return v
        if safe_int(outer_k) == pid_int:
            return v
    return None

def get_authors_from_post(post_id: Any, posts_raw: Dict[str, Any], posts_by_id: Dict[int, Dict[str, Any]]):
    p = get_post_by_id(post_id, posts_raw, posts_by_id)
    if not p:
        return "MM+"
    authors = p.get("authors") or []
    if not isinstance(authors, list):
        return "MM+"
    names = []
    for a in authors:
        if not isinstance(a, dict):
            continue
        name = a.get("display_name") or a.get("name") or ""
        if name:
            names.append(name)
    return ", ".join(names) if names else "MM+"

def build_reserved_slim(reserved_pvs: Any, users_by_id: Dict[int, Dict[str, Any]]):
    reserved_slim: Dict[int, Dict[str, str]] = {}
    if not isinstance(reserved_pvs, dict):
        return reserved_slim
    for pv_id_str, info in reserved_pvs.items():
        if not isinstance(info, dict):
            continue
        # prefer the 'id' inside the info; fallback to key
        pv_id = safe_int(info.get("id")) or safe_int(pv_id_str)
        if pv_id is None:
            continue
        if not (MIN_PV_ID <= pv_id <= MAX_PV_ID):
            continue
        user_id = info.get("user")
        username = ""
        uid_int = safe_int(user_id)
        if uid_int is not None and uid_int in users_by_id:
            uinfo = users_by_id[uid_int]
            username = uinfo.get("display_name") or uinfo.get("name") or ""
        reserved_slim[int(pv_id)] = {"username": username}
    return reserved_slim

def build_used_slim(uploaded_pvs: Any, posts_raw: Dict[str, Any], posts_by_id: Dict[int, Dict[str, Any]]):
    used_slim: Dict[int, Dict[str, str]] = {}
    if isinstance(uploaded_pvs, dict):
        for outer_key, entries in uploaded_pvs.items():
            entry = None
            if isinstance(entries, list) and entries:
                # pick the first dict-like entry
                for e in entries:
                    if isinstance(e, dict):
                        entry = e
                        break
            elif isinstance(entries, dict):
                entry = entries

            if not isinstance(entry, dict):
                continue

            # determine pv_id (try outer_key first, otherwise entry['id'])
            pv_id = safe_int(outer_key) or safe_int(entry.get("id"))
            if pv_id is None:
                continue
            if not (MIN_PV_ID <= pv_id <= MAX_PV_ID):
                continue

            title = entry.get("name") or entry.get("title") or ""
            title_en = entry.get("name_en") or entry.get("title_en") or ""
            post_id = entry.get("post")
            username = get_authors_from_post(post_id, posts_raw, posts_by_id)

            used_slim[int(pv_id)] = {
                "title": title,
                "title_en": title_en,
                "username": username
            }

    elif isinstance(uploaded_pvs, list):
        for entry in uploaded_pvs:
            if not isinstance(entry, dict):
                continue
            pv_id = safe_int(entry.get("id"))
            if pv_id is None:
                continue
            if not (MIN_PV_ID <= pv_id <= MAX_PV_ID):
                continue
            title = entry.get("name") or entry.get("title") or ""
            title_en = entry.get("name_en") or entry.get("title_en") or ""
            post_id = entry.get("post")
            username = get_authors_from_post(post_id, posts_raw, posts_by_id)
            used_slim[int(pv_id)] = {
                "title": title,
                "title_en": title_en,
                "username": username
            }

    return used_slim

def main():
    print("Fetching", URL)
    data = fetch_json(URL)

    # Raw pieces
    reserved_pvs = data.get("reserved_pvs", {}) or {}
    uploaded_pvs = data.get("uploaded_pvs", {}) or {}

    # 1) Collect referenced post IDs from uploaded_pvs (so we can ensure we map posts_by_id)
    referenced_post_ids = collect_referenced_post_ids_from_uploaded(uploaded_pvs)
    print("Referenced post IDs found in uploaded_pvs:", len(referenced_post_ids))

    # 2) Normalize posts and users (index by inner id when possible)
    posts_raw, posts_by_id, users_raw, users_by_id = normalize_posts_and_users(data, referenced_post_ids)
    print("Posts indexed by id:", len(posts_by_id), "Users indexed by id:", len(users_by_id))

    # 3) Build slim dicts
    reserved_slim = build_reserved_slim(reserved_pvs, users_by_id)
    used_slim = build_used_slim(uploaded_pvs, posts_raw, posts_by_id)

    # 4) Persist files
    reserved_path = OUTDIR / "reserved_slim.json"
    used_path = OUTDIR / "used_slim.json"

    with reserved_path.open("w", encoding="utf8") as f:
        json.dump(reserved_slim, f, ensure_ascii=False, indent=2)

    with used_path.open("w", encoding="utf8") as f:
        json.dump(used_slim, f, ensure_ascii=False, indent=2)

    print(f"✔️ Saved: {reserved_path} ({len(reserved_slim)} entries)")
    print(f"✔️ Saved: {used_path} ({len(used_slim)} entries)")

if __name__ == "__main__":
    main()