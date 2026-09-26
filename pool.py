# language: Python 3, file: pool.py
import os, random, socks, yaml
from telethon import TelegramClient

def load_proxies(path):
    if not os.path.exists(path): return []
    with open(path) as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]

def proxy_tuple(url):
    if not url: return None
    scheme, rest = url.split("://", 1)
    if "@" in rest:
        creds, host = rest.split("@", 1)
        user, pw = creds.split(":", 1)
    else:
        user, pw, host = None, None, rest
    ip, port = host.split(":")
    kind = socks.SOCKS5 if scheme.startswith("socks5") else socks.HTTP
    return (kind, ip, int(port), True, user, pw)

def load_sessions(cfg):
    api_id, api_hash = cfg["api_id"], cfg["api_hash"]
    proxies = load_proxies(cfg["proxy_file"])
    out = []
    for fn in os.listdir(cfg["session_dir"]):
        if not fn.endswith(".session"): continue
        name = os.path.join(cfg["session_dir"], fn[:-8])
        px = proxy_tuple(random.choice(proxies)) if proxies else None
        c = TelegramClient(name, api_id, api_hash, proxy=px)
        c._session_name = fn[:-8]
        out.append(c)
    return out
