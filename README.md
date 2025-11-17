# Project Diva PV ID Tracker

Generates a **daily-updated dataset** of *used*, *reserved*, and *available* PV IDs for the Project Diva modding community.

---

## 📌 Overview

This repository automatically fetches PV ID data from **DivaModArchive** once per day and produces lightweight JSON files that tools can use without repeatedly querying the public API.

Designed for:

* Modding tools
* Automated validators
* Scripts that need fast PV ID checks
* Users who want an up-to-date snapshot of PV ID availability

---

## 🔄 How it Works

A scheduled GitHub Action runs every day at 06:00 UTC:

1. Fetches the latest data from the **DivaModArchive** public API (`/api/v1/ids/all_pvs`)
2. Processes:

   * **Uploaded PVs** → PVs already used
   * **Reserved PVs** → PVs claimed but not yet used
   * **Users** → For username attribution
   * **Posts** → For author lists
3. Normalizes the data
4. Saves clean, simplified JSON files in `pv_ids/`

---

## 📁 Output Files

All generated JSON files are located in `pv_ids/`.

### **`used_slim.json`**

Lightweight PV metadata for IDs currently in use.

Includes:

```json
{
  "PV_ID": {
    "title": "Song Title",
    "title_en": "Song Title (EN)",
    "username": "Author Name(s)"
  }
}
```

---

### **`reserved_slim.json`**

Reserved PV IDs with the user who reserved them.

```json
{
  "PV_ID": {
    "username": "User Name"
  }
}
```

---

### *(Optional — if you add it)* `free.json`

All IDs between 1 and 9999 not present in either list.

---

## 🧠 Why Pre-Generate the JSON?

* 📉 **Avoids hitting the API constantly**
* ⚡ **Instant lookups** from tools
* 🤝 **Reduces load on DivaModArchive**
* 🔧 **Easy to integrate** with Python, C#, JavaScript, Lua, etc.

---

## 🚀 Integration Example (Python)

```python
import json

with open("pv_ids/used_slim.json", encoding="utf-8") as f:
    used = json.load(f)

pv_id = 1234

if str(pv_id) in used:
    print("PV already used:", used[str(pv_id)]["title"])
```

---

## 🛠 GitHub Actions Automation

The update job is defined in `.github/workflows/update_ids.yml` and runs:

* 🕕 Daily at 06:00 UTC
* ▶️ Manually with *Run workflow*
* 📝 Always commits a new update (using `--allow-empty`)

---

## 🙌 Credits

All data comes from: **DivaModArchive**
→ [https://divamodarchive.com/](https://divamodarchive.com/)

This repository only **mirrors, simplifies, and caches** the public data.
Full credit for all API content belongs to DivaModArchive.

---

## 📄 License

The generated JSON files and update scripts are **free to use, modify, and distribute**.
Attribution is appreciated but **not required**.

¿Quieres que lo deje listo para copiar-pegar en tu repositorio?
