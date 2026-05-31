import logging

from app.config import settings

logger = logging.getLogger(__name__)

_neo4j_warned = False


class Neo4jManager:
    """Neo4j driver wrapper with graceful degradation.

    When Neo4j is unavailable, all methods return None and callers
    should skip graph-enrichment steps. Impact: job matching proceeds
    without knowledge-graph profiles (pure RAG + algorithmic scoring),
    and the /job-graph API returns an error to the frontend.
    """

    def __init__(self):
        self._driver = None

    @property
    def driver(self):
        global _neo4j_warned
        if self._driver is None:
            try:
                from neo4j import AsyncGraphDatabase
                self._driver = AsyncGraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
            except Exception as e:
                if not _neo4j_warned:
                    logger.warning(
                        f"[Neo4j] Driver init failed — graph enrichment disabled. "
                        f"Job matching will use RAG+scoring only (no graph profiles). "
                        f"Error: {e}"
                    )
                    _neo4j_warned = True
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
        global _neo4j_warned
        d = self.driver
        if d is None:
            return None
        try:
            return d.session()
        except Exception as e:
            if not _neo4j_warned:
                logger.warning(
                    f"[Neo4j] Session creation failed — graph features unavailable. "
                    f"Error: {e}"
                )
                _neo4j_warned = True
            return None


neo4j_manager = Neo4jManager()
