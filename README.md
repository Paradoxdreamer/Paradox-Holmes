# Paradox Holmes

**Production-grade dark-web hunter**

Multi-engine .onion search · authenticated forum crawl · Telegram / Discord mirrors · archive unpack · MIME triage · SQLite FTS5 index

---

## Quick start (clone → run)

### Linux

```bash
git clone https://github.com/Paradoxdreamer/Paradox-Holmes.git
cd Paradox-Holmes

pip install aiohttp aiohttp-socks beautifulsoup4 lxml stem

# Tor must be up (SOCKS 9050, control 9051 optional)
# sudo systemctl start tor   # or: tor &

python3 paradox_holmes.py hunt "your query" -o results.zip
python3 paradox_holmes.py search paradox_index.db
```

### Termux (Android)

```bash
pkg update
pkg install -y git python clang libxml2 libxslt pkg-config tor

pip install aiohttp aiohttp-socks beautifulsoup4 stem
pip install lxml
# if lxml still fails:
#   export PKG_CONFIG_PATH=$PREFIX/lib/pkgconfig
#   pip install --no-cache-dir lxml

git clone https://github.com/Paradoxdreamer/Paradox-Holmes.git
cd Paradox-Holmes

tor &
sleep 8

python paradox_holmes.py hunt "your query" -o results.zip
```

---

## Commands

| Goal | Command |
|------|---------|
| Hunt / collect | `python paradox_holmes.py hunt "query" -o results.zip` |
| Search local index | `python paradox_holmes.py search paradox_index.db` |
| Help | `python paradox_holmes.py -h` |

Hunt output zip contains:

```
loot/            # raw downloads
extracted/       # unpacked archives
MANIFEST.txt     # human summary
sources.json     # machine source map
paradox_index.db # FTS5 index
```

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

Optional: `unrar`, `p7zip` for rar/7z.

Tor: SOCKS `127.0.0.1:9050`, control port `9051` for NEWNYM rotation.

---

## Config

Knobs live at the top of `paradox_holmes.py` (Tor URLs, limits, forum cookies, Telegram/Discord lists).

---

**Paradox Tech · 2026**
