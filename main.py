# language: Python 3, file: main.py
import asyncio, signal, yaml, uvicorn
from pool import load_sessions
from collapse import collapse_loop
from bus import bus
from panel import app

async def bot_task(cfg, clients):
    while not bus.running:
        await asyncio.sleep(0.5)
    bus.stats["workers"] = len(clients)
    await collapse_loop(cfg, clients, bus.stats, bus.stop_event)

async def panel_task():
    cfg = uvicorn.Config(app, host="127.0.0.1", port=8080, log_level="warning")
    await uvicorn.Server(cfg).serve()

async def main():
    cfg = yaml.safe_load(open("config.yaml"))
    clients = load_sessions(cfg)
    if not clients:
        raise SystemExit("sessions/ folder e .session file nai")
    signal.signal(signal.SIGINT, lambda *_: bus.stop_event.set())
    await asyncio.gather(panel_task(), bot_task(cfg, clients))

if __name__ == "__main__":
    asyncio.run(main())
