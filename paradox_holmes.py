#!/usr/bin/env python3
"""
Paradox Holmes
Protected production build
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import random
import re
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus, urljoin, urlparse

import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller

# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("apex")

# ──────────────────────────────────────────────
# PROTECTED BRANDING (base64)
# ──────────────────────────────────────────────
_BANNER_B64 = "CuKVlOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVlwrilZEgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIOKVkQrilZEgICBQQVJBRE9YIEZJTkRFUiBBUEVYICDigJQgIFByb2R1Y3Rpb24gRWRpdGlvbiAgICAgICAgICAgICAgICAg4pWRCuKVkSAgIEJ1aWx0IGJ5IFBhcmFkb3ggVGVjaCAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg4pWRCuKVkSAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg4pWRCuKVkSAgIC5vbmlvbiBzZWFyY2ggIOKAoiAgZm9ydW0gYXV0aCAg4oCiICBUZWxlZ3JhbS9EaXNjb3JkIG1pcnJvcnMgIOKVkQrilZEgICB6aXAvdGFyL3Jhci83eiAg4oCiICBGVFM1IGluZGV4ICDigKIgIGFzeW5jLXNhZmUgcm90YXRpb24gICAgICDilZEK4pWRICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICDilZEK4pWa4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWdCg=="
_BUILT_BY = "QnVpbHQgYnkgUGFyYWRveCBUZWNo"
_NAME = "UGFyYWRveCBGaW5kZXIgQXBleA=="
_MANIFEST = "UEFSQURPWCBGSU5ERVIgQVBFWCDigJQgUFJPRFVDVElPTiBNQU5JRkVTVA=="
_SEARCH_TITLE = "UGFyYWRveCBGaW5kZXIgQXBleCDigJQgSW5kZXggU2VhcmNo"
_PROD_ED = "UGFyYWRveCBGaW5kZXIgQXBleCDigJQgUHJvZHVjdGlvbiBFZGl0aW9u"

def _banner() -> str:
    return base64.b64decode(_BANNER_B64).decode("utf-8")

def _built() -> str:
    return base64.b64decode(_BUILT_BY).decode("utf-8")

def _name() -> str:
    return base64.b64decode(_NAME).decode("utf-8")

def _manifest_header() -> str:
    return base64.b64decode(_MANIFEST).decode("utf-8")

def _search_title() -> str:
    return base64.b64decode(_SEARCH_TITLE).decode("utf-8")

def _prod_ed() -> str:
    return base64.b64decode(_PROD_ED).decode("utf-8")

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
TOR_SOCKS             = "socks5://127.0.0.1:9050"
TOR_CONTROL_PORT      = 9051
TOR_CONTROL_PASS: Optional[str] = None

MAX_ARCHIVE_BYTES     = 500 * 1024 * 1024
MAX_FILE_BYTES        = 95  * 1024 * 1024
MAX_DEPTH             = 2
CONCURRENT_DOWNLOADS  = 8
CONCURRENT_CRAWL      = 6
REQUEST_TIMEOUT       = 40
IDENTITY_ROTATE_EVERY = 15
MAX_RETRIES           = 3
RETRY_BASE_DELAY      = 1.5

FORUM_CONFIGS: Dict[str, dict] = {}

TELEGRAM_CHANNELS: List[Tuple[str, str]] = []

DISCORD_MIRRORS: List[str] = []

ALLOWED_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz",
    ".py", ".pyw", ".exe", ".dll", ".bin", ".sh", ".bash", ".pl",
    ".php", ".js", ".ts", ".go", ".rs", ".c", ".cpp",
    ".txt", ".md", ".pdf", ".html", ".json", ".xml", ".sql",
    ".apk", ".jar", ".war", ".db", ".sqlite",
}

TEXT_EXTENSIONS = {".txt", ".md", ".py", ".js", ".ts", ".json", ".html", ".xml", ".sql", ".sh", ".bash", ".c", ".cpp", ".go", ".rs", ".php"}

ENGINES = [
    {"name": "Ahmia",      "url": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={query}"},
    {"name": "Torch",      "url": "http://xmh57jrzrnw6insl.onion/4a1f/search.php?query={query}"},
    {"name": "Tor66",      "url": "http://tor66sewwizhwfrnrphw53cthpvxj6hr4copuh6zd7lgkoo3cqcmj7yd.onion/search?q={query}"},
    {"name": "DeepSearch", "url": "http://search7tdrcvri22rieiwgi5g46qnwsesvnubqav2xakhezv4hjzkkad.onion/search?q={query}"},
    {"name": "Excavator",  "url": "http://2fd6cemt4gmccflhm6imvdfvli3nf7zn6rfrwpsy7uhxrgbypvwf5fad.onion/?q={query}"},
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; rv:115.0) Gecko/20100101 Firefox/115.0",
]

# ──────────────────────────────────────────────
# DATA STRUCTURES
# ──────────────────────────────────────────────
@dataclass
class Hit:
    title:  str
    url:    str
    engine: str
    score:  float = 0.0

@dataclass
class Loot:
    path:        Path
    url:         str
    size:        int
    name:        str
    sha256:      str
    source_page: str
    mime:        str         = "unknown"
    unpacked:    List[str]   = field(default_factory=list)
    triage_notes: str        = ""

# ──────────────────────────────────────────────
# TOR MANAGER
# ──────────────────────────────────────────────
class TorManager:
    def __init__(self):
        self._count = 0
        self._lock  = asyncio.Lock()

    async def renew(self):
        try:
            with Controller.from_port(port=TOR_CONTROL_PORT) as c:
                if TOR_CONTROL_PASS:
                    c.authenticate(password=TOR_CONTROL_PASS)
                else:
                    c.authenticate()
                c.signal(Signal.NEWNYM)
            delay = random.uniform(6, 10)
            log.info("new identity — waiting %.1fs", delay)
            await asyncio.sleep(delay)
        except Exception as e:
            log.warning("renew failed: %s", e)

    async def maybe_rotate(self):
        async with self._lock:
            self._count += 1
            if self._count % IDENTITY_ROTATE_EVERY == 0:
                await self.renew()

# ──────────────────────────────────────────────
# SESSION FACTORY
# ──────────────────────────────────────────────
def _make_connector() -> ProxyConnector:
    return ProxyConnector.from_url(TOR_SOCKS)

async def session_factory(cookies: Optional[Dict[str, str]] = None) -> aiohttp.ClientSession:
    connector = _make_connector()
    timeout   = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    jar       = aiohttp.CookieJar(unsafe=True)
    headers   = {"User-Agent": random.choice(USER_AGENTS)}
    session   = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers=headers,
        cookie_jar=jar,
    )
    if cookies:
        session._injected_cookies = cookies  # type: ignore[attr-defined]
    return session

def _get_request_kwargs(session: aiohttp.ClientSession, url: str) -> dict:
    cookies = getattr(session, "_injected_cookies", None)
    return {"cookies": cookies} if cookies else {}

# ──────────────────────────────────────────────
# RETRY WRAPPER
# ──────────────────────────────────────────────
async def fetch_with_retry(
    session:  aiohttp.ClientSession,
    url:      str,
    tor:      TorManager,
    *,
    method:   str = "GET",
    data:     Optional[dict] = None,
    retries:  int = MAX_RETRIES,
) -> Optional[aiohttp.ClientResponse]:
    extra = _get_request_kwargs(session, url)
    delay = RETRY_BASE_DELAY
    for attempt in range(retries):
        try:
            await tor.maybe_rotate()
            if method == "POST":
                resp = await session.post(url, data=data, **extra)
            else:
                resp = await session.get(url, **extra)
            if resp.status < 500:
                return resp
            log.debug("HTTP %d on %s (attempt %d)", resp.status, url[:60], attempt + 1)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.debug("fetch error %s (attempt %d): %s", url[:60], attempt + 1, e)
        await asyncio.sleep(delay + random.uniform(0, 0.5))
        delay *= 2
    return None

# ──────────────────────────────────────────────
# FORUM AUTH + CRAWL
# ──────────────────────────────────────────────
async def forum_login(session: aiohttp.ClientSession, cfg: dict, tor: TorManager) -> bool:
    if cfg.get("cookies"):
        session._injected_cookies = cfg["cookies"]  # type: ignore[attr-defined]
        log.info("forum: using pre-harvested cookies")
        return True
    login_url  = cfg.get("login_url")
    login_data = cfg.get("login_data", {})
    if not login_url or not login_data:
        return False
    resp = await fetch_with_retry(session, login_url, tor, method="POST", data=login_data)
    if resp is None:
        log.warning("forum login failed: no response")
        return False
    text = await resp.text()
    if 'type="password"' in text.lower():
        log.warning("forum login: credentials rejected")
        return False
    log.info("forum login: success (%s)", login_url[:50])
    return True

async def forum_crawl(
    session:  aiohttp.ClientSession,
    cfg:      dict,
    query:    str,
    tor:      TorManager,
) -> List[str]:
    links: List[str] = []
    base       = cfg["base_url"]
    search_url = base + cfg.get("search_path", "/search?q={query}").format(query=quote_plus(query))

    resp = await fetch_with_retry(session, search_url, tor)
    if resp is None:
        return links
    text = await resp.text()
    soup = BeautifulSoup(text, "lxml")
    for a in soup.find_all("a", href=True):
        full = urljoin(base, a["href"])
        if any(full.lower().endswith(e) for e in ALLOWED_EXTENSIONS) or "download" in full.lower():
            links.append(full)
    log.info("forum %s: %d links", base[:40], len(links))
    return links

# ──────────────────────────────────────────────
# SEARCH ENGINES
# ──────────────────────────────────────────────
async def search_engine(session: aiohttp.ClientSession, engine: dict, query: str, tor: TorManager) -> List[Hit]:
    hits: List[Hit] = []
    url  = engine["url"].format(query=quote_plus(query))
    resp = await fetch_with_retry(session, url, tor)
    if resp is None or resp.status != 200:
        return hits
    text = await resp.text()
    soup = BeautifulSoup(text, "lxml")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(url, href)
        if ".onion" not in full:
            continue
        title = a.get_text(strip=True)[:130] or full
        hits.append(Hit(title=title, url=full, engine=engine["name"]))
    log.info("%-12s  %3d hits", engine["name"], len(hits))
    return hits

async def multi_search(query: str, tor: TorManager) -> List[Hit]:
    async with await session_factory() as session:
        results = await asyncio.gather(*(search_engine(session, e, query, tor) for e in ENGINES))
    seen:   Set[str]  = set()
    unique: List[Hit] = []
    for batch in results:
        for h in batch:
            if h.url not in seen:
                seen.add(h.url)
                unique.append(h)
    log.info("multi-search: %d unique hits", len(unique))
    return unique

# ──────────────────────────────────────────────
# TELEGRAM / DISCORD
# ──────────────────────────────────────────────
async def scrape_telegram(session: aiohttp.ClientSession, tor: TorManager) -> List[str]:
    found: List[str] = []
    for base, channel in TELEGRAM_CHANNELS:
        url = f"{base}/{channel}"
        resp = await fetch_with_retry(session, url, tor)
        if resp is None:
            continue
        text = await resp.text()
        soup = BeautifulSoup(text, "lxml")
        for tag in soup.find_all(class_=re.compile(r"tgme_widget_message")):
            raw = str(tag)
            for m in re.findall(r'https?://[^\s<>"\']+', raw):
                if any(m.lower().endswith(e) for e in ALLOWED_EXTENSIONS):
                    found.append(m)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(href.lower().endswith(e) for e in ALLOWED_EXTENSIONS):
                found.append(href)
        log.info("telegram @%s: %d links", channel, len(found))
    return list(set(found))

async def scrape_discord_mirrors(session: aiohttp.ClientSession, tor: TorManager) -> List[str]:
    found: List[str] = []
    for mirror_url in DISCORD_MIRRORS:
        resp = await fetch_with_retry(session, mirror_url, tor)
        if resp is None:
            continue
        text = await resp.text()
        for m in re.findall(r'https?://[^\s<>"\']+', text):
            if any(m.lower().endswith(e) for e in ALLOWED_EXTENSIONS):
                found.append(m)
    return list(set(found))

# ──────────────────────────────────────────────
# PAGE HARVEST
# ──────────────────────────────────────────────
async def harvest_page(session: aiohttp.ClientSession, hit: Hit, tor: TorManager) -> Set[str]:
    candidates: Set[str] = set()
    resp = await fetch_with_retry(session, hit.url, tor)
    if resp is None or resp.status != 200:
        return candidates
    text = await resp.text()
    soup = BeautifulSoup(text, "lxml")
    for a in soup.find_all("a", href=True):
        full = urljoin(hit.url, a["href"])
        if any(full.lower().endswith(e) for e in ALLOWED_EXTENSIONS) or "download" in full.lower():
            candidates.add(full)
    for m in re.findall(r'https?://[^\s<>"\']+', text):
        if any(m.lower().endswith(e) for e in ALLOWED_EXTENSIONS):
            candidates.add(m)
    await asyncio.sleep(random.uniform(0.5, 1.5))
    return candidates

# ──────────────────────────────────────────────
# DOWNLOAD
# ──────────────────────────────────────────────
def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _safe_name(url: str) -> str:
    name = Path(urlparse(url).path).name or f"file_{hashlib.md5(url.encode()).hexdigest()[:8]}"
    return re.sub(r"[^\w.\-]", "_", name)[:90]

async def download_one(
    session:  aiohttp.ClientSession,
    url:      str,
    dest:     Path,
    source:   str,
    tor:      TorManager,
    byte_budget: "asyncio.Lock",
    total_ref: list,
) -> Optional[Loot]:
    resp = await fetch_with_retry(session, url, tor)
    if resp is None or resp.status != 200:
        return None
    try:
        data = await resp.read()
    except Exception as e:
        log.debug("read error %s: %s", url[:60], e)
        return None

    if len(data) < 64 or len(data) > MAX_FILE_BYTES:
        return None

    async with byte_budget:
        if total_ref[0] + len(data) > MAX_ARCHIVE_BYTES:
            log.info("byte ceiling reached — skipping %s", url[:60])
            return None
        total_ref[0] += len(data)

    name = _safe_name(url)
    path = dest / name
    if path.exists():
        path = dest / f"{path.stem}_{random.randint(1000, 9999)}{path.suffix}"
    path.write_bytes(data)

    loop = asyncio.get_running_loop()
    sha  = await loop.run_in_executor(None, _sha256, path)

    return Loot(path=path, url=url, size=len(data), name=path.name, sha256=sha, source_page=source)

# ──────────────────────────────────────────────
# UNPACK
# ──────────────────────────────────────────────
def _has_tool(name: str) -> bool:
    return shutil.which(name) is not None

def try_unpack(loot: Loot, extract_dir: Path) -> List[str]:
    extracted: List[str] = []
    name  = loot.name.lower()
    out   = extract_dir / loot.name
    out.mkdir(parents=True, exist_ok=True)

    try:
        if name.endswith((".zip", ".jar", ".war", ".apk")):
            with zipfile.ZipFile(loot.path, "r") as z:
                for member in z.namelist():
                    if ".." in member or member.startswith("/"):
                        continue
                    z.extract(member, out)
                extracted = [str(p) for p in out.rglob("*") if p.is_file()]

        elif name.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")):
            with tarfile.open(loot.path) as t:
                safe_members = [m for m in t.getmembers() if not (".." in m.name or m.name.startswith("/"))]
                t.extractall(out, members=safe_members)
                extracted = [str(p) for p in out.rglob("*") if p.is_file()]

        elif name.endswith(".rar"):
            if _has_tool("unrar"):
                subprocess.run(["unrar", "x", "-y", str(loot.path), str(out)], capture_output=True, timeout=120)
                extracted = [str(p) for p in out.rglob("*") if p.is_file()]
            elif _has_tool("7z"):
                subprocess.run(["7z", "x", f"-o{out}", "-y", str(loot.path)], capture_output=True, timeout=120)
                extracted = [str(p) for p in out.rglob("*") if p.is_file()]
            else:
                loot.triage_notes += " [rar: unrar/7z not found]"

        elif name.endswith(".7z"):
            if _has_tool("7z"):
                subprocess.run(["7z", "x", f"-o{out}", "-y", str(loot.path)], capture_output=True, timeout=120)
                extracted = [str(p) for p in out.rglob("*") if p.is_file()]
            else:
                loot.triage_notes += " [7z: 7z not found]"

        elif name.endswith((".gz", ".bz2", ".xz")) and not name.endswith((".tar.gz", ".tar.bz2", ".tar.xz")):
            import gzip, bz2, lzma
            decompressors = {".gz": gzip.open, ".bz2": bz2.open, ".xz": lzma.open}
            ext   = Path(name).suffix
            inner = out / Path(name).stem
            opener = decompressors.get(ext)
            if opener:
                with opener(loot.path, "rb") as src, open(inner, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted = [str(inner)]

    except Exception as e:
        loot.triage_notes += f" [unpack error: {e}]"

    loot.unpacked = extracted
    return extracted

# ──────────────────────────────────────────────
# TRIAGE
# ──────────────────────────────────────────────
MAGIC_SIGNATURES: List[Tuple[bytes, str]] = [
    (b"MZ",           "PE executable"),
    (b"\x7fELF",      "ELF binary"),
    (b"PK\x03\x04",   "ZIP/APK/JAR"),
    (b"Rar!",         "RAR archive"),
    (b"7z\xbc\xaf",   "7-Zip archive"),
    (b"\x1f\x8b",     "gzip"),
    (b"BZh",          "bzip2"),
    (b"\xfd7zXZ",     "XZ archive"),
    (b"%PDF",         "PDF"),
    (b"\xca\xfe\xba\xbe", "Java class / Mach-O fat"),
    (b"dex\n",        "Android DEX"),
    (b"SQLite format 3", "SQLite DB"),
]

def triage_file(path: Path) -> Tuple[str, str]:
    notes: List[str] = []
    mime  = "unknown"
    try:
        data = path.read_bytes()[:8192]
        size = path.stat().st_size

        for magic, label in MAGIC_SIGNATURES:
            if data.startswith(magic):
                mime = label
                notes.append(label)
                break

        if mime == "unknown":
            if b"#!/usr/bin/env python" in data or b"import " in data[:200]:
                mime = "python source"; notes.append("python source")
            elif b"#!/" in data[:4]:
                mime = "shell script"; notes.append("shell script")
            elif b"function " in data and (b"var " in data or b"const " in data or b"let " in data):
                mime = "javascript"; notes.append("javascript")
            elif b"<html" in data.lower()[:200]:
                mime = "html"; notes.append("html")
            elif b"<?php" in data[:10]:
                mime = "php"; notes.append("php")
            elif b"package main" in data[:200]:
                mime = "go source"; notes.append("go source")

        notes.append(f"size={size:,} bytes")

        if size > 1024:
            sample = data[:4096]
            freq   = [sample.count(bytes([i])) for i in range(256)]
            entropy = -sum((c / len(sample)) * __import__("math").log2(c / len(sample)) for c in freq if c > 0)
            if entropy > 7.2:
                notes.append(f"high entropy={entropy:.2f} (possibly packed/encrypted)")

    except Exception:
        pass

    return mime, " | ".join(notes) if notes else "unknown"

# ──────────────────────────────────────────────
# LOCAL FTS5 INDEX
# ──────────────────────────────────────────────
class LocalIndex:
    def __init__(self, db_path: str = "paradox_index.db"):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = asyncio.Lock()
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS meta (
                id      INTEGER PRIMARY KEY,
                path    TEXT UNIQUE,
                name    TEXT,
                sha256  TEXT,
                mime    TEXT,
                size    INTEGER,
                indexed_at TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
                name,
                content,
                content='meta',
                content_rowid='id',
                tokenize='porter unicode61'
            );
        """)
        self.db.commit()

    def _add_sync(self, path: Path, content: str, sha: str, mime: str, size: int):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            self.db.execute(
                "INSERT OR IGNORE INTO meta (path, name, sha256, mime, size, indexed_at) VALUES (?,?,?,?,?,?)",
                (str(path), path.name, sha, mime, size, ts),
            )
            rowid = self.db.execute("SELECT id FROM meta WHERE path=?", (str(path),)).fetchone()[0]
            snippet = content[:60000]
            self.db.execute(
                "INSERT INTO docs (rowid, name, content) VALUES (?,?,?)",
                (rowid, path.name, snippet),
            )
            self.db.commit()
        except sqlite3.IntegrityError:
            pass

    async def add(self, path: Path, content: str, sha: str, mime: str, size: int):
        async with self._lock:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._add_sync, path, content, sha, mime, size)

    def search(self, query: str, limit: int = 20) -> List[dict]:
        try:
            cur = self.db.execute(
                """
                SELECT m.path, m.name, m.mime, m.size,
                       snippet(docs, 1, '>>>', '<<<', '…', 20)
                FROM docs
                JOIN meta m ON docs.rowid = m.id
                WHERE docs MATCH ?
                ORDER BY bm25(docs)
                LIMIT ?
                """,
                (query, limit),
            )
            return [
                {"path": r[0], "name": r[1], "mime": r[2], "size": r[3], "snippet": r[4]}
                for r in cur.fetchall()
            ]
        except sqlite3.OperationalError as e:
            log.error("FTS search error: %s", e)
            return []

    def close(self):
        self.db.close()

async def index_path(index: LocalIndex, path: Path, sha: str, mime: str, size: int):
    try:
        content = await asyncio.get_running_loop().run_in_executor(
            None, lambda: path.read_text(errors="ignore")
        )
        await index.add(path, content, sha, mime, size)
    except Exception:
        pass

# ──────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────
async def run_hunt(query: str, out_zip: str):
    print(_banner())
    log.info("query → %s", query)

    tor = TorManager()
    await tor.renew()

    hits = await multi_search(query, tor)

    candidates: Set[str] = set()

    async with await session_factory() as session:
        sem = asyncio.Semaphore(CONCURRENT_CRAWL)

        async def harvest(h: Hit):
            async with sem:
                found = await harvest_page(session, h, tor)
                candidates.update(found)

        await asyncio.gather(*(harvest(h) for h in hits[:50]))

        tg = await scrape_telegram(session, tor)
        candidates.update(tg)

        dc = await scrape_discord_mirrors(session, tor)
        candidates.update(dc)

    for fname, fcfg in FORUM_CONFIGS.items():
        async with await session_factory() as fsession:
            ok = await forum_login(fsession, fcfg, tor)
            if ok:
                links = await forum_crawl(fsession, fcfg, query, tor)
                candidates.update(links)
            else:
                log.warning("forum %s: login failed, skipping", fname)

    log.info("%d download candidates", len(candidates))

    tmp      = Path(tempfile.mkdtemp(prefix="paradox_apex_"))
    loot:    List[Loot] = []
    lock_budget          = asyncio.Lock()
    total_ref            = [0]

    async with await session_factory() as session:
        dl_sem = asyncio.Semaphore(CONCURRENT_DOWNLOADS)

        async def dl(url: str):
            async with dl_sem:
                item = await download_one(session, url, tmp, url, tor, lock_budget, total_ref)
                if item:
                    loot.append(item)
                    log.info("  + %-50s  (%s KB)", item.name[:50], item.size // 1024)

        await asyncio.gather(*(dl(u) for u in list(candidates)[:100]))

    if not loot:
        log.warning("nothing collected")
        shutil.rmtree(tmp, ignore_errors=True)
        return

    extract_root = tmp / "_extracted"
    extract_root.mkdir()
    db_path = str(tmp / "paradox_index.db")
    index   = LocalIndex(db_path)

    index_tasks = []
    for item in loot:
        mime, notes        = triage_file(item.path)
        item.mime          = mime
        item.triage_notes  = notes

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, try_unpack, item, extract_root)

        if item.path.suffix.lower() in TEXT_EXTENSIONS:
            index_tasks.append(index_path(index, item.path, item.sha256, item.mime, item.size))

        for p_str in item.unpacked:
            pp = Path(p_str)
            if pp.suffix.lower() in TEXT_EXTENSIONS:
                sha = await loop.run_in_executor(None, _sha256, pp)
                index_tasks.append(index_path(index, pp, sha, "extracted", pp.stat().st_size))

    await asyncio.gather(*index_tasks)
    index.close()

    log.info("packing %d files → %s", len(loot), out_zip)
    manifest_lines = [
        _manifest_header(),
        _built(),
        f"Query      : {query}",
        f"Created    : {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Files      : {len(loot)}",
        f"Total bytes: {total_ref[0]:,}",
        "",
        f"{'#':<4}  {'Name':<50}  {'Size':>10}  {'MIME':<22}  SHA256",
        "-" * 120,
    ]

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for i, item in enumerate(loot, 1):
            arc = f"loot/{i:03d}_{item.name}"
            zf.write(item.path, arc)
            manifest_lines.append(
                f"{i:<4}  {item.name:<50}  {item.size:>10,}  {item.mime:<22}  {item.sha256}"
            )
            manifest_lines.append(f"       source  : {item.url}")
            if item.triage_notes:
                manifest_lines.append(f"       triage  : {item.triage_notes}")
            if item.unpacked:
                manifest_lines.append(f"       unpacked: {len(item.unpacked)} files")
            manifest_lines.append("")

            for p_str in item.unpacked:
                pp = Path(p_str)
                arc_ex = f"extracted/{i:03d}_{item.name}/{pp.name}"
                try:
                    zf.write(pp, arc_ex)
                except Exception:
                    pass

        zf.writestr("MANIFEST.txt", "\n".join(manifest_lines))

        sources_json = json.dumps(
            [
                {
                    "index":   i,
                    "name":    x.name,
                    "url":     x.url,
                    "size":    x.size,
                    "sha256":  x.sha256,
                    "mime":    x.mime,
                    "triage":  x.triage_notes,
                    "unpacked": x.unpacked,
                    "source_page": x.source_page,
                }
                for i, x in enumerate(loot, 1)
            ],
            indent=2,
        )
        zf.writestr("sources.json", sources_json)

        idx = Path(db_path)
        if idx.exists():
            zf.write(idx, "paradox_index.db")

    shutil.rmtree(tmp, ignore_errors=True)
    log.info("done → %s", out_zip)
    log.info("FTS5 index included as paradox_index.db")
    log.info(
        'search later: python -c "from paradox_holmes import LocalIndex; '
        'idx=LocalIndex(\'paradox_index.db\'); print(idx.search(\'your term\'))"'
    )

# ──────────────────────────────────────────────
# INTERACTIVE SEARCH MODE
# ──────────────────────────────────────────────
def search_mode(db_path: str):
    idx = LocalIndex(db_path)
    print(_search_title())
    print(f"Database: {db_path}\n")
    while True:
        try:
            q = input("search> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        results = idx.search(q)
        if not results:
            print("  (no matches)\n")
            continue
        for r in results:
            print(f"  [{r['mime']}] {r['name']}  ({r['size']:,} bytes)")
            print(f"    {r['path']}")
            print(f"    … {r['snippet']} …\n")
    idx.close()

# ──────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description=_prod_ed(),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    hunt_p = sub.add_parser("hunt", help="Run a dark-web hunt")
    hunt_p.add_argument("query")
    hunt_p.add_argument("-o", "--output", default=None, help="Output zip path")

    srch_p = sub.add_parser("search", help="Search a local FTS5 index")
    srch_p.add_argument("db", help="Path to paradox_index.db")

    args = ap.parse_args()

    if args.cmd == "hunt":
        out = args.output or (
            f"paradox_apex_{re.sub(r'[^a-z0-9]+', '_', args.query.lower())[:35]}_{int(time.time())}.zip"
        )
        asyncio.run(run_hunt(args.query, out))

    elif args.cmd == "search":
        search_mode(args.db)
