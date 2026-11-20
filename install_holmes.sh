#!/data/data/com.termux/files/usr/bin/bash
# Install production Paradox Holmes (resilient build)
set -e
DEST="${1:-$HOME/Paradox-Holmes}"
mkdir -p "$DEST"
cd "$DEST"
BASE="https://raw.githubusercontent.com/Paradoxdreamer/Paradox-Holmes/main"
echo "[*] Downloading production build (chunks)..."
rm -f /tmp/holmes.b64
for i in 0 1 2 3 4; do
  curl -fsSL "$BASE/holmes.b64.$i" >> /tmp/holmes.b64 || { echo "[!] missing chunk $i"; exit 1; }
done
python3 - << 'PY'
import base64, pathlib, re, py_compile
b = pathlib.Path("/tmp/holmes.b64").read_text()
data = base64.b64decode(re.sub(r"\s+", "", b))
pathlib.Path("paradox_holmes.py").write_bytes(data)
print("[+] paradox_holmes.py", len(data), "bytes")
py_compile.compile("paradox_holmes.py", doraise=True)
print("[+] syntax OK")
PY
echo
echo "Deps:  pip install aiohttp aiohttp-socks beautifulsoup4 lxml stem"
echo "Tor:   pkill -9 tor; tor &; sleep 20"
echo "Test:  curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip"
echo "Hunt:  python3 paradox_holmes.py hunt \"query\" -o out.zip"
