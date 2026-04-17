import json
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

class MemoryManager:

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(settings.REDIS_URL)
            except Exception:
                self._redis = None
        return self._redis

    async def store_paper_knowledge(self, paper_id: str, text: str, paper_title: str = ""):
        try:
            from app.vector_store.faiss_store import get_vector_store
            store = get_vector_store()
            # Chunk the text so large papers don't create one giant embedding
            chunks = store.chunk_text(text)
            store.add_texts(chunks, paper_id=paper_id, paper_title=paper_title)
        except Exception as e:
            print(f"Warning: vector store: {e}")

    async def search_knowledge(self, query: str, top_k: int = 5) -> list:
        try:
            from app.vector_store.faiss_store import get_vector_store
            return get_vector_store().search(query, top_k=top_k)
        except Exception as e:
            print(f"Warning: search failed: {e}")
            return []

    async def get_history(self, session_id: str) -> list:
        try:
            r = await self._get_redis()
            if not r:
                return []
            data = await r.get(f"chat:{session_id}")
            return json.loads(data) if data else []
        except Exception:
            return []

    async def save_message(self, session_id: str, role: str, content: str):
        try:
            r = await self._get_redis()
            if not r:
                return
            history = await self.get_history(session_id)
            history.append({"role": role, "content": content})
            history = history[-20:]
            await r.setex(f"chat:{session_id}", 86400, json.dumps(history))
        except Exception as e:
            print(f"Warning: save message: {e}")

    async def set_task_status(self, task_id: str, status: dict):
        try:
            r = await self._get_redis()
            if r:
                await r.setex(f"task:{task_id}", 3600, json.dumps(status))
        except Exception:
            pass

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        try:
            r = await self._get_redis()
            if not r:
                return None
            data = await r.get(f"task:{task_id}")
            return json.loads(data) if data else None
        except Exception:
            return None
