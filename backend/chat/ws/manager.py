from collections import defaultdict
from fastapi import WebSocket
import asyncio


class ConnectionManager:
    def __init__(self):
        # room_id -> set of (user_id, websocket)
        self._rooms: dict[int, dict[int, list[WebSocket]]] = defaultdict(lambda: defaultdict(list))
        self._lock = asyncio.Lock()

    async def connect(self, room_id: int, user_id: int, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._rooms[room_id][user_id].append(ws)

    async def disconnect(self, room_id: int, user_id: int, ws: WebSocket):
        async with self._lock:
            conns = self._rooms[room_id][user_id]
            if ws in conns:
                conns.remove(ws)
            if not conns:
                del self._rooms[room_id][user_id]
            if not self._rooms[room_id]:
                del self._rooms[room_id]

    async def broadcast(self, room_id: int, payload: dict, exclude_ws: WebSocket | None = None):
        dead: list[tuple[int, WebSocket]] = []
        for uid, conns in list(self._rooms.get(room_id, {}).items()):
            for ws in list(conns):
                if ws is exclude_ws:
                    continue
                try:
                    await ws.send_json(payload)
                except Exception:
                    dead.append((uid, ws))
        for uid, ws in dead:
            await self.disconnect(room_id, uid, ws)

    def online_users(self, room_id: int) -> list[int]:
        return list(self._rooms.get(room_id, {}).keys())


manager = ConnectionManager()
