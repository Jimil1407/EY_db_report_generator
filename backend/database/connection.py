import oracledb
from fastapi import FastAPI
from .config import settings

class OracleConnectionPool:
    def __init__(self):
        self.pool = None

    async def init_pool(self):
        self.pool = oracledb.create_pool(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=f"{settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_DB_NAME}",
            min=5,
            max=20,
            increment=1,
            encoding="UTF-8",
            pool_timeout=60
        )

    async def get_connection(self):
        return await self.pool.acquire()

    async def close_pool(self):
        if self.pool:
            await self.pool.close()

# Dependency injection for FastAPI lifecycle
oracle_pool = OracleConnectionPool()

def init_db(app: FastAPI):
    @app.on_event("startup")
    async def startup_event():
        await oracle_pool.init_pool()

    @app.on_event("shutdown")
    async def shutdown_event():
        await oracle_pool.close_pool()
