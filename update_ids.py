#!/usr/bin/env python3
# coding: utf-8

import requests
import json
import time
from pathlib import Path

MIN_PV_ID = 1
MAX_PV_ID = 4294967296

OUTDIR = Path("pv_ids")
OUTDIR.mkdir(exist_ok=True)

URL = "https://divamodarchive.com/api/v1/ids/all_pvs"


def safe_int(v):
    try:
        return int(v)
    except:
        return None


def fetch_json(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def normalize_posts_and_users(data):
    posts_raw = data.get("posts", {}) or {}
    users_raw = data.get("users", {}) or {}

    posts_by_id = {}

    # index posts by inner ID
    for outer_k, v in posts_raw.items():
        if isinstance(v, dict):
            pid = safe_int(v.get("id"))
            if pid is not None:
                posts_by_id[pid] = v

    # fallback to outer key
    for outer_k, v in posts_raw.items():
        if isinstance(v, dict):
            ok = safe_int(outer_k)
            if ok is not None and ok not in posts_by_id:
                posts_by_id[ok] = v

    users_by_id = {}
    for outer_k, v in users_raw.items():
        if isinstance(v, dict):
            uid = safe_int(v.get("id"))
            if uid is not None:
                users_by_id[uid] = v
            else:
                ok = safe_int(outer_k)
                if ok is not None:
                    users_by_id[ok] = v

    return posts_raw, posts_by_id, users_raw, users_by_id


def get_post_by_id(pid, posts_raw, posts_by_id):
    pid_int = safe_int(pid)
    if pid_int is None:
        return None

    if pid_int in posts_by_id:
        return posts_by_id[pid_int]

    for outer_k, v in posts_raw.items():
        if isinstance(v, dict):
            if safe_int(v.get("id")) == pid_int:
                return v
            if safe_int(outer_k) == pid_int:
                return v
    return None


def get_authors_from_post(post_id, posts_raw, posts_by_id):
    post = get_post_by_id(post_id, posts_raw, posts_by_id)
    if not post:
        return "MM+"

    authors = post.get("authors") or []
    if not isinstance(authors, list):
        return "MM+"

    names = []
    for a in authors:
        if isinstance(a, dict):
            nm = a.get("display_name") or a.get("name")
            if nm:
                names.append(nm)

    return ", ".join(names) if names else "MM+"


def build_reserved_slim(reserved_pvs, users_by_id):
    out = {}
    if not isinstance(reserved_pvs, dict):
        return out

    for pv_id_str, info in reserved_pvs.items():
        if not isinstance(info, dict):
            continue

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

        out[pv_id] = {"username": username}

    return out


def build_used_slim(uploaded_pvs, posts_raw, posts_by_id):
    out = {}

    if isinstance(uploaded_pvs, dict):
        for pv_id_str, entries in uploaded_pvs.items():
            if isinstance(entries, list) and entries:
                entry = entries[0]
            else:
                continue

            if not isinstance(entry, dict):
                continue

            pv_id = safe_int(pv_id_str) or safe_int(entry.get("id"))
            if pv_id is None:
                continue
            if not (MIN_PV_ID <= pv_id <= MAX_PV_ID):
                continue

            title = entry.get("name") or ""
            title_en = entry.get("name_en") or ""
            post_id = entry.get("post")
            username = get_authors_from_post(post_id, posts_raw, posts_by_id)

            out[pv_id] = {
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

            title = entry.get("name") or ""
            title_en = entry.get("name_en") or ""
            post_id = entry.get("post")
            username = get_authors_from_post(post_id, posts_raw, posts_by_id)

            out[pv_id] = {
                "title": title,
                "title_en": title_en,
                "username": username
            }

    return out


def main():
    print("Fetching:", URL)
    data = fetch_json(URL)

    reserved_pvs = data.get("reserved_pvs", {}) or {}
    uploaded_pvs = data.get("uploaded_pvs", {}) or {}

    posts_raw, posts_by_id, users_raw, users_by_id = normalize_posts_and_users(data)

    reserved_slim = build_reserved_slim(reserved_pvs, users_by_id)
    used_slim = build_used_slim(uploaded_pvs, posts_raw, posts_by_id)

    # ---------------------------------------------------
    # TIMESTAMP FORZOSO EN EL ROOT DEL JSON
    # ---------------------------------------------------
    timestamp = str(int(time.time()))

    reserved_out = {"_meta_timestamp": timestamp} | reserved_slim
    used_out = {"_meta_timestamp": timestamp} | used_slim

    with open(OUTDIR / "reserved_slim.json", "w", encoding="utf8") as f:
        json.dump(reserved_out, f, indent=2, ensure_ascii=False)

    with open(OUTDIR / "used_slim.json", "w", encoding="utf8") as f:
        json.dump(used_out, f, indent=2, ensure_ascii=False)

    print("✔ Archivos actualizados forzosamente.")
    print("  reserved:", len(reserved_slim))
    print("  used:", len(used_slim))


if __name__ == "__main__":
    main()