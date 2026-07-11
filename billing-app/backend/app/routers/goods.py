from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from .. import db
from ..models import GoodIn, serialize

router = APIRouter(prefix="/goods", tags=["goods"])


def _oid(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid id")


@router.get("")
async def list_goods():
    coll = db.get_db()["goods"]
    docs = await coll.find().sort("description", 1).to_list(length=2000)
    return [serialize(d) for d in docs]


@router.post("")
async def create_good(body: GoodIn):
    coll = db.get_db()["goods"]
    doc = body.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    res = await coll.insert_one(doc)
    doc["_id"] = res.inserted_id
    return serialize(doc)


@router.put("/{id}")
async def update_good(id: str, body: GoodIn):
    coll = db.get_db()["goods"]
    res = await coll.find_one_and_update(
        {"_id": _oid(id)}, {"$set": body.model_dump()}, return_document=True
    )
    if not res:
        raise HTTPException(status_code=404, detail="Item not found")
    return serialize(res)


@router.delete("/{id}")
async def delete_good(id: str):
    coll = db.get_db()["goods"]
    res = await coll.delete_one({"_id": _oid(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}
