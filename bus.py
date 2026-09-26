# language: Python 3, file: bus.py
import asyncio, time
from collections import deque

class Bus:
    def __init__(self):
        self.stats = {
            "cycles": 0, "join": 0, "leave": 0,
            "errors": 0, "media_sessions": 0, "workers": 0,
        }
        self.running = False
        self.stop_event = asyncio.Event()
        self.params = {
            "jitter_ms": 80, "cycles": 0,
            "cooldown_sec": 3, "rtp_hold_sec": 8,
            "rejoin_race": True,
        }
        self.log = deque(maxlen=200)
        self.per_worker = {}
        self.timeline = deque(maxlen=120)

    def emit(self, kind, msg, worker=None):
        self.log.append((time.time(), kind, worker or "-", msg))

bus = Bus()
