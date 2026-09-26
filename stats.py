# language: Python 3, file: stats.py
import asyncio
from rich.console import Console
from rich.table import Table

console = Console()

async def reporter(stats, stop, every=2):
    while not stop.is_set():
        await asyncio.sleep(every)
        t = Table(title="tg-call-crash")
        t.add_column("metric"); t.add_column("value", justify="right")
        for k in ("cycles","join","leave","errors","media_sessions","workers"):
            t.add_row(k, str(stats.get(k, 0)))
        console.clear(); console.print(t)
