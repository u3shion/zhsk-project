from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from auth.dependencies import get_current_user, TokenData
from models.chat import Room, RoomMember, Message
from rooms.schemas import RoomCreate, RoomInvite, RoomResponse, RoomMemberResponse, MessageResponse

router = APIRouter(prefix="/rooms", tags=["rooms"])


def _get_room_or_404(room_id: int, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


def _require_member(room: Room, user_id: int):
    is_member = any(m.user_id == user_id for m in room.members)
    if not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a room member")


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    body: RoomCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    room = Room(name=body.name, description=body.description, created_by=current_user.user_id)
    db.add(room)
    db.flush()
    member = RoomMember(room_id=room.id, user_id=current_user.user_id)
    db.add(member)
    db.commit()
    db.refresh(room)
    return room


@router.get("/", response_model=list[RoomResponse])
def list_my_rooms(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    memberships = db.query(RoomMember).filter(RoomMember.user_id == current_user.user_id).all()
    room_ids = [m.room_id for m in memberships]
    return db.query(Room).filter(Room.id.in_(room_ids), Room.is_active == True).all()


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    room = _get_room_or_404(room_id, db)
    _require_member(room, current_user.user_id)
    return room


@router.post("/{room_id}/invite", status_code=status.HTTP_201_CREATED)
def invite_user(
    room_id: int,
    body: RoomInvite,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    room = _get_room_or_404(room_id, db)
    _require_member(room, current_user.user_id)
    already = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == body.user_id,
    ).first()
    if already:
        raise HTTPException(status_code=400, detail="User already a member")
    db.add(RoomMember(room_id=room_id, user_id=body.user_id))
    db.commit()
    return {"message": "invited", "user_id": body.user_id}


@router.delete("/{room_id}/leave", status_code=status.HTTP_200_OK)
def leave_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    room = _get_room_or_404(room_id, db)
    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=400, detail="Not a member")
    db.delete(member)
    db.commit()
    return {"message": "left", "room_id": room_id}


@router.get("/{room_id}/members", response_model=list[RoomMemberResponse])
def get_members(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    room = _get_room_or_404(room_id, db)
    _require_member(room, current_user.user_id)
    return room.members


@router.get("/{room_id}/messages", response_model=list[MessageResponse])
def get_messages(
    room_id: int,
    limit: int = 50,
    before_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    room = _get_room_or_404(room_id, db)
    _require_member(room, current_user.user_id)
    q = db.query(Message).filter(Message.room_id == room_id, Message.is_deleted == False)
    if before_id:
        q = q.filter(Message.id < before_id)
    return q.order_by(Message.id.desc()).limit(limit).all()
