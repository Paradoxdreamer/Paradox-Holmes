#!/data/data/com.termux/files/usr/bin/bash
# Harden Paradox Holmes against Tor/SOCKS crashes (Termux + Linux)
# Usage:
#   cd ~/Paradox-Holmes && bash harden_holmes.sh
#   curl -sL https://raw.githubusercontent.com/Paradoxdreamer/Paradox-Holmes/main/harden_holmes.sh | bash

set -e
cd "${1:-$HOME/Paradox-Holmes}"
if [ ! -f paradox_holmes.py ]; then
  echo "[!] paradox_holmes.py not found in $(pwd)"
  echo "    git clone https://github.com/Paradoxdreamer/Paradox-Holmes.git"
  exit 1
fi

python3 << 'ENDPY'
from pathlib import Path

p = Path("paradox_holmes.py")
t = p.read_text(encoding="utf-8")
changed = []

if "SocksProxyError" not in t:
    needle = "from aiohttp_socks import ProxyConnector"
    insert = (
        "from aiohttp_socks import ProxyConnector\n"
        "try:\n"
        "    from aiohttp_socks import ProxyError as SocksProxyError\n"
        "except ImportError:\n"
        "    try:\n"
        "        from python_socks import ProxyError as SocksProxyError\n"
        "    except ImportError:\n"
        "        class SocksProxyError(Exception):\n"
        "            pass"
    )
    if needle in t:
        t = t.replace(needle, insert, 1)
        changed.append("SocksProxyError import")
    else:
        print("[!] could not patch ProxyConnector import")
else:
    print("[*] SocksProxyError already present")

old = (
    '        except (aiohttp.ClientError, asyncio.TimeoutError) as e:\n'
    '            log.debug("fetch error %s (attempt %d): %s", url[:60], attempt + 1, e)'
)
new = (
    '        except (aiohttp.ClientError, asyncio.TimeoutError, SocksProxyError, OSError, ConnectionError) as e:\n'
    '            log.debug("fetch error %s (attempt %d): %s", url[:60], attempt + 1, e)\n'
    '        except Exception as e:\n'
    '            log.debug("unexpected fetch error %s (attempt %d): %s", url[:60], attempt + 1, e)'
)
if old in t:
    t = t.replace(old, new, 1)
    changed.append("fetch_with_retry")
elif "SocksProxyError, OSError" in t:
    print("[*] fetch_with_retry already hardened")
else:
    print("[!] fetch_with_retry pattern not found (file may already differ)")

old = (
    "        results = await asyncio.gather(*(search_engine(session, e, query, tor) for e in ENGINES))\n"
    "    seen:   Set[str]  = set()\n"
    "    unique: List[Hit] = []\n"
    "    for batch in results:\n"
    "        for h in batch:"
)
new = (
    "        results = await asyncio.gather(\n"
    "            *(search_engine(session, e, query, tor) for e in ENGINES),\n"
    "            return_exceptions=True,\n"
    "        )\n"
    "    seen:   Set[str]  = set()\n"
    "    unique: List[Hit] = []\n"
    "    for batch in results:\n"
    "        if isinstance(batch, Exception):\n"
    "            log.warning(\"engine error: %s\", batch)\n"
    "            continue\n"
    "        for h in batch:"
)
if old in t:
    t = t.replace(old, new, 1)
    changed.append("multi_search")
elif "return_exceptions=True" in t:
    print("[*] multi_search already hardened")
else:
    print("[!] multi_search pattern not found")

if "async def check_tor" not in t:
    pre = '''
async def check_tor() -> bool:
    """Verify SOCKS5 is accepting connections. Returns True if OK."""
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", 9050), timeout=3)
        s.close()
    except OSError:
        log.error("Tor SOCKS not reachable on 127.0.0.1:9050")
        log.error("  Termux:  pkill -9 tor; tor &   then wait for Bootstrapped 100%%")
        log.error("  Test:    curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip")
        return False
    try:
        connector = _make_connector()
        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get("http://httpbin.org/ip") as resp:
                if resp.status == 200:
                    log.info("Tor SOCKS OK")
                    return True
                log.warning("Tor probe HTTP %s", resp.status)
    except Exception as e:
        log.error("Tor SOCKS probe failed: %s", e)
        log.error("  Tor may still be bootstrapping. Wait and retry.")
        log.error("  curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip")
        return False
    return False

'''
    t = t.replace("async def run_hunt(query: str, out_zip: str):", pre + "async def run_hunt(query: str, out_zip: str):", 1)
    changed.append("check_tor")

old_rh = (
    "    print(_banner())\n"
    "    log.info(\"query \u2192 %s\", query)\n"
    "\n"
    "    tor = TorManager()\n"
    "    await tor.renew()\n"
    "\n"
    "    hits = await multi_search(query, tor)"
)
new_rh = (
    "    print(_banner())\n"
    "    log.info(\"query \u2192 %s\", query)\n"
    "\n"
    "    if not await check_tor():\n"
    "        log.error(\"Aborting hunt \u2014 fix Tor first, then re-run.\")\n"
    "        return\n"
    "\n"
    "    tor = TorManager()\n"
    "    await tor.renew()  # soft: warning only if control port closed\n"
    "\n"
    "    try:\n"
    "        hits = await multi_search(query, tor)\n"
    "    except Exception as e:\n"
    "        log.error(\"multi-search failed: %s\", e)\n"
    "        hits = []"
)
if old_rh in t:
    t = t.replace(old_rh, new_rh, 1)
    changed.append("run_hunt guard")
elif "Aborting hunt" in t:
    print("[*] run_hunt already guarded")
else:
    print("[!] run_hunt start pattern not found")

old_main = "        asyncio.run(run_hunt(args.query, out))"
new_main = (
    "        try:\n"
    "            asyncio.run(run_hunt(args.query, out))\n"
    "        except KeyboardInterrupt:\n"
    "            print(\"\\n[!] interrupted\")\n"
    "        except Exception as e:\n"
    "            log.error(\"hunt crashed: %s\", e)\n"
    "            raise SystemExit(1)"
)
if old_main in t and "hunt crashed" not in t:
    t = t.replace(old_main, new_main, 1)
    changed.append("main try/except")
elif "hunt crashed" in t:
    print("[*] main already wrapped")

p.write_text(t, encoding="utf-8")
print("[+] wrote", p.resolve())
if changed:
    print("[+] applied:", ", ".join(changed))
else:
    print("[*] no new patches applied")

import py_compile
py_compile.compile(str(p), doraise=True)
print("[+] syntax OK")
print()
print("Next:")
print("  pkill -9 tor 2>/dev/null; tor &")
print("  sleep 20")
print("  curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip")
print("  python3 paradox_holmes.py hunt \"test\" -o out.zip")
ENDPY
