#!/data/data/com.termux/files/usr/bin/bash
set -e
DEST="${1:-$HOME/Paradox-Holmes}"
mkdir -p "$DEST"
cd "$DEST"
echo "[*] Fetching base Holmes from git history..."
if [ -d .git ]; then
  git fetch origin aa4e87b8b30adbd43c71e79cadb48255f869a5d8 2>/dev/null || true
  git show aa4e87b8b30adbd43c71e79cadb48255f869a5d8:paradox_holmes.py > paradox_holmes.py
else
  git clone https://github.com/Paradoxdreamer/Paradox-Holmes.git /tmp/holmes-src
  cd /tmp/holmes-src
  git fetch origin aa4e87b8b30adbd43c71e79cadb48255f869a5d8 2>/dev/null || true
  git show aa4e87b8b30adbd43c71e79cadb48255f869a5d8:paradox_holmes.py > "$DEST/paradox_holmes.py"
  cd "$DEST"
fi
echo "[*] Applying resilience patches..."
curl -fsSL https://raw.githubusercontent.com/Paradoxdreamer/Paradox-Holmes/main/harden_holmes.sh | bash
python3 - << 'ENDPY'
from pathlib import Path
import re, py_compile
t = Path("paradox_holmes.py").read_text(encoding="utf-8")
changed = []
if "Ahmia-Clear" not in t and "ENGINES" in t:
    new_engines = """ENGINES = [
    {"name": "Ahmia",      "url": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={query}", "tor": True},
    {"name": "Torch",      "url": "http://xmh57jrzrnw6insl.onion/4a1f/search.php?query={query}", "tor": True},
    {"name": "Tor66",      "url": "http://tor66sewwizhwfrnrphw53cthpvxj6hr4copuh6zd7lgkoo3cqcmj7yd.onion/search?q={query}", "tor": True},
    {"name": "DeepSearch", "url": "http://search7tdrcvri22rieiwgi5g46qnwsesvnubqav2xakhezv4hjzkkad.onion/search?q={query}", "tor": True},
    {"name": "Excavator",  "url": "http://2fd6cemt4gmccflhm6imvdfvli3nf7zn6rfrwpsy7uhxrgbypvwf5fad.onion/?q={query}", "tor": True},
    {"name": "Ahmia-Clear", "url": "https://ahmia.fi/search/?q={query}", "tor": True},
]"""
    t2, n = re.subn(r"ENGINES\s*=\s*\[.*?\]", new_engines, t, count=1, flags=re.S)
    if n:
        t = t2
        changed.append("engines")
if "return_exceptions=True" not in t or t.count("return_exceptions") < 2:
    t = t.replace(
        "await asyncio.gather(*(harvest(h) for h in hits[:50]))",
        "await asyncio.gather(*(harvest(h) for h in hits[:50]), return_exceptions=True)",
    )
    t = t.replace(
        "await asyncio.gather(*(dl(u) for u in list(candidates)[:100]))",
        "await asyncio.gather(*(dl(u) for u in list(candidates)[:100]), return_exceptions=True)",
    )
    changed.append("gather")
Path("paradox_holmes.py").write_text(t, encoding="utf-8")
py_compile.compile("paradox_holmes.py", doraise=True)
print("[+] production Holmes ready", Path("paradox_holmes.py").stat().st_size, "bytes")
if changed:
    print("[+] extra:", ", ".join(changed))
ENDPY
echo
echo "Deps: pip install aiohttp aiohttp-socks beautifulsoup4 lxml stem"
echo "Tor:  pkill -9 tor; tor &; sleep 20"
echo "Test: curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip"
echo "Hunt: python3 paradox_holmes.py hunt QUERY -o out.zip"
