# language: Python 3, file: panel.py
import asyncio, json, time
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bus import bus

app = FastAPI(title="tg-call-crash panel")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/stats")
async def stats():
    return JSONResponse({
        "running": bus.running, "stats": bus.stats,
        "params": bus.params, "workers": bus.per_worker,
    })

@app.post("/api/start")
async def start():
    if bus.running: return {"ok": False, "msg": "already running"}
    bus.running = True; bus.stop_event.clear()
    bus.emit("ctl", "start requested")
    return {"ok": True}

@app.post("/api/stop")
async def stop():
    bus.running = False; bus.stop_event.set()
    bus.emit("ctl", "stop requested")
    return {"ok": True}

@app.post("/api/params")
async def set_params(req: Request):
    body = await req.json()
    for k in ("jitter_ms","cycles","cooldown_sec","rtp_hold_sec"):
        if k in body: bus.params[k] = int(body[k])
    if "rejoin_race" in body:
        bus.params["rejoin_race"] = bool(body["rejoin_race"])
    bus.emit("ctl", f"params {body}")
    return {"ok": True, "params": bus.params}

@app.get("/api/log")
async def log():
    return JSONResponse([
        {"ts": t, "kind": k, "worker": w, "msg": m}
        for (t, k, w, m) in bus.log
    ])

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = {
                "t": time.time(), "running": bus.running,
                "stats": bus.stats, "params": bus.params,
                "workers": bus.per_worker,
                "timeline": list(bus.timeline)[-60:],
                "log_tail": [
                    {"ts": t, "kind": k, "worker": w, "msg": m}
                    for (t, k, w, m) in list(bus.log)[-20:]
                ],
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
