import os
import json
from aiohttp import web, WSMsgType

clients = set()
buzz_order = []
scores = {}

routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
    return web.Response(text="Buzzin server running!")

@routes.get("/ws")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    clients.add(ws)

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)

                if data["type"] == "buzz":
                    if not any(player["name"] == data["name"] for player in buzz_order):
                        buzz_order.append({ "name": data["name"], "team": data["team"] })
                        scores.setdefault(data["name"], 0)

                elif data["type"] == "clear":
                    buzz_order.clear()

                elif data["type"] == "score":
                    scores[data["name"]] = scores.get(data["name"], 0) + int(data["delta"])

                message = json.dumps({"buzz_order": buzz_order, "scores": scores})
                for client in clients:
                    await client.send_str(message)

            except Exception as e:
                print(f"Error handling message: {e}")

        elif msg.type == WSMsgType.ERROR:
            print(f"WebSocket connection closed with exception: {ws.exception()}")

    clients.remove(ws)
    return ws

app = web.Application()
app.add_routes(routes)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port)
