"""
WebSocket manager for real-time progress updates.
"""
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    """

    def __init__(self):
        # Map generation_id to set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, generation_id: str):
        """Accept a new WebSocket connection for a generation."""
        await websocket.accept()
        if generation_id not in self.active_connections:
            self.active_connections[generation_id] = set()
        self.active_connections[generation_id].add(websocket)
        print(f"✅ WebSocket connected for generation: {generation_id}")

    def disconnect(self, websocket: WebSocket, generation_id: str):
        """Remove a WebSocket connection."""
        if generation_id in self.active_connections:
            self.active_connections[generation_id].discard(websocket)
            if not self.active_connections[generation_id]:
                del self.active_connections[generation_id]
        print(f"❌ WebSocket disconnected for generation: {generation_id}")

    async def broadcast(self, generation_id: str, message: dict):
        """
        Broadcast a message to all connections for a specific generation.
        """
        if generation_id not in self.active_connections:
            return

        # Send to all active connections
        disconnected = set()
        for connection in self.active_connections[generation_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"⚠️ Error sending message to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, generation_id)

    def get_connection_count(self, generation_id: str) -> int:
        """Get number of active connections for a generation."""
        if generation_id not in self.active_connections:
            return 0
        return len(self.active_connections[generation_id])


# Global connection manager instance
manager = ConnectionManager()
