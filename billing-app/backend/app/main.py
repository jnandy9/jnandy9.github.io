from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .config import settings
from .models import BusinessSettings, BankAccount
from .routers import settings as settings_router
from .routers import receivers, goods, invoices, sessions


async def seed_business():
    """Ensure the single Shivam Engineering business profile exists."""
    coll = db.get_db()["settings"]
    existing = await coll.find_one({"_id": "business"})
    if existing:
        return
    doc = BusinessSettings(
        banks=[
            BankAccount(name="PUNJAB NATIONAL BANK- Barabazar branch,Kolkata",
                        ac="0096208700000116", ifsc="PUNB0009620"),
            BankAccount(name="CANARA BANK - ShyamBazar Branch , Kolkata",
                        ac="125003181403", ifsc="CNRB0019506"),
        ]
    ).model_dump()
    doc["_id"] = "business"
    await coll.insert_one(doc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await seed_business()
    yield
    await db.close()


app = FastAPI(title="Shivam Engineering Billing API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # Also allow any localhost/127.0.0.1 port (Vite may pick 5173, 5174, ...) so
    # local dev works regardless of the exact port it binds to.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings_router.router)
app.include_router(receivers.router)
app.include_router(goods.router)
app.include_router(sessions.router)
app.include_router(invoices.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
