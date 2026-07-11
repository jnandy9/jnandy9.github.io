from motor.motor_asyncio import AsyncIOMotorClient

from .config import settings

client: AsyncIOMotorClient | None = None


def get_db():
    """Return the active database handle. Call connect() at startup first."""
    assert client is not None, "Mongo client not initialised"
    return client[settings.mongodb_db]


async def connect():
    global client
    client = AsyncIOMotorClient(settings.mongodb_uri)
    # Fail fast if the URI/credentials are wrong.
    await client.admin.command("ping")


async def close():
    global client
    if client is not None:
        client.close()
        client = None
