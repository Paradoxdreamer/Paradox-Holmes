# Paradox Holmes

<p align="center">
  <img src="https://i.imgur.com/uiXt4pO.jpeg" alt="Paradox Holmes" width="420"/>
</p>

<p align="center">
  <strong>Production-grade dark-web hunter</strong><br/>
  Multi-engine .onion search • Authenticated forum crawl • Telegram / Discord mirrors<br/>
  Archive unpacking • MIME triage • SQLite FTS5 index • Async identity rotation
</p>

---

## What it is

Paradox Holmes is the production evolution of the Paradox Finder line.  
It is a single-file async hunter built for operators who need structured collection from the clearnet-to-onion surface without babysitting sessions.

It does not pretend to be a full OSINT suite. It does one thing well:  
**find → harvest → download → unpack → triage → index → pack**.

You give it a query. It returns a zip containing the loot, a human-readable MANIFEST, a machine-readable `sources.json`, and a ready-to-query FTS5 database.

---

## Core capabilities

| Layer | Capability |
|-------|------------|
| Search | Multi-engine .onion (Ahmia, Torch, Tor66, DeepSearch, Excavator) |
| Auth | Cookie injection + POST login for private forums |
| Mirrors | Public Telegram channel scrapers + Discord archive mirrors |
| Network | Tor SOCKS5, control-port NEWNYM rotation, exponential backoff |
| Collection | Concurrent downloads with hard byte ceiling |
| Archives | zip / tar / rar / 7z / gz / bz2 / xz (path-traversal safe) |
| Triage | Magic-byte MIME sniffing + high-entropy detection |
| Index | Local SQLite FTS5 with BM25 ranking |
| Output | Single zip: loot + extracted tree + MANIFEST + sources.json + index |

---

## Requirements

```
Python 3.10+
aiohttp
aiohttp-socks
beautifulsoup4
lxml
stem
```

Optional system tools for rar/7z:

```
unrar
7z / p7zip
```

Tor must be running with SOCKS on `127.0.0.1:9050` and control port `9051`.

---

## Quick start

```bash
# Install
pip install aiohttp aiohttp-socks beautifulsoup4 lxml stem

# Hunt
python paradox_holmes.py hunt "your query here" -o results.zip

# Search an existing index later
python paradox_holmes.py search paradox_index.db
```

The hunt command produces a zip. Inside you will find:

```
loot/               # raw downloaded files
extracted/          # unpacked contents
MANIFEST.txt        # human summary
sources.json        # machine-readable source map
paradox_index.db    # FTS5 index
```

---

## Configuration

All knobs live at the top of `paradox_holmes.py`.

### Tor

```python
TOR_SOCKS        = "socks5://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASS = None          # set if you use HashedControlPassword
```

### Limits

```python
MAX_ARCHIVE_BYTES     = 500 * 1024 * 1024   # global download ceiling
MAX_FILE_BYTES        = 95  * 1024 * 1024   # single file ceiling
CONCURRENT_DOWNLOADS  = 8
CONCURRENT_CRAWL      = 6
IDENTITY_ROTATE_EVERY = 15                  # requests between NEWNYM
```

### Authenticated forums

```python
FORUM_CONFIGS = {
    "dread": {
        "base_url":   "http://....onion",
        "login_url":  "http://....onion/login",
        "login_data": {"username": "...", "password": "..."},
        "cookies":    {},                   # optional pre-harvested cookies
        "search_path": "/search?q={query}",
    },
}
```

### Telegram / Discord mirrors

```python
TELEGRAM_CHANNELS = [
    ("https://t.me/s", "channel_name"),
]

DISCORD_MIRRORS = [
    "https://discord.com/channels/...",
]
```

---

## Architecture notes

- **Async throughout.** No blocking sleeps on the event loop except controlled rotation delays.
- **Identity rotation.** Tor NEWNYM is issued every N requests under an async lock so concurrent tasks never race the control port.
- **Byte ceiling.** A shared lock protects a mutable total so concurrent downloads never exceed the global archive budget.
- **Safe unpack.** Path traversal members (`..`, absolute paths) are stripped before extraction.
- **Triage.** Magic signatures + simple heuristics + Shannon entropy check for packed/encrypted payloads.
- **Index.** FTS5 with Porter tokenizer. BM25 ranking. Content capped at 60 kB per document for speed.

---

## Output format

`MANIFEST.txt` is deliberately human:

```
PARADOX FINDER APEX — PRODUCTION MANIFEST
Built by Paradox Tech
Query      : example
Created    : 2026-11-16 12:00:00
Files      : 12
Total bytes: 4,128,441

#    Name                                                Size  MIME                    SHA256
----------------------------------------------------------------------------------------------------
1    payload.zip                                    1,024,000  ZIP/APK/JAR             a1b2...
       source  : http://....onion/...
       triage  : ZIP/APK/JAR | size=1,024,000 bytes
       unpacked: 7 files
```

`sources.json` is the machine twin of the same data.

---

## Search mode

After a hunt you can query the index without re-running the collector:

```bash
python paradox_holmes.py search paradox_index.db
search> credential
  [python source] stealer.py  (12,441 bytes)
    ... snippet with >>>matches<<< ...
```

---

## Design philosophy

Paradox Holmes is intentionally a **single file**.  
No package tree, no plugin system, no config directory.  
You drop it on a machine that already has Tor, you run it, you get a zip.

Branding strings are base64-encoded and decoded only at runtime so the source does not contain plain-text product names that can be casually rewritten.

---

## License / Ownership

Built by **Paradox Tech**.  
All rights retained.  
Do not redistribute without the original branding intact.

---

<p align="center">
  <em>Paradox Holmes — production edition</em>
</p>
