from typing import List

from fastapi import WebSocket


class IConnectionManager:
    async def connect(self, websocket: WebSocket):
        raise NotImplementedError

    async def disconnect(self, websocket: WebSocket):
        raise NotImplementedError

    async def broadcast(self, message: dict):
        raise NotImplementedError


class ConnectionManager(IConnectionManager):
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


ws_manager = ConnectionManager()
