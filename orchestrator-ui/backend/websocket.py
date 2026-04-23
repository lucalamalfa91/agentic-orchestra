"""
WebSocket connection manager for real-time generation progress.
"""
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """
    Manages WebSocket connections grouped by generation_id.
    """

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, generation_id: str, websocket: WebSocket):
        await websocket.accept()
        if generation_id not in self.active_connections:
            self.active_connections[generation_id] = []
        self.active_connections[generation_id].append(websocket)
        conn_count = len(self.active_connections[generation_id])
        print(f"[WS] CONNECT    generation_id={generation_id} "
              f"total_connections={conn_count}")

    def disconnect(self, generation_id: str, websocket: WebSocket):
        if generation_id in self.active_connections:
            try:
                self.active_connections[generation_id].remove(websocket)
            except ValueError:
                pass
            remaining = len(self.active_connections[generation_id])
            print(f"[WS] DISCONNECT generation_id={generation_id} "
                  f"remaining_connections={remaining}")
            if remaining == 0:
                del self.active_connections[generation_id]
                print(f"[WS] CLEANUP    generation_id={generation_id} (no listeners)")

    async def broadcast(self, generation_id: str, message: dict):
        if generation_id not in self.active_connections:
            print(f"[WS] BROADCAST  generation_id={generation_id} "
                  f"WARNING: no active connections, message dropped: step={message.get('step')} "
                  f"pct={message.get('percentage')}")
            return

        payload = json.dumps(message)
        listeners = list(self.active_connections[generation_id])
        print(f"[WS] BROADCAST  generation_id={generation_id} "
              f"listeners={len(listeners)} "
              f"step={message.get('step')} "
              f"step_number={message.get('step_number')} "
              f"pct={message.get('percentage')} "
              f"msg={message.get('message', '')[:60]}")

        dead = []
        for ws in listeners:
            try:
                await ws.send_text(payload)
            except Exception as e:
                print(f"[WS] SEND_ERROR generation_id={generation_id} "
                      f"error={e}")
                dead.append(ws)

        for ws in dead:
            self.disconnect(generation_id, ws)

    async def broadcast_log(self, generation_id: str, step_number: int, text: str):
        """Broadcast a log_entry message for the expandable per-step log in the UI."""
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        await self.broadcast(generation_id, {
            "type": "log_entry",
            "step_number": step_number,
            "text": f"{ts}  {text}",
        })

    async def send_error(self, generation_id: str, error_message: str):
        print(f"[WS] ERROR      generation_id={generation_id} "
              f"error={error_message[:200]}")
        await self.broadcast(generation_id, {
            "type": "error",
            "step": "error",
            "step_number": 0,
            "percentage": 0,
            "message": f"Generation failed: {error_message}",
        })


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, generation_id: str):
    """
    FastAPI WebSocket endpoint handler.
    Keeps the connection alive until the client disconnects.
    """
    await manager.connect(generation_id, websocket)
    try:
        while True:
            # Keep-alive: just drain any incoming pings; we only push from server
            data = await asyncio.wait_for(websocket.receive_text(), timeout=300)
            print(f"[WS] RECV       generation_id={generation_id} data={data[:80]}")
    except asyncio.TimeoutError:
        print(f"[WS] TIMEOUT    generation_id={generation_id} (300s idle, closing)")
    except WebSocketDisconnect as e:
        print(f"[WS] CLIENT_DC  generation_id={generation_id} code={e.code}")
    except Exception as e:
        print(f"[WS] EXCEPTION  generation_id={generation_id} error={e}")
    finally:
        manager.disconnect(generation_id, websocket)
