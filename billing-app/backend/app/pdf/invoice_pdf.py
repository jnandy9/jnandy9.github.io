"""Pixel-exact reproduction of the MUKTA / Shivam Engineering tax invoice.

Every line, box and text anchor below was reverse-engineered from the original
`MUKTA 2.pdf` (US Letter, 612x792 pt). Coordinates are kept in the SAME
top-left origin as the source PDF; `_ty()` converts to ReportLab's bottom-left
origin so the numbers stay readable against the extraction.

Do NOT casually "tidy" these numbers — they are the format contract.
"""
from __future__ import annotations

import io
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ..models import compute_totals

PAGE_W, PAGE_H = letter  # 612 x 792

# ---- fonts -----------------------------------------------------------------
REG = "Helvetica"
BOLD = "Helvetica-Bold"
# The business name in the original uses a heavy decorative face. Drop a .ttf at
# app/pdf/fonts/title.ttf to match it exactly; otherwise we fall back to bold.
TITLE = BOLD
_font_dir = os.path.join(os.path.dirname(__file__), "fonts")
_title_ttf = os.path.join(_font_dir, "title.ttf")
if os.path.exists(_title_ttf):
    try:
        pdfmetrics.registerFont(TTFont("InvoiceTitle", _title_ttf))
        TITLE = "InvoiceTitle"
    except Exception:
        TITLE = BOLD


# ---- number / date helpers -------------------------------------------------
_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
         "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
         "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
         "Eighty", "Ninety"]


def num_to_words(num: float) -> str:
    num = int(round(num))
    if num == 0:
        return "Zero"

    def two(n):
        return _ONES[n] if n < 20 else _TENS[n // 10] + (" " + _ONES[n % 10] if n % 10 else "")

    def three(n):
        s = ""
        if n >= 100:
            s += _ONES[n // 100] + " Hundred "
            n %= 100
        if n:
            s += two(n)
        return s.strip()

    crore, num = divmod(num, 10000000)
    lakh, num = divmod(num, 100000)
    thousand, rest = divmod(num, 1000)
    parts = []
    if crore:
        parts.append(three(crore) + " Crore")
    if lakh:
        parts.append(three(lakh) + " Lakh")
    if thousand:
        parts.append(three(thousand) + " Thousand")
    if rest:
        parts.append(three(rest))
    return " ".join(parts)


def inr(n) -> str:
    """Indian-grouped money with 2 decimals, e.g. 60234 -> '60,234.00'."""
    n = round(float(n or 0) + 1e-9, 2)
    neg = n < 0
    n = abs(n)
    intp, dec = f"{n:.2f}".split(".")
    if len(intp) > 3:
        last3 = intp[-3:]
        rest = intp[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        intp = ",".join(groups) + "," + last3
    return ("-" if neg else "") + intp + "." + dec


def fmt_date(iso: str) -> str:
    if not iso or "-" not in iso:
        return iso or ""
    try:
        y, m, d = iso.split("-")
        return f"{d}-{m}-{y}"
    except ValueError:
        return iso


# ---- low-level drawing -----------------------------------------------------
def _ty(y: float) -> float:
    """Convert a top-left-origin y (source PDF space) to ReportLab y."""
    return PAGE_H - y


class _Pen:
    def __init__(self, c: canvas.Canvas):
        self.c = c

    def hline(self, y, x0, x1, w=0.8):
        self.c.setLineWidth(w)
        self.c.line(x0, _ty(y), x1, _ty(y))

    def vline(self, x, y0, y1, w=0.8):
        self.c.setLineWidth(w)
        self.c.line(x, _ty(y0), x, _ty(y1))

    def text(self, x, y_bottom, s, size=9, bold=False, font=None):
        if s is None or s == "":
            return
        self.c.setFont(font or (BOLD if bold else REG), size)
        self.c.drawString(x, _ty(y_bottom) + 2, str(s))

    def center(self, cx, y_bottom, s, size=9, bold=False, font=None):
        if not s:
            return
        self.c.setFont(font or (BOLD if bold else REG), size)
        self.c.drawCentredString(cx, _ty(y_bottom) + 2, str(s))

    def right(self, x_right, y_bottom, s, size=9, bold=False, font=None):
        if s is None or s == "":
            return
        self.c.setFont(font or (BOLD if bold else REG), size)
        self.c.drawRightString(x_right, _ty(y_bottom) + 2, str(s))

    def fit(self, x, y_bottom, s, size, max_w, bold=False):
        """Left-aligned text that shrinks its font until it fits max_w."""
        if s is None or s == "":
            return
        from reportlab.pdfbase.pdfmetrics import stringWidth
        font = BOLD if bold else REG
        while size > 5 and stringWidth(str(s), font, size) > max_w:
            size -= 0.5
        self.c.setFont(font, size)
        self.c.drawString(x, _ty(y_bottom) + 2, str(s))

    def center_fit(self, cx, y_bottom, s, size, max_w, bold=False):
        """Centred text that shrinks to fit max_w."""
        if not s:
            return
        from reportlab.pdfbase.pdfmetrics import stringWidth
        font = BOLD if bold else REG
        while size > 5 and stringWidth(str(s), font, size) > max_w:
            size -= 0.5
        self.c.setFont(font, size)
        self.c.drawCentredString(cx, _ty(y_bottom) + 2, str(s))

    def center_wrap(self, cx, y_bottom, s, size, max_w, line_h=10.0, max_lines=2, bold=False):
        """Centred text wrapped onto up to max_lines lines (last line shrinks to fit)."""
        if not s:
            return
        from reportlab.pdfbase.pdfmetrics import stringWidth
        font = BOLD if bold else REG
        words = str(s).split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if stringWidth(trial, font, size) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if len(lines) > max_lines:                       # merge overflow into last line
            lines = lines[:max_lines - 1] + [" ".join(lines[max_lines - 1:])]
        # vertically centre the block around y_bottom
        y0 = y_bottom - (len(lines) - 1) * line_h / 2
        for i, ln in enumerate(lines):
            self.center_fit(cx, y0 + i * line_h, ln, size, max_w, bold=bold)


# ---- the grid (exact coordinates from MUKTA 2.pdf) -------------------------
_VLINES = [
    (53.2, 72.2, 770.8),     # outer left frame
    (564.6, 39.2, 770.8),    # outer right frame
    (208.9, 183.9, 238.6),   # meta: label|value divider (left half)
    (337.9, 183.9, 584.5),   # centre divider = HSN|Qty divider
    (72.4, 340.1, 584.5),    # items: S.L.|Description
    (287.7, 340.1, 584.5),   # items: Description|HSN
    (436.9, 340.1, 770.8),   # items: Qty|Rate  +  bank|totals major divider
    (485.9, 340.1, 584.5),   # items: Rate|Amount
    (517.5, 38.4, 73.1),     # copy box left edge
    (517.5, 584.5, 665.5),   # totals: label|value divider
]
_HLINES = [
    (38.8, 518.4, 565.1),    # copy box top
    (50.8, 518.4, 565.1),
    (62.8, 518.4, 565.1),
    (72.6, 53.6, 565.1),     # main frame top
    (183.4, 53.6, 565.1),    # below seller header block
    (238.1, 53.6, 565.1),    # below meta grid
    (251.7, 53.6, 565.1),    # below parties header
    (339.7, 53.6, 565.1),    # above items header
    (367.0, 53.6, 565.1),    # below items header
    (584.1, 53.6, 565.1),    # bottom of items table
    (596.7, 53.6, 565.1),    # below bank/other-charges header
    (608.7, 53.6, 565.1),    # below PNB / TOTAL
    (622.2, 53.6, 565.1),    # below PNB a/c / SGST
    (638.4, 437.4, 565.0),   # right only: below CGST
    (652.5, 53.6, 565.1),    # below Canara a/c / IGST
    (665.1, 53.6, 565.1),    # below amount-in-words / grand total
    (742.8, 437.4, 565.0),   # right only: signature divider
    (770.4, 53.6, 565.1),    # bottom frame
]
_UNDERLINES = [
    (90.5, 264.4, 354.3),    # under "TAX INVOICE"
    (197.0, 108.5, 209.4),   # under invoice-no value
    (197.0, 242.2, 338.4),   # under date value
]

# column centres for the items table
_C_SL = (53.2 + 72.4) / 2
_C_DESC_X = 74.2            # description is left-aligned
_C_HSN = (287.7 + 337.9) / 2
_C_QTY = (337.9 + 436.9) / 2
_C_RATE = (436.9 + 485.9) / 2
_AMT_R = 562.8             # amount column right edge (right-aligned)

# party half centres
_C_RECV = (53.2 + 337.9) / 2
_C_CONS = (337.9 + 564.6) / 2

ROW_H = 13.53
FIRST_ROW_BASE = 406.6
N_ROWS = 14


def _sign_off(c, p, text, cx, cell_w, size=10):
    """Draw 'For <business>' centred, wrapped to two lines, shrinking the font so
    every word fits (never drop 'CONCERN')."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = text.split()

    def wrap(sz):
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if stringWidth(trial, BOLD, sz) <= cell_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    lines = wrap(size)
    while len(lines) > 2 and size > 6:
        size -= 0.5
        lines = wrap(size)
    ys = [755.5, 769.1] if len(lines) >= 2 else [762.0]
    for line, yy in zip(lines[:2], ys):
        p.center(cx, yy, line, size, bold=True)


def build_invoice_pdf(inv: dict, biz: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    p = _Pen(c)
    t = compute_totals(inv)

    banks = (biz.get("banks") or [])
    b0 = banks[0] if len(banks) > 0 else {}
    b1 = banks[1] if len(banks) > 1 else {}

    # ---- grid ----
    for y, x0, x1 in _HLINES:
        p.hline(y, x0, x1)
    for x, y0, y1 in _VLINES:
        p.vline(x, y0, y1)
    for y, x0, x1 in _UNDERLINES:
        p.hline(y, x0, x1, w=0.6)

    # ---- header ----
    p.text(395.4, 49.3, "Original for Receipient", 8)
    p.text(395.4, 61.3, "Duplicate for Transporter", 8)
    p.text(395.4, 72.2, "Triplicate for supplier", 8)
    p.center(309.4, 90.0, "TAX INVOICE", 17, bold=True)
    p.text(410.4, 105.5, f"Mobile  : {biz.get('mobile','')}", 10, bold=True)
    p.center(309.6, 132.0, biz.get("name", ""), 26, font=TITLE)
    p.center(309.0, 143.5, biz.get("tagline", ""), 10)
    p.center(309.0, 155.5, biz.get("specialist", ""), 10)
    p.center(309.0, 168.5, f"Office & Works : {biz.get('office','')}", 10, bold=True)
    p.center(309.0, 181.0,
             f"GSTN - {biz.get('gstin','')}  ●  PAN NO. - {biz.get('pan','')}",
             10, bold=True)

    # ---- meta grid ----
    # left sub-column A
    p.text(56.9, 195.6, "Invoice No.", 10)
    p.text(125.4, 195.6, inv.get("invoice_no", ""), 10)
    p.text(55.0, 209.2, "challan No.", 10)
    p.text(125.4, 209.2, inv.get("challan_no", ""), 10)
    p.text(55.0, 223.0, "Order No.", 10)
    p.text(125.4, 223.0, inv.get("order_no", ""), 10)
    p.text(55.0, 236.8, "state  :", 10)
    p.text(128.8, 236.8, biz.get("state", ""), 10, bold=True)
    # left sub-column B
    p.text(210.8, 196.1, "Date :", 10)
    p.text(266.7, 195.6, fmt_date(inv.get("date", "")), 10, bold=True)
    p.text(210.8, 209.7, "Date :", 10)
    p.text(266.7, 209.2, fmt_date(inv.get("date", "")), 10)
    p.text(210.8, 223.5, "Date :", 10)
    p.text(210.8, 236.8, "State code :", 10)
    p.text(308.1, 237.3, biz.get("state_code", ""), 10)
    # right half
    p.text(339.7, 196.1, "C.N./R.R. No  :", 10)
    p.text(339.7, 209.7, "Date :", 10)
    p.text(339.7, 223.5, "Mode of Transport :", 10)
    p.text(474.1, 223.0, inv.get("mode_of_transport", ""), 10)
    p.text(339.7, 237.3, "Through :", 10)
    p.text(390.0, 237.3, inv.get("through", ""), 10)

    # ---- parties ----
    p.center(195.5, 249.0, "Details of receiver (Billed to)", 10, bold=True)
    p.center(451.2, 249.0, "Details of consignee (shipped to)", 10, bold=True)

    def party_block(party, label_x, right_edge):
        # Values are centred in the area to the right of the labels (matching the
        # original). Long addresses wrap onto two lines instead of shrinking tiny.
        region_left = label_x + 58          # clear the widest label ("state code :")
        region_right = right_edge - 4
        cx = (region_left + region_right) / 2
        max_w = region_right - region_left
        p.text(label_x, 264.2, "Name :", 10)
        p.center_fit(cx, 264.2, party.get("name", ""), 10, max_w, bold=True)
        p.text(label_x, 283.2, "Address :", 10)
        p.center_wrap(cx, 279.0, party.get("address", ""), 9, max_w, line_h=10.0, max_lines=2)
        p.text(label_x, 301.9, "state :", 10)
        p.center_fit(cx, 301.9, party.get("state", ""), 10, max_w)
        p.text(label_x, 315.7, "state code :", 10)
        p.center_fit(cx, 315.7, party.get("state_code", ""), 10, max_w)
        p.text(label_x, 327.5, "GSTIN /", 9)
        p.text(label_x, 338.5, "Unique ID :", 9)
        p.center_fit(cx, 334.0, party.get("gstin", ""), 10, max_w)

    party_block(inv.get("buyer", {}), 55.0, 337.9)
    consignee = inv.get("buyer", {}) if inv.get("same_as_buyer") else inv.get("consignee", {})
    party_block(consignee, 339.7, 564.6)

    # ---- items header ----
    p.center(_C_SL, 350.6, "S.L.", 9, bold=True)
    p.center(_C_SL, 364.2, "NO", 9, bold=True)
    p.center((72.4 + 287.7) / 2, 358.9, "Description of Goods", 10, bold=True)
    p.center(_C_HSN, 350.6, "HSN /SA", 9, bold=True)
    p.center(_C_HSN, 364.2, "CODE", 9, bold=True)
    p.center(_C_QTY, 358.9, "Quantity(pcs)", 10, bold=True)
    p.center(_C_RATE, 359.4, "Rate ( /-)", 10, bold=True)
    p.center((485.9 + 564.6) / 2, 358.9, "Amount (Rs)", 10, bold=True)

    # ---- "Machining Charges Only" heading (machining bills only) ----
    if inv.get("bill_type") == "MACHINING":
        from reportlab.pdfbase.pdfmetrics import stringWidth
        heading = "Machining Charges Only"
        hcx = (72.4 + 287.7) / 2
        p.center(hcx, 385.0, heading, 11, bold=True)
        hw = stringWidth(heading, BOLD, 11)
        p.hline(388.0, hcx - hw / 2, hcx + hw / 2, w=0.7)   # underline

    # ---- items body (fixed 14 rows, empty rows show 0.00 like the original) ----
    items = inv.get("items", [])
    for i in range(N_ROWS):
        base = FIRST_ROW_BASE + i * ROW_H
        if i < len(items):
            it = items[i]
            qty = float(it.get("qty") or 0)
            rate = float(it.get("rate") or 0)
            amount = qty * rate
            p.center(_C_SL, base, str(i + 1), 10)
            p.fit(_C_DESC_X, base, it.get("description", ""), 10, 287.7 - _C_DESC_X - 3)
            p.center(_C_HSN, base, it.get("hsn", ""), 10)
            p.center(_C_QTY, base, ("%g" % qty) if qty else "", 10)
            p.center(_C_RATE, base, ("%g" % rate) if rate else "", 10)
            p.right(_AMT_R, base, inr(amount), 10)
        else:
            p.right(_AMT_R, base, "0.00", 10)

    # ---- bank details (left) ----
    p.text(55.0, 595.8, "Bank Details :", 10, bold=True)
    if b0:
        p.text(55.0, 607.7, b0.get("name", ""), 10, bold=True)
        p.text(55.0, 620.9, f"A/C- {b0.get('ac','')}     IFSC -{b0.get('ifsc','')}", 10, bold=True)
    if b1:
        p.text(55.0, 635.9, b1.get("name", ""), 10, bold=True)
        p.text(55.0, 650.9, f"A/C - {b1.get('ac','')}  IFSC- {b1.get('ifsc','')}", 10, bold=True)
    p.text(55.0, 664.2, "Amount in words :", 10, bold=True)
    # keep the words inside the left block (must not cross the totals divider at 436.9)
    p.fit(157.0, 664.2, f"Rupees {num_to_words(t['grand_total'])} Only", 10, 436.9 - 157.0 - 3, bold=True)

    # ---- declaration + terms (left) ----
    decl = biz.get("declaration", [])
    p.text(54.8, 677.1, "Ddeclaration :", 10, bold=True)
    if len(decl) > 0:
        p.text(54.8, 690.8, decl[0], 10)
    if len(decl) > 1:
        p.text(54.8, 703.7, decl[1], 10)
    p.text(54.8, 716.0, "Terms of sale :", 10, bold=True)
    terms = biz.get("terms", [])
    term_ys = [728.3, 741.4, 755.0, 768.5]
    for line, yy in zip(terms, term_ys):
        p.text(54.8, yy, line, 10)

    # ---- totals (right) ----
    p.text(438.7, 595.8, "Other Charges", 10, bold=True)
    if t["other"] > 0:
        p.right(_AMT_R, 595.8, inr(t["other"]), 10)
    p.text(438.7, 607.7, "TOTAL", 10, bold=True)
    p.right(_AMT_R, 607.7, inr(t["subtotal"]), 10)

    igst_mode = inv.get("tax_mode") == "IGST"
    p.text(438.7, 620.9, f"Add : SGST@ {('%g' % float(inv.get('sgst_pct',0)))}%", 10)
    p.right(_AMT_R, 620.9, inr(t["sgst"]) if not igst_mode else "0.00", 10)
    p.text(438.7, 635.8, f"Add : CGST@ {('%g' % float(inv.get('cgst_pct',0)))}%", 10)
    p.right(_AMT_R, 635.8, inr(t["cgst"]) if not igst_mode else "0.00", 10)
    igst_label = f"Add : IGST@ {('%g' % float(inv.get('igst_pct',0)))}%" if igst_mode else "Add : IGST@ "
    p.text(438.7, 650.9, igst_label, 10)
    if igst_mode:
        p.right(_AMT_R, 650.9, inr(t["igst"]), 10)
    p.text(438.7, 664.2, "GRAND TOTAL", 10, bold=True)
    p.right(_AMT_R, 664.2, inr(t["grand_total"]), 10, bold=True)

    # ---- signature (right) ----
    p.center(500.7, 677.8, "E. & O.E", 10, bold=True)
    _sign_off(c, p, f"For {biz.get('name','')}", cx=500.7, cell_w=120.0)

    c.showPage()
    c.save()
    return buf.getvalue()
