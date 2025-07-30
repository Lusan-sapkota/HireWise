// Service for recruiter-specific notifications (new applications, candidate status, etc.)
import { webSocketService, WebSocketMessage } from './websocket';

export type RecruiterNotificationType = 'new_application' | 'candidate_status' | 'ai_score' | 'interview_feedback';

export interface RecruiterNotification {
  id: string;
  title: string;
  message: string;
  type: RecruiterNotificationType;
  created_at: string;
  data?: any;
}

export function subscribeRecruiterNotifications(onMessage: (msg: RecruiterNotification) => void) {
  webSocketService.connect('recruiter_notifications').then(ws => {
    webSocketService.addEventListener('recruiter_notifications', (msg: WebSocketMessage) => {
      if (msg.type === 'notification') {
        onMessage(msg.data as RecruiterNotification);
      }
    });
  });
}
