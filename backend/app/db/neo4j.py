from neo4j import AsyncGraphDatabase
from app.config import settings


class Neo4jManager:
    def __init__(self):
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
        return self._driver

    async def close(self):
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def get_session(self):
        return self.driver.session()


neo4j_manager = Neo4jManager()
