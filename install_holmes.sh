#!/data/data/com.termux/files/usr/bin/bash
# Install production Paradox Holmes
set -e
DEST="${1:-$HOME/Paradox-Holmes}"
mkdir -p "$DEST"
cd "$DEST"
BASE="https://raw.githubusercontent.com/Paradoxdreamer/Paradox-Holmes/main"
echo "[*] Downloading production build..."
if curl -fsSL "$BASE/holmes.b64" -o /tmp/holmes.b64; then
  python3 -c "import base64,pathlib,re; b=pathlib.Path('/tmp/holmes.b64').read_text(); pathlib.Path('paradox_holmes.py').write_bytes(base64.b64decode(re.sub(r'\\s+','',b)))"
else
  echo "[!] could not fetch holmes.b64"
  exit 1
fi
python3 -c "import py_compile,os; py_compile.compile('paradox_holmes.py', doraise=True); print('[+] paradox_holmes.py OK', os.path.getsize('paradox_holmes.py'), 'bytes')"
echo
echo "Deps:  pip install aiohttp aiohttp-socks beautifulsoup4 lxml stem"
echo "Tor:   pkill -9 tor; tor &; sleep 20"
echo "Test:  curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip"
echo "Hunt:  python3 paradox_holmes.py hunt \"query\" -o out.zip"
