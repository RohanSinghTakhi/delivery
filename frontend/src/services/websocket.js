import { io } from 'socket.io-client';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

class WebSocketService {
  constructor() {
    this.socket = null;
  }

  connect(path, token, onConnect, onMessage, onError) {
    const url = `${BACKEND_URL}${path}`;
    
    this.socket = io(url, {
      transports: ['websocket'],
      query: { token },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      if (onConnect) onConnect();
    });

    this.socket.on('message', (data) => {
      if (onMessage) onMessage(data);
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    return this.socket;
  }

  send(event, data) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export default new WebSocketService();