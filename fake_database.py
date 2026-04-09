import asyncio

class Database:
    def __init__(self):
        self._data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            "messages": [
                {"id": 1, "text": "Hello World"},
            ],
        }

    @classmethod
    async def connect(cls):
        await asyncio.sleep(0.1)  # Simulate async connection delay
        return cls()

    async def disconnect(self):
        await asyncio.sleep(0.1)  # Simulate closing connection

    def query(self, table: str = "users") -> list:
        return self._data.get(table, [])
