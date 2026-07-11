from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from .. import db
from ..models import ReceiverIn, serialize

router = APIRouter(prefix="/receivers", tags=["receivers"])


def _oid(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid id")


@router.get("")
async def list_receivers():
    coll = db.get_db()["receivers"]
    docs = await coll.find().sort("name", 1).to_list(length=1000)
    return [serialize(d) for d in docs]


@router.post("")
async def create_receiver(body: ReceiverIn):
    coll = db.get_db()["receivers"]
    doc = body.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    res = await coll.insert_one(doc)
    doc["_id"] = res.inserted_id
    return serialize(doc)


@router.put("/{id}")
async def update_receiver(id: str, body: ReceiverIn):
    coll = db.get_db()["receivers"]
    res = await coll.find_one_and_update(
        {"_id": _oid(id)}, {"$set": body.model_dump()}, return_document=True
    )
    if not res:
        raise HTTPException(status_code=404, detail="Receiver not found")
    return serialize(res)


@router.delete("/{id}")
async def delete_receiver(id: str):
    coll = db.get_db()["receivers"]
    res = await coll.delete_one({"_id": _oid(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Receiver not found")
    return {"ok": True}
