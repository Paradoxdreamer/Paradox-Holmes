# Paradox Holmes

**Production-grade dark-web hunter**

Multi-engine .onion search · forum auth · Telegram/Discord mirrors · archive unpack · MIME triage · SQLite FTS5

---

## Install (Termux / Linux) — one shot

```bash
curl -sL https://raw.githubusercontent.com/Paradoxdreamer/Paradox-Holmes/main/install_holmes.sh | bash
cd ~/Paradox-Holmes
pip install aiohttp aiohttp-socks beautifulsoup4 lxml stem

# Tor must be up and bootstrapped
pkill -9 tor 2>/dev/null
tor &
sleep 20
curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip
# expect: "IsTor": true

python3 paradox_holmes.py hunt "your query" -o results.zip
```

Or clone + install:

```bash
git clone https://github.com/Paradoxdreamer/Paradox-Holmes.git
cd Paradox-Holmes
bash install_holmes.sh .
pip install aiohttp aiohttp-socks beautifulsoup4 lxml stem
```

---

## Commands

| Goal | Command |
|------|---------|
| Hunt | `python3 paradox_holmes.py hunt "query" -o results.zip` |
| Search index | `python3 paradox_holmes.py search paradox_index.db` |

---

## What it does (guaranteed behavior)

1. **Tor preflight** — refuses to hunt if SOCKS 9050 is dead (clear message, no traceback spam)
2. **Multi-engine search** — Ahmia / Torch / Tor66 / DeepSearch / Excavator + Ahmia clearnet mirror
3. **Fault isolation** — one dead engine never kills the hunt (`return_exceptions`)
4. **Proxy errors swallowed** — SOCKS failures retry then skip that URL
5. **Harvest → download → unpack → triage → FTS5 index → zip**
6. **Empty results** — exits cleanly with a warning (no crash)

---

## Requirements

- Python 3.10+
- `aiohttp` `aiohttp-socks` `beautifulsoup4` `lxml` `stem`
- Tor SOCKS on `127.0.0.1:9050` (control port 9051 optional for NEWNYM)

---

**Paradox Tech · 2026**
