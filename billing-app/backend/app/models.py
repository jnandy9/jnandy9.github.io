"""Pydantic schemas for the billing app.

MongoDB stores documents with an ObjectId `_id`. We expose it to the frontend
as a string field `id`. Helper `serialize()` converts a raw Mongo document.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


def serialize(doc: dict) -> dict:
    """Turn a raw Mongo doc into a JSON-friendly dict (ObjectId -> str id)."""
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


# ---------- Business profile (the single seller: Shivam Engineering) ----------
class BankAccount(BaseModel):
    name: str = ""          # e.g. "PUNJAB NATIONAL BANK- Barabazar branch,Kolkata"
    ac: str = ""            # account number
    ifsc: str = ""


class BusinessSettings(BaseModel):
    name: str = "SHIVAM ENGINEERING CONCERN"
    tagline: str = "Mechanical Engineers, Manufacturer, Fabricators & General Order suppliers"
    specialist: str = "Specialist in : All kinds of C.I.,C.S. & Graded Plummer Block (Bearing Housing)"
    office: str = "BALITIKURI BAMUNPARA, (SETH PARA), HOWRAH - 711 113"
    gstin: str = "19AFGPN7417M1ZV"
    pan: str = "AFGPN7417M"
    mobile: str = "9830200701"
    state: str = "WEST BENGAL"
    state_code: str = "19"
    banks: list[BankAccount] = Field(default_factory=list)
    terms: list[str] = Field(
        default_factory=lambda: [
            "1. Goods once sold will not be taken back or exchanged.",
            "2. Seller is not responsible for any loss or damaged goods in transit.",
            "3. Buyer undertakes to submit prescribted ST Dceleration to sender on demand.",
            "Disputes if any will be subject to seller court jurisdiction.",
        ]
    )
    declaration: list[str] = Field(
        default_factory=lambda: [
            "We declare that this invoice shows the actual price of goods.",
            "described and that all particulars are true and correct.",
        ]
    )


# ---------- Receiver (buyer / consignee) saved for repeat billing ----------
class Party(BaseModel):
    name: str = ""
    address: str = ""
    state: str = "WEST BENGAL"
    state_code: str = "19"
    gstin: str = ""


class ReceiverIn(Party):
    """A saved customer. Same shape as Party plus an optional label."""
    pass


class Receiver(ReceiverIn):
    id: str
    created_at: Optional[datetime] = None


# ---------- Goods catalogue (saved items for reuse) ----------
class GoodIn(BaseModel):
    hsn: str = ""
    description: str = ""
    rate: float = 0.0


class Good(GoodIn):
    id: str
    created_at: Optional[datetime] = None


# ---------- Invoice ----------
class InvoiceItem(BaseModel):
    hsn: str = ""
    description: str = ""
    qty: float = 0.0
    rate: float = 0.0


class InvoiceIn(BaseModel):
    invoice_no: str
    session: str = ""                   # financial year folder, e.g. "2026-27"
    challan_no: str = ""
    order_no: str = ""
    date: str = ""                      # ISO yyyy-mm-dd
    cnrr_no: str = ""
    mode_of_transport: str = ""
    through: str = ""
    # NORMAL -> goods (HSN 84833); MACHINING -> machining charges only (SAC 998931)
    bill_type: Literal["NORMAL", "MACHINING"] = "NORMAL"
    buyer: Party
    consignee: Party
    same_as_buyer: bool = True
    items: list[InvoiceItem] = Field(default_factory=list)
    tax_mode: Literal["SGST_CGST", "IGST"] = "SGST_CGST"
    sgst_pct: float = 9.0
    cgst_pct: float = 9.0
    igst_pct: float = 18.0
    other_charges: float = 0.0


class Invoice(InvoiceIn):
    id: str
    created_at: Optional[datetime] = None


# ---------- Computed totals (shared by API + PDF) ----------
def compute_totals(inv: dict) -> dict:
    items = inv.get("items", [])
    subtotal = sum((float(i.get("qty") or 0) * float(i.get("rate") or 0)) for i in items)
    other = float(inv.get("other_charges") or 0)
    sgst = cgst = igst = 0.0
    if inv.get("tax_mode") == "IGST":
        igst = subtotal * float(inv.get("igst_pct") or 0) / 100
    else:
        sgst = subtotal * float(inv.get("sgst_pct") or 0) / 100
        cgst = subtotal * float(inv.get("cgst_pct") or 0) / 100
    grand = subtotal + other + sgst + cgst + igst
    return {
        "subtotal": subtotal,
        "other": other,
        "sgst": sgst,
        "cgst": cgst,
        "igst": igst,
        "grand_total": grand,
    }
