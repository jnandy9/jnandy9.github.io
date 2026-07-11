import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Response

from .. import db
from ..models import InvoiceIn, compute_totals, serialize
from ..pdf.invoice_pdf import build_invoice_pdf

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _oid(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid id")


async def _remember_receiver(buyer: dict):
    """Save/refresh the buyer so it can be reused for repeat billing."""
    if not buyer or not buyer.get("name"):
        return
    coll = db.get_db()["receivers"]
    key = {"name": buyer["name"].strip()}
    await coll.update_one(
        key,
        {"$set": {**buyer, "name": buyer["name"].strip()},
         "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


async def _remember_goods(items: list[dict]):
    coll = db.get_db()["goods"]
    for it in items:
        desc = (it.get("description") or "").strip()
        if not desc:
            continue
        await coll.update_one(
            {"description": desc},
            {"$set": {"description": desc, "hsn": it.get("hsn", ""), "rate": float(it.get("rate") or 0)},
             "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )


async def _remember_session(name: str):
    name = (name or "").strip()
    if not name:
        return
    await db.get_db()["sessions"].update_one(
        {"name": name},
        {"$setOnInsert": {"name": name, "created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


@router.get("")
async def list_invoices(session: str | None = None):
    coll = db.get_db()["invoices"]
    query = {"session": session} if session else {}
    docs = await coll.find(query).sort("created_at", -1).to_list(length=5000)
    out = []
    for d in docs:
        d = serialize(d)
        d["totals"] = compute_totals(d)
        out.append(d)
    return out


@router.post("")
async def create_invoice(body: InvoiceIn):
    coll = db.get_db()["invoices"]
    doc = body.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    res = await coll.insert_one(doc)
    doc["_id"] = res.inserted_id
    # remember buyer + goods + session for reuse / folder organisation
    await _remember_receiver(doc.get("buyer", {}))
    await _remember_goods(doc.get("items", []))
    await _remember_session(doc.get("session", ""))
    out = serialize(doc)
    out["totals"] = compute_totals(out)
    return out


@router.put("/{id}")
async def update_invoice(id: str, body: InvoiceIn):
    coll = db.get_db()["invoices"]
    doc = body.model_dump()
    res = await coll.find_one_and_update(
        {"_id": _oid(id)}, {"$set": doc}, return_document=True
    )
    if not res:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await _remember_receiver(doc.get("buyer", {}))
    await _remember_goods(doc.get("items", []))
    await _remember_session(doc.get("session", ""))
    out = serialize(res)
    out["totals"] = compute_totals(out)
    return out


@router.get("/{id}")
async def get_invoice(id: str):
    coll = db.get_db()["invoices"]
    doc = await coll.find_one({"_id": _oid(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")
    out = serialize(doc)
    out["totals"] = compute_totals(out)
    return out


@router.delete("/{id}")
async def delete_invoice(id: str):
    coll = db.get_db()["invoices"]
    res = await coll.delete_one({"_id": _oid(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"ok": True}


@router.get("/{id}/pdf")
async def invoice_pdf(id: str):
    doc = await db.get_db()["invoices"].find_one({"_id": _oid(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")
    biz = await db.get_db()["settings"].find_one({"_id": "business"}) or {}
    pdf_bytes = build_invoice_pdf(serialize(doc), biz)
    # filename: "<buyer company> <bill serial>.pdf"  e.g. "NANDY WORKS 02.pdf"
    buyer = ((doc.get("buyer") or {}).get("name") or "Invoice").strip()
    serial = (doc.get("invoice_no") or "invoice").split("/")[0].strip()
    safe = re.sub(r'[\\/:*?"<>|\r\n]+', "", f"{buyer} {serial}").strip() or "Invoice"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe}.pdf"'},
    )
