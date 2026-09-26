# language: Python 3, file: rtp_hold.py
import asyncio, json, time

async def open_srtp_session(transport_json: dict):
    class _Session:
        def __init__(self): self.closed = False
        async def close(self): self.closed = True
    return _Session()

def extract_transport(res):
    for u in res.updates:
        params = getattr(u, "params", None)
        if params and getattr(params, "data", None):
            try:
                return json.loads(params.data)
            except Exception:
                pass
    return None
