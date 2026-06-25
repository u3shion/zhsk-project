import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import JWTError
from sqlalchemy.orm import Session

from core.database import get_db
from auth.security import decode_token
from models.chat import Room, RoomMember, Message
from ws.manager import manager

router = APIRouter(tags=["websocket"])


def _authenticate_ws(token: str) -> dict | None:
    try:
        return decode_token(token)
    except JWTError:
        return None


def _is_member(room_id: int, user_id: int, db: Session) -> bool:
    return db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id,
    ).first() is not None


@router.websocket("/ws/rooms/{room_id}")
async def websocket_room(
    room_id: int,
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    payload = _authenticate_ws(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id: int = payload.get("user_id")
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if room is None:
        await websocket.close(code=4004, reason="Room not found")
        return

    if not _is_member(room_id, user_id, db):
        await websocket.close(code=4003, reason="Not a member")
        return

    await manager.connect(room_id, user_id, websocket)

    await manager.broadcast(room_id, {
        "type": "presence",
        "user_id": user_id,
        "event": "joined",
        "online": manager.online_users(room_id),
    })

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            msg_type = data.get("type")

            if msg_type == "message":
                content = (data.get("content") or "").strip()
                if not content:
                    await websocket.send_json({"type": "error", "detail": "Empty message"})
                    continue

                msg = Message(room_id=room_id, user_id=user_id, content=content)
                db.add(msg)
                db.commit()
                db.refresh(msg)

                await manager.broadcast(room_id, {
                    "type": "message",
                    "id": msg.id,
                    "room_id": room_id,
                    "user_id": user_id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                })

            elif msg_type == "delete":
                msg_id = data.get("message_id")
                if not msg_id:
                    await websocket.send_json({"type": "error", "detail": "message_id required"})
                    continue

                msg = db.query(Message).filter(
                    Message.id == msg_id,
                    Message.room_id == room_id,
                    Message.is_deleted == False,
                ).first()
                if not msg:
                    await websocket.send_json({"type": "error", "detail": "Message not found"})
                    continue
                if msg.user_id != user_id and payload.get("role") != "admin":
                    await websocket.send_json({"type": "error", "detail": "Forbidden"})
                    continue

                msg.is_deleted = True
                db.commit()

                await manager.broadcast(room_id, {
                    "type": "deleted",
                    "message_id": msg_id,
                    "room_id": room_id,
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({"type": "error", "detail": f"Unknown type: {msg_type}"})

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(room_id, user_id, websocket)
        await manager.broadcast(room_id, {
            "type": "presence",
            "user_id": user_id,
            "event": "left",
            "online": manager.online_users(room_id),
        })
        db.close()
