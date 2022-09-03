from typing import Any, Mapping
from sqlalchemy.sql import ClauseElement

import databases


class Database:
    def __init__(self, read_dsn: str, write_dsn: str) -> None:
        self.read_database = databases.Database(read_dsn)
        self.write_database = databases.Database(write_dsn)

    async def connect(self) -> None:
        await self.read_database.connect()
        await self.write_database.connect()

    async def disconnect(self) -> None:
        await self.read_database.disconnect()
        await self.write_database.disconnect()

    async def fetch_all(
        self,
        query: ClauseElement | str,
        values: dict | None = None,
    ) -> list[Mapping]:
        rows = await self.read_database.fetch_all(query, values)
        return [row._mapping for row in rows]

    async def fetch_one(
        self,
        query: ClauseElement | str,
        values: dict | None = None,
    ) -> Mapping:
        return (await self.read_database.fetch_one(query, values))._mapping

    async def fetch_val(
        self,
        query: ClauseElement | str,
        values: dict | None = None,
        column: Any = 0,
    ) -> Any:
        return await self.read_database.fetch_val(query, values, column)

    async def execute(
        self,
        query: ClauseElement | str,
        values: dict | None = None,
    ) -> Any:
        return await self.write_database.execute(query, values)
