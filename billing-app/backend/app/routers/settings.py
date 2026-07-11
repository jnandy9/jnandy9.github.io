from fastapi import APIRouter

from .. import db
from ..models import BusinessSettings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings():
    coll = db.get_db()["settings"]
    doc = await coll.find_one({"_id": "business"})
    if not doc:
        doc = BusinessSettings().model_dump()
        doc["_id"] = "business"
        await coll.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("")
async def update_settings(body: BusinessSettings):
    coll = db.get_db()["settings"]
    doc = body.model_dump()
    await coll.update_one({"_id": "business"}, {"$set": doc}, upsert=True)
    return doc
