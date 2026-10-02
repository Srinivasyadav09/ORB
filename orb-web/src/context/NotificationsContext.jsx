import { createContext, useCallback, useContext, useMemo, useState } from "react";
const NotificationsContext = createContext(null);
export function NotificationsProvider({ children }) {
  const [notifications, setNotifications] = useState([]);
  const notify = useCallback((message, type = "info") => { const notice = { id: `notice-${Date.now()}`, message, type, createdAt: new Date().toISOString(), read: false }; setNotifications(current => [notice, ...current]); return notice; }, []);
  const value = useMemo(() => ({ notifications, unreadCount: notifications.filter(item => !item.read).length, notify, markRead(id) { setNotifications(current => current.map(item => item.id === id ? { ...item, read: true } : item)); }, clearNotifications() { setNotifications([]); } }), [notifications, notify]);
  return <NotificationsContext.Provider value={value}>{children}</NotificationsContext.Provider>;
}
export function useNotifications() { const context = useContext(NotificationsContext); if (!context) throw new Error("useNotifications must be used within NotificationsProvider"); return context; }
