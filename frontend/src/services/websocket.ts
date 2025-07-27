import { apiService } from './api';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface NotificationMessage extends WebSocketMessage {
  type: 'notification';
  data: {
    id: string;
    title: string;
    message: string;
    notification_type: string;
    created_at: string;
  };
}

export interface MessageUpdate extends WebSocketMessage {
  type: 'message';
  data: {
    conversation_id: string;
    message: {
      id: string;
      sender: string;
      content: string;
      timestamp: string;
    };
  };
}

export interface InterviewUpdate extends WebSocketMessage {
  type: 'interview_update';
  data: {
    session_id: string;
    status: string;
    feedback?: any;
  };
}

export interface JobMatchUpdate extends WebSocketMessage {
  type: 'job_match';
  data: {
    job_id: string;
    match_score: number;
    job_title: string;
    company: string;
  };
}

type WebSocketEventHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private connections: Map<string, WebSocket> = new Map();
  private eventHandlers: Map<string, WebSocketEventHandler[]> = new Map();
  private reconnectAttempts: Map<string, number> = new Map();
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second

  connect(endpoint: string): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      try {
        const token = apiService.getAuthToken();
        if (!token) {
          reject(new Error('No authentication token available'));
          return;
        }

        const wsUrl = `${import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'}/ws/${endpoint}/?token=${token}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log(`WebSocket connected: ${endpoint}`);
          this.connections.set(endpoint, ws);
          this.reconnectAttempts.set(endpoint, 0);
          resolve(ws);
        };

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(endpoint, message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error(`WebSocket error on ${endpoint}:`, error);
          reject(error);
        };

        ws.onclose = (event) => {
          console.log(`WebSocket disconnected: ${endpoint}`, event.code, event.reason);
          this.connections.delete(endpoint);
          
          // Attempt to reconnect if not a normal closure
          if (event.code !== 1000 && event.code !== 1001) {
            this.attemptReconnect(endpoint);
          }
        };

      } catch (error) {
        console.error(`Failed to create WebSocket connection to ${endpoint}:`, error);
        reject(error);
      }
    });
  }

  private attemptReconnect(endpoint: string) {
    const attempts = this.reconnectAttempts.get(endpoint) || 0;
    
    if (attempts < this.maxReconnectAttempts) {
      const delay = this.reconnectDelay * Math.pow(2, attempts); // Exponential backoff
      
      console.log(`Attempting to reconnect to ${endpoint} in ${delay}ms (attempt ${attempts + 1}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.reconnectAttempts.set(endpoint, attempts + 1);
        this.connect(endpoint).catch(error => {
          console.error(`Reconnection attempt ${attempts + 1} failed for ${endpoint}:`, error);
        });
      }, delay);
    } else {
      console.error(`Max reconnection attempts reached for ${endpoint}`);
      this.reconnectAttempts.delete(endpoint);
    }
  }

  private handleMessage(endpoint: string, message: WebSocketMessage) {
    const handlers = this.eventHandlers.get(endpoint) || [];
    handlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in WebSocket message handler:', error);
      }
    });

    // Global handlers for specific message types
    const globalHandlers = this.eventHandlers.get('*') || [];
    globalHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in global WebSocket message handler:', error);
      }
    });
  }

  addEventListener(endpoint: string, handler: WebSocketEventHandler) {
    if (!this.eventHandlers.has(endpoint)) {
      this.eventHandlers.set(endpoint, []);
    }
    this.eventHandlers.get(endpoint)!.push(handler);
  }

  removeEventListener(endpoint: string, handler: WebSocketEventHandler) {
    const handlers = this.eventHandlers.get(endpoint);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  send(endpoint: string, message: any) {
    const ws = this.connections.get(endpoint);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      console.warn(`WebSocket connection to ${endpoint} is not open`);
    }
  }

  disconnect(endpoint: string) {
    const ws = this.connections.get(endpoint);
    if (ws) {
      ws.close(1000, 'Client disconnect');
      this.connections.delete(endpoint);
      this.eventHandlers.delete(endpoint);
      this.reconnectAttempts.delete(endpoint);
    }
  }

  disconnectAll() {
    this.connections.forEach((ws, endpoint) => {
      ws.close(1000, 'Client disconnect all');
    });
    this.connections.clear();
    this.eventHandlers.clear();
    this.reconnectAttempts.clear();
  }

  isConnected(endpoint: string): boolean {
    const ws = this.connections.get(endpoint);
    return ws ? ws.readyState === WebSocket.OPEN : false;
  }

  // Convenience methods for common endpoints
  async connectNotifications(handler: WebSocketEventHandler): Promise<WebSocket> {
    this.addEventListener('notifications', handler);
    return this.connect('notifications');
  }

  async connectMessages(handler: WebSocketEventHandler): Promise<WebSocket> {
    this.addEventListener('messages', handler);
    return this.connect('messages');
  }

  async connectInterviews(handler: WebSocketEventHandler): Promise<WebSocket> {
    this.addEventListener('interviews', handler);
    return this.connect('interviews');
  }

  // Send typed messages
  sendNotificationAck(notificationId: string) {
    this.send('notifications', {
      type: 'notification_ack',
      notification_id: notificationId,
    });
  }

  sendMessageRead(conversationId: string, messageId: string) {
    this.send('messages', {
      type: 'message_read',
      conversation_id: conversationId,
      message_id: messageId,
    });
  }

  sendTypingIndicator(conversationId: string, isTyping: boolean) {
    this.send('messages', {
      type: 'typing_indicator',
      conversation_id: conversationId,
      is_typing: isTyping,
    });
  }

  sendInterviewResponse(sessionId: string, response: any) {
    this.send('interviews', {
      type: 'interview_response',
      session_id: sessionId,
      response: response,
    });
  }
}

// Create and export singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService;