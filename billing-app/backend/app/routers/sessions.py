from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import db

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionIn(BaseModel):
    name: str


@router.get("")
async def list_sessions():
    coll = db.get_db()["sessions"]
    docs = await coll.find().sort("name", -1).to_list(length=500)
    return [{"name": d["name"]} for d in docs]


@router.post("")
async def create_session(body: SessionIn):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Session name required")
    coll = db.get_db()["sessions"]
    await coll.update_one(
        {"name": name},
        {"$setOnInsert": {"name": name, "created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return {"name": name}


@router.delete("/{name}")
async def delete_session(name: str):
    coll = db.get_db()["sessions"]
    res = await coll.delete_one({"name": name})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}
