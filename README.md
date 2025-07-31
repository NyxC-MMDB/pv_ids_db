# Project Diva PV ID Tracker

This repository provides a daily-updated list of available, used, and reserved PV IDs for Project Diva modding purposes.

## What it does

- Calls the **DivaModArchive** public API **once per day**
- Parses the current PV ID usage
- Generates three JSON files:
  - `used.json` – IDs currently in use
  - `reserved.json` – IDs manually reserved for future use
  - `free.json` – IDs available for use (from 1 to 9999, excluding used and reserved)

## Why only one API call?

To minimize unnecessary traffic to the **DivaModArchive** servers. The data is cached and stored for fast local access by modding tools and scripts.

## API Attribution

All data comes from the public API provided by [DivaModArchive](https://divamodarchive.com/).  
We do **not** host or control the API — full credit and ownership go to DivaModArchive.

## License

This repository's contents are free to use, modify, and distribute.  
Attribution is appreciated but **not required** for the generated JSON files.
