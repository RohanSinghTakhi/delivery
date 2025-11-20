from typing import Dict, Set, Optional
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    WebSocket connection manager with room support
    
    In-memory implementation for MVP. For production scaling,
    replace with Redis pub/sub adapter.
    
    Redis migration guide:
    1. Install: redis, aioredis
    2. Replace active_connections with Redis pub/sub
    3. Use Redis channels for rooms
    4. Broadcast via Redis publish
    """
    
    def __init__(self):
        # Store connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store rooms (e.g., order_123, vendor_456)
        self.rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, user_id: str):
        """Remove connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            # Remove from all rooms
            for room_users in self.rooms.values():
                room_users.discard(user_id)
            logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)
    
    def join_room(self, room: str, user_id: str):
        """Add user to a room"""
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(user_id)
        logger.info(f"User {user_id} joined room {room}")
    
    def leave_room(self, room: str, user_id: str):
        """Remove user from a room"""
        if room in self.rooms:
            self.rooms[room].discard(user_id)
            if not self.rooms[room]:
                del self.rooms[room]
            logger.info(f"User {user_id} left room {room}")
    
    async def broadcast_to_room(self, room: str, message: dict):
        """Broadcast message to all users in a room"""
        if room not in self.rooms:
            return
        
        disconnected_users = []
        for user_id in self.rooms[room]:
            if user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {user_id} in room {room}: {e}")
                    disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    async def broadcast_all(self, message: dict):
        """Broadcast message to all connected users"""
        disconnected_users = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)

# Global manager instance
manager = ConnectionManager()

# Redis adapter example (for future scaling):
"""
import aioredis

class RedisConnectionManager(ConnectionManager):
    def __init__(self, redis_url: str):
        super().__init__()
        self.redis = await aioredis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
    
    async def broadcast_to_room(self, room: str, message: dict):
        # Publish to Redis channel
        await self.redis.publish(f"room:{room}", json.dumps(message))
    
    async def listen_redis(self):
        # Subscribe to channels and forward to WebSocket
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                room = message['channel'].decode().split(':')[1]
                # Send to local connections in this room
                await super().broadcast_to_room(room, data)
"""