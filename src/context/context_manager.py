# src/context/context_manager.py

import threading
import time
import asyncio
from typing import Dict, Any, Callable, List, Optional
from src.config.config import settings

# Conditional import for Redis
if settings.get("USE_REDIS_CACHING", False):
    try:
        import redis
    except ImportError:
        raise ImportError("Redis caching is enabled but the 'redis' package is not installed.")

def recursive_update(original: dict, updates: dict) -> dict:
    """
    Recursively update the original dictionary with values from updates.
    """
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(original.get(key), dict):
            original[key] = recursive_update(original.get(key, {}), value)
        else:
            original[key] = value
    return original

class ContextManager:
    """
    ContextManager provides shared context management functions for the multi-agent system.

    Optional Features (controlled via Dynaconf settings):
      - Redis based caching (USE_REDIS_CACHING)
      - Time-Based Expiration (TIME_BASED_EXPIRATION, SESSION_EXPIRATION_SECONDS)
      - Garbage Collection (GARBAGE_COLLECTION)
      - Asynchronous Operations (ASYNC_OPERATIONS)
      - Event Emission (EVENT_EMISSION)
    """

    def __init__(self):
        # Load settings from centralized configuration
        self.use_redis = settings.get("USE_REDIS_CACHING", False)
        self.expiration_enabled = settings.get("TIME_BASED_EXPIRATION", False)
        self.session_expiration = settings.get("SESSION_EXPIRATION_SECONDS", 3600)
        self.garbage_collection_enabled = settings.get("GARBAGE_COLLECTION", False)
        self.async_enabled = settings.get("ASYNC_OPERATIONS", False)
        self.event_emission_enabled = settings.get("EVENT_EMISSION", False)

        # Set up event listeners (callbacks)
        self._event_listeners: List[Callable[[str, str, Any], None]] = []

        if self.use_redis:
            redis_url = settings.get("REDIS_URL", "redis://localhost:6379/0")
            try:
                self.redis_client = redis.Redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
            except (redis.ConnectionError, redis.ResponseError) as e:
                raise ConnectionError(f"Failed to connect to Redis at {redis_url}: {str(e)}")
        else:
            # In-memory store: Each session maps to a dict that includes a special key "_timestamp"
            self._context_store: Dict[str, Dict[str, Any]] = {}
            self._lock = threading.Lock()

        # Start garbage collection if enabled (only for in-memory)
        if self.garbage_collection_enabled and not self.use_redis:
            self._start_garbage_collection()

    def _emit_event(self, session_id: str, event_type: str, data: Any) -> None:
        """
        Emit an event if event emission is enabled.
        """
        if self.event_emission_enabled:
            for callback in self._event_listeners:
                try:
                    callback(session_id, event_type, data)
                except Exception as e:
                    print(f"Error in event listener: {e}")

    def add_event_listener(self, callback: Callable[[str, str, Any], None]) -> None:
        """
        Register an event listener callback.
        The callback will be called with (session_id, event_type, data) on events.
        """
        self._event_listeners.append(callback)

    def create_session(self, session_id: str) -> None:
        """
        Create a new context session.
        """
        if self.use_redis:
            # For Redis, we simply ensure a key exists; use a Redis hash.
            if not self.redis_client.exists(session_id):
                self.redis_client.hset(session_id, mapping={"_timestamp": time.time()})
                print(f"Redis session '{session_id}' created.")
        else:
            with self._lock:
                if session_id not in self._context_store:
                    self._context_store[session_id] = {"_timestamp": time.time()}
                    print(f"Session '{session_id}' created.")
                else:
                    print(f"Session '{session_id}' already exists.")
        self._emit_event(session_id, "create_session", None)

    def set_context(self, session_id: str, key: str, value: Any) -> None:
        """
        Set or update a context variable for a specific session.
        """
        if self.use_redis:
            # Use Redis HSET to update the field
            self.redis_client.hset(session_id, key, value)
            self.redis_client.hset(session_id, "_timestamp", time.time())
        else:
            with self._lock:
                if session_id not in self._context_store:
                    self._context_store[session_id] = {"_timestamp": time.time()}
                self._context_store[session_id][key] = value
                # Update timestamp on modification
                self._context_store[session_id]["_timestamp"] = time.time()
        print(f"Context updated for session '{session_id}': {key} = {value}")
        self._emit_event(session_id, "set_context", {key: value})

    def update_partial_context(self, session_id: str, partial_context: Dict[str, Any]) -> None:
        """
        Update specific parts of the context without replacing the entire structure.
        Performs a recursive update.
        """
        if self.use_redis:
            # For Redis, retrieve the current context, update it, and save back.
            current = self.get_context(session_id)
            updated = recursive_update(current, partial_context)
            for key, value in updated.items():
                self.redis_client.hset(session_id, key, value)
            self.redis_client.hset(session_id, "_timestamp", time.time())
        else:
            with self._lock:
                if session_id not in self._context_store:
                    self._context_store[session_id] = {"_timestamp": time.time()}
                recursive_update(self._context_store[session_id], partial_context)
                self._context_store[session_id]["_timestamp"] = time.time()
        print(f"Partial context updated for session '{session_id}': {partial_context}")
        self._emit_event(session_id, "update_partial", partial_context)

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve the entire context for a given session.
        """
        if self.use_redis:
            data = self.redis_client.hgetall(session_id)
            # Decode bytes to strings and attempt to convert numeric values
            context = {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}
            return context
        else:
            with self._lock:
                return self._context_store.get(session_id, {}).copy()

    def delete_context(self, session_id: str) -> None:
        """
        Delete the context for a specific session.
        """
        if self.use_redis:
            self.redis_client.delete(session_id)
        else:
            with self._lock:
                if session_id in self._context_store:
                    del self._context_store[session_id]
                    print(f"Context for session '{session_id}' deleted.")
                else:
                    print(f"Session '{session_id}' does not exist.")
        self._emit_event(session_id, "delete_context", None)

    def _start_garbage_collection(self) -> None:
        """
        Start a background thread to remove expired sessions.
        Only applicable for in-memory storage.
        """
        def gc_worker():
            while True:
                time.sleep(10)  # Run every 10 seconds
                now = time.time()
                with self._lock:
                    expired_sessions = [
                        session_id for session_id, context in self._context_store.items()
                        if now - context.get("_timestamp", now) > self.session_expiration
                    ]
                    for session_id in expired_sessions:
                        del self._context_store[session_id]
                        print(f"Garbage collected session: {session_id}")
                        self._emit_event(session_id, "garbage_collected", None)

        gc_thread = threading.Thread(target=gc_worker, daemon=True)
        gc_thread.start()

    # Asynchronous versions if ASYNC_OPERATIONS is enabled
    async def async_create_session(self, session_id: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.create_session, session_id)

    async def async_set_context(self, session_id: str, key: str, value: Any) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.set_context, session_id, key, value)

    async def async_get_context(self, session_id: str) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_context, session_id)

    async def async_delete_context(self, session_id: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.delete_context, session_id)

    async def async_update_partial_context(self, session_id: str, partial_context: Dict[str, Any]) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.update_partial_context, session_id, partial_context)


# Example usage for testing purposes:
if __name__ == "__main__":
    cm = ContextManager()

    session = "session_001"
    cm.create_session(session)
    cm.set_context(session, "user_query", "How do I book a flight?")
    cm.set_context(session, "agent", "chat_agent")

    print("Initial Context:", cm.get_context(session))

    partial_update = {"intent": "booking", "details": {"class": "economy", "flexible": True}}
    cm.update_partial_context(session, partial_update)

    print("After Partial Update:", cm.get_context(session))

    # Simulate asynchronous usage if desired:
    if cm.async_enabled:
        async def async_demo():
            await cm.async_set_context(session, "async_key", "async_value")
            ctx = await cm.async_get_context(session)
            print("Async Context:", ctx)

        asyncio.run(async_demo())

    # Wait a moment to see garbage collection in action (if expiration is set low for testing)
    time.sleep(2)
    cm.delete_context(session)
    print("Final Context:", cm.get_context(session))