import json
from typing import Optional

class RedisClient:
    def __init__(self):
        self._client = None
        self._enabled = False

    def init(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            import redis
            self._client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self._client.ping()
            self._enabled = True
        except (ImportError, Exception):
            self._enabled = False

    def get(self, key: str) -> Optional[str]:
        if not self._enabled:
            return None
        return self._client.get(key)

    def set(self, key: str, value: str, ttl: int = 60):
        if not self._enabled:
            return
        self._client.setex(key, ttl, value)

    def set_spot_status(self, spot_id: int, occupied: bool):
        self.set(f"spot:{spot_id}:occupied", json.dumps(occupied), ttl=300)

    def get_spot_status(self, spot_id: int) -> Optional[bool]:
        data = self.get(f"spot:{spot_id}:occupied")
        return json.loads(data) if data else None

    def set_spot_battery(self, spot_id: int, level: float):
        self.set(f"spot:{spot_id}:battery", json.dumps(level), ttl=3600)

    def get_spot_battery(self, spot_id: int) -> Optional[float]:
        data = self.get(f"spot:{spot_id}:battery")
        return json.loads(data) if data else None

    def invalidate_spot(self, spot_id: int):
        if not self._enabled:
            return
        self._client.delete(f"spot:{spot_id}:occupied", f"spot:{spot_id}:battery")


redis_cache = RedisClient()
