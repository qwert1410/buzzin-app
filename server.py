# === server.py ===
# Backend using websockets to manage buzzers and teams

import asyncio
import websockets
import json
import os

clients = set()
buzz_order = []
players = {}  # socket: {"name": str, "team": str}
scores = {"A": 0, "B": 0}

async def notify_all():
    if clients:
        data = {
            "buzz_order": buzz_order,
            "scores": scores
        }
        message = json.dumps(data)
        await asyncio.gather(*(client.send(message) for client in clients))


async def handler(websocket):
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)

            if data["action"] == "join":
                players[websocket] = {"name": data["name"], "team": data["team"]}

            elif data["action"] == "buzz":
                if players[websocket]["name"] not in buzz_order:
                    buzz_order.append(players[websocket]["name"])

            elif data["action"] == "clear":
                buzz_order.clear()

            elif data["action"] == "add_point":
                scores[data["team"]] += 1

            elif data["action"] == "sub_point":
                scores[data["team"]] -= 1

            await notify_all()

    except websockets.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)
        if websocket in players:
            del players[websocket]


PORT = int(os.environ.get("PORT", 8000))

async def main():
    async with websockets.serve(handler, "", PORT):
        print(f"Server running on ws://0.0.0.0:{PORT}")
        await asyncio.Future()

asyncio.run(main())
