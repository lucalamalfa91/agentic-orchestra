"""
WebSocket manager for real-time progress updates.
Includes a per-generation message buffer so messages sent before
the client connects are not lost (race condition fix).
"""
from collections import deque
from typing import Dict, Set, Deque
from fastapi import WebSocket

# Max messages buffered per generation while waiting for client to connect
_BUFFER_MAX = 100


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    Buffers up to _BUFFER_MAX messages per generation so that progress
    events emitted before the frontend connects are not silently dropped.
    """

    def __init__(self):
        # Map generation_id -> set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map generation_id -> deque of buffered messages (sent before client arrives)
        self._buffers: Dict[str, Deque[dict]] = {}

    async def connect(self, websocket: WebSocket, generation_id: str):
        """Accept a new WebSocket connection and flush any buffered messages."""
        await websocket.accept()
        if generation_id not in self.active_connections:
            self.active_connections[generation_id] = set()
        self.active_connections[generation_id].add(websocket)
        print(f"[OK] WebSocket connected for generation: {generation_id}")

        # Flush buffered messages that arrived before this client connected
        if generation_id in self._buffers:
            buffered = self._buffers.pop(generation_id)
            print(f"[WS] Flushing {len(buffered)} buffered messages to new client")
            for msg in buffered:
                try:
                    await websocket.send_json(msg)
                except Exception as e:
                    print(f"[WARN] Error flushing buffered message: {e}")
                    break

    def disconnect(self, websocket: WebSocket, generation_id: str):
        """Remove a WebSocket connection."""
        if generation_id in self.active_connections:
            self.active_connections[generation_id].discard(websocket)
            if not self.active_connections[generation_id]:
                del self.active_connections[generation_id]
        print(f"[DISCONNECTED] WebSocket disconnected for generation: {generation_id}")

    async def broadcast(self, generation_id: str, message: dict):
        """
        Broadcast a message to all connections for a specific generation.
        If no client is connected yet, buffer the message for later delivery.
        """
        if generation_id not in self.active_connections:
            # No client connected yet — buffer the message
            if generation_id not in self._buffers:
                self._buffers[generation_id] = deque(maxlen=_BUFFER_MAX)
            self._buffers[generation_id].append(message)
            print(f"[WS] Buffered message (no client yet): type={message.get('type')} step={message.get('step')}")
            return

        # Send to all active connections
        disconnected = set()
        for connection in self.active_connections[generation_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WARN] Error sending message to WebSocket: {e}")
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
