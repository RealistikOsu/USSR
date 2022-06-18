from __future__ import annotations

from starlette.endpoints import WebSocketEndpoint

from config import config


class ScoreFeed(WebSocketEndpoint):
    encoding = "json"
    websockets = set()

    async def on_connect(self, websocket):
        await websocket.accept()
        self.websockets.add(websocket)

    async def on_receive(self, websocket, data):
        if data["type"] == "write" and data["write_key"] == config.WS_WRITE_KEY:
            for _websocket in filter(lambda c: c != websocket, self.websockets):
                await _websocket.send_json(data["data"])
            await websocket.close()

    async def on_disconnect(self, websocket, close_code):
        self.websockets.remove(websocket)
