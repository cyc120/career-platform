from app.config import settings


class Neo4jManager:
    def __init__(self):
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            try:
                from neo4j import AsyncGraphDatabase
                self._driver = AsyncGraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
            except Exception:
                return None
        return self._driver

    async def close(self):
        if self._driver:
            try:
                await self._driver.close()
            except Exception:
                pass
            self._driver = None

    async def get_session(self):
        d = self.driver
        if d is None:
            return None
        try:
            return d.session()
        except Exception:
            return None


neo4j_manager = Neo4jManager()
