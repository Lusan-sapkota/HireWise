import { useState, useEffect, useCallback } from "react";
import { apiService, Notification } from "../services/api";
import { webSocketService, NotificationMessage } from "../services/websocket";

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  deleteNotification: (id: string) => Promise<void>;
  loadMore: () => Promise<void>;
  refresh: () => Promise<void>;
}

export const useNotifications = (): UseNotificationsReturn => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);

  // Load initial notifications
  const loadNotifications = useCallback(async (pageNum = 1, append = false) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiService.getNotifications({
        page: pageNum,
        page_size: 20,
      });

      const newNotifications = response.data.results;

      if (append) {
        setNotifications((prev) => [...prev, ...newNotifications]);
      } else {
        setNotifications(newNotifications);
      }

      setHasMore(!!response.data.next);
      setPage(pageNum);

      // Update unread count
      const unreadResponse = await apiService.getNotifications({
        is_read: false,
        page_size: 1,
      });
      setUnreadCount(unreadResponse.data.count);
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to load notifications");
      console.error("Failed to load notifications:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle real-time notification updates
  const handleWebSocketMessage = useCallback((message: NotificationMessage) => {
    if (message.type === "notification") {
      const newNotification: Notification = {
        id: message.data.id,
        user: "current-user", // This would come from auth context
        title: message.data.title,
        message: message.data.message,
        notification_type: message.data.notification_type,
        is_read: false,
        created_at: message.data.created_at,
      };

      setNotifications((prev) => [newNotification, ...prev]);
      setUnreadCount((prev) => prev + 1);

      // Show browser notification if permission granted
      if (Notification.permission === "granted") {
        new Notification(newNotification.title, {
          body: newNotification.message,
          icon: "/logo192.png",
          tag: newNotification.id,
        });
      }

      // Acknowledge receipt
      webSocketService.sendNotificationAck(message.data.id);
    }
  }, []);

  // Initialize notifications and WebSocket connection
  useEffect(() => {
    loadNotifications();

    // Request notification permission
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }

    // Connect to WebSocket for real-time updates
    webSocketService
      .connectNotifications(handleWebSocketMessage)
      .catch((error) => {
        console.error("Failed to connect to notifications WebSocket:", error);
      });

    return () => {
      webSocketService.disconnect("notifications");
    };
  }, [loadNotifications, handleWebSocketMessage]);

  const markAsRead = useCallback(async (id: string) => {
    try {
      await apiService.markNotificationAsRead(id);

      setNotifications((prev) =>
        prev.map((notification) =>
          notification.id === id
            ? { ...notification, is_read: true }
            : notification
        )
      );

      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err: any) {
      console.error("Failed to mark notification as read:", err);
      throw err;
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await apiService.markAllNotificationsAsRead();

      setNotifications((prev) =>
        prev.map((notification) => ({ ...notification, is_read: true }))
      );

      setUnreadCount(0);
    } catch (err: any) {
      console.error("Failed to mark all notifications as read:", err);
      throw err;
    }
  }, []);

  const deleteNotification = useCallback(
    async (id: string) => {
      try {
        // TODO: Add delete notification API endpoint
        // await apiService.deleteNotification(id);

        const notification = notifications.find((n) => n.id === id);

        setNotifications((prev) => prev.filter((n) => n.id !== id));

        if (notification && !notification.is_read) {
          setUnreadCount((prev) => Math.max(0, prev - 1));
        }
      } catch (err: any) {
        console.error("Failed to delete notification:", err);
        throw err;
      }
    },
    [notifications]
  );

  const loadMore = useCallback(async () => {
    if (!hasMore || isLoading) return;

    await loadNotifications(page + 1, true);
  }, [hasMore, isLoading, page, loadNotifications]);

  const refresh = useCallback(async () => {
    await loadNotifications(1, false);
  }, [loadNotifications]);

  return {
    notifications,
    unreadCount,
    isLoading,
    error,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    loadMore,
    refresh,
  };
};
