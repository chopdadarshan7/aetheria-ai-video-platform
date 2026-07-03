import json
import logging
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket
import redis.asyncio as aioredis
from ..config import settings

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps client_id/username/user_id to a set of active websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Background task for Redis Pub/Sub listener
        self.pubsub_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
        logger.info(f"WebSocket client connected: {client_id}. Active connections: {len(self.active_connections[client_id])}")

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_to_client(self, client_id: str, message: dict):
        """Send message safely to all open sockets for a specific client."""
        if client_id not in self.active_connections:
            return
            
        closed_sockets = set()
        for websocket in self.active_connections[client_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message to client {client_id}: {e}")
                closed_sockets.add(websocket)
                
        # Clean up stale/closed connections
        for stale in closed_sockets:
            self.active_connections[client_id].discard(stale)
        if client_id in self.active_connections and not self.active_connections[client_id]:
            del self.active_connections[client_id]

    async def start_pubsub_listener(self):
        """Start background loop listening to Redis channel and forwarding to clients."""
        logger.info("Initializing Redis Pub/Sub WebSocket listener task...")
        redis_client = aioredis.from_url(settings.broker_url)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("render_progress")
        
        try:
            while True:
                # Read message with short timeout to prevent blocking thread pool
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    payload_data = message.get("data")
                    if payload_data:
                        try:
                            # Payload keys: user_id, job_id, progress, status, error, result_url, thumb_url, gif_url
                            payload = json.loads(payload_data.decode("utf-8"))
                            user_id = str(payload.get("user_id"))
                            
                            # Forward message to user socket
                            if user_id:
                                await self.send_to_client(user_id, payload)
                        except Exception as parse_err:
                            logger.error(f"Error parsing PubSub message package: {parse_err}")
                await asyncio.sleep(0.1) # yield control to asyncio event loop
        except asyncio.CancelledError:
            logger.info("Redis Pub/Sub WebSocket listener task was cancelled.")
        except Exception as e:
            logger.exception(f"Unexpected error in Redis Pub/Sub listener loop: {e}")
        finally:
            await pubsub.unsubscribe("render_progress")
            await redis_client.close()

# Global connection manager instance
ws_manager = ConnectionManager()
