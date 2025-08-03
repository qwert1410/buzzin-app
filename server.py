import asyncio
import json
import os
from aiohttp import web
import websockets
from websockets import WebSocketServerProtocol

clients = set()
buzz_order = []
scores = {}

async def notify_all():
    if clients:
        message = json.dumps({"buzz_order": buzz_order, "scores": scores})
        await asyncio.gather(*(client.send(message) for client in clients))

async def ws_handler(ws: WebSocketServerProtocol):
    clients.add(ws)
    try:
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "buzz":
                if data["name"] not in buzz_order:
                    buzz_order.append(data["name"])
                    scores.setdefault(data["name"], 0)
            elif data["type"] == "clear":
                buzz_order.clear()
            elif data["type"] == "score":
                scores[data["name"]] = scores.get(data["name"], 0) + int(data["delta"])
            await notify_all()
    finally:
        clients.remove(ws)

async def http_handler(request):
    return web.Response(text="Buzzin WebSocket server is up.")

async def start_servers():
    port = int(os.environ.get("PORT", 8000))

    # Start WebSocket server
    await websockets.serve(ws_handler, "0.0.0.0", port)

    # HTTP server for health checks
    app = web.Application()
    app.router.add_get("/", http_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port + 1)
    await site.start()

    await asyncio.Future()

asyncio.run(start_servers())
