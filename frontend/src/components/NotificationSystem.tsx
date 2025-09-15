import React, { useState, useEffect } from 'react';

interface Notification {
  id: string;
  type: 'info' | 'warning' | 'success' | 'emergency';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionRequired?: boolean;
}

interface NotificationSystemProps {
  isOpen: boolean;
  onClose: () => void;
}

const NotificationSystem: React.FC<NotificationSystemProps> = ({
  isOpen,
  onClose
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread' | 'emergency'>('all');

  useEffect(() => {
    // 실제로는 백엔드에서 가져올 데이터
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'emergency',
        title: '긴급 근무 변경',
        message: '김간호사님이 응급상황으로 인해 오늘 야간근무에서 제외되었습니다. 대체 인력이 필요합니다.',
        timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30분 전
        read: false,
        actionRequired: true
      },
      {
        id: '2',
        type: 'warning',
        title: '최소 인력 부족 경고',
        message: '12월 15일(금) 야간 교대에 최소 인력이 부족합니다. 추가 배정을 검토해주세요.',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2시간 전
        read: false,
        actionRequired: true
      },
      {
        id: '3',
        type: 'info',
        title: '휴가 승인 알림',
        message: '박간호사님의 12월 20-22일 연차휴가가 승인되었습니다.',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4시간 전
        read: true,
        actionRequired: false
      },
      {
        id: '4',
        type: 'success',
        title: '근무표 생성 완료',
        message: '2024년 12월 내과병동 근무표가 성공적으로 생성되었습니다.',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1일 전
        read: true,
        actionRequired: false
      },
      {
        id: '5',
        type: 'info',
        title: '교육 일정 안내',
        message: '간호사 보수교육이 12월 25일 오후 2시에 예정되어 있습니다.',
        timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3일 전
        read: false,
        actionRequired: false
      }
    ];

    setNotifications(mockNotifications);
  }, []);

  const getFilteredNotifications = () => {
    switch (filter) {
      case 'unread':
        return notifications.filter(n => !n.read);
      case 'emergency':
        return notifications.filter(n => n.type === 'emergency' || n.actionRequired);
      default:
        return notifications;
    }
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(n => ({ ...n, read: true }))
    );
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'emergency': return '🚨';
      case 'warning': return '⚠️';
      case 'success': return '✅';
      case 'info': return 'ℹ️';
      default: return '📢';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'emergency': return '#dc2626';
      case 'warning': return '#f59e0b';
      case 'success': return '#10b981';
      case 'info': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  const formatRelativeTime = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 60) {
      return `${minutes}분 전`;
    } else if (hours < 24) {
      return `${hours}시간 전`;
    } else {
      return `${days}일 전`;
    }
  };

  const filteredNotifications = getFilteredNotifications();
  const unreadCount = notifications.filter(n => !n.read).length;
  const emergencyCount = notifications.filter(n => n.type === 'emergency' || n.actionRequired).length;

  if (!isOpen) return null;

  return (
    <div className="notification-system">
      <div className="notification-backdrop" onClick={onClose}></div>
      <div className="notification-panel">
        <div className="notification-header">
          <div className="header-title">
            <h2>📢 알림</h2>
            <div className="notification-badges">
              {unreadCount > 0 && (
                <span className="badge unread-badge">{unreadCount}</span>
              )}
              {emergencyCount > 0 && (
                <span className="badge emergency-badge">{emergencyCount}</span>
              )}
            </div>
          </div>
          <div className="header-actions">
            <button
              className="mark-all-read-btn"
              onClick={markAllAsRead}
              disabled={unreadCount === 0}
            >
              모두 읽음
            </button>
            <button className="close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        <div className="notification-filters">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            전체 ({notifications.length})
          </button>
          <button
            className={`filter-btn ${filter === 'unread' ? 'active' : ''}`}
            onClick={() => setFilter('unread')}
          >
            안읽음 ({unreadCount})
          </button>
          <button
            className={`filter-btn ${filter === 'emergency' ? 'active' : ''}`}
            onClick={() => setFilter('emergency')}
          >
            중요 ({emergencyCount})
          </button>
        </div>

        <div className="notification-list">
          {filteredNotifications.length === 0 ? (
            <div className="empty-notifications">
              <div className="empty-icon">📭</div>
              <div className="empty-message">
                {filter === 'all'
                  ? '알림이 없습니다'
                  : filter === 'unread'
                  ? '읽지 않은 알림이 없습니다'
                  : '중요한 알림이 없습니다'
                }
              </div>
            </div>
          ) : (
            filteredNotifications.map(notification => (
              <div
                key={notification.id}
                className={`notification-item ${notification.read ? 'read' : 'unread'} ${notification.type}`}
                onClick={() => !notification.read && markAsRead(notification.id)}
              >
                <div className="notification-icon">
                  {getNotificationIcon(notification.type)}
                </div>

                <div className="notification-content">
                  <div className="notification-title-row">
                    <span className="notification-title">{notification.title}</span>
                    {notification.actionRequired && (
                      <span className="action-required-badge">조치 필요</span>
                    )}
                  </div>

                  <div className="notification-message">
                    {notification.message}
                  </div>

                  <div className="notification-meta">
                    <span className="notification-time">
                      {formatRelativeTime(notification.timestamp)}
                    </span>
                    {!notification.read && (
                      <span className="unread-indicator">●</span>
                    )}
                  </div>
                </div>

                <div className="notification-actions">
                  <button
                    className="delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteNotification(notification.id);
                    }}
                    title="삭제"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <style jsx>{`
        .notification-system {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
          display: flex;
          justify-content: flex-end;
          align-items: flex-start;
          padding-top: 60px;
        }

        .notification-backdrop {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
        }

        .notification-panel {
          width: 400px;
          max-height: 80vh;
          background: white;
          border-radius: 16px 0 0 16px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
          display: flex;
          flex-direction: column;
          position: relative;
          margin-right: 0;
        }

        .notification-header {
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .header-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .header-title h2 {
          margin: 0;
          font-size: 18px;
          color: #1f2937;
        }

        .notification-badges {
          display: flex;
          gap: 6px;
        }

        .badge {
          padding: 2px 6px;
          border-radius: 10px;
          font-size: 11px;
          font-weight: 600;
        }

        .unread-badge {
          background: #3b82f6;
          color: white;
        }

        .emergency-badge {
          background: #dc2626;
          color: white;
        }

        .header-actions {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .mark-all-read-btn {
          padding: 6px 12px;
          background: #f3f4f6;
          border: none;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
          color: #374151;
        }

        .mark-all-read-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .mark-all-read-btn:hover:not(:disabled) {
          background: #e5e7eb;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: #6b7280;
          padding: 4px;
        }

        .notification-filters {
          display: flex;
          padding: 16px 20px 0 20px;
          gap: 8px;
          border-bottom: 1px solid #f3f4f6;
        }

        .filter-btn {
          padding: 8px 12px;
          background: none;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
          color: #6b7280;
          transition: all 0.2s ease;
        }

        .filter-btn.active {
          background: #3b82f6;
          color: white;
          border-color: #3b82f6;
        }

        .filter-btn:hover:not(.active) {
          background: #f9fafb;
          border-color: #d1d5db;
        }

        .notification-list {
          flex: 1;
          overflow-y: auto;
          padding: 16px 0;
        }

        .empty-notifications {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px 20px;
          color: #6b7280;
        }

        .empty-icon {
          font-size: 48px;
          margin-bottom: 12px;
        }

        .empty-message {
          font-size: 14px;
        }

        .notification-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 16px 20px;
          border-bottom: 1px solid #f3f4f6;
          cursor: pointer;
          transition: background-color 0.2s ease;
        }

        .notification-item:hover {
          background: #f9fafb;
        }

        .notification-item.unread {
          background: #fefbff;
          border-left: 3px solid #3b82f6;
        }

        .notification-item.emergency {
          border-left-color: #dc2626;
        }

        .notification-item.warning {
          border-left-color: #f59e0b;
        }

        .notification-item.success {
          border-left-color: #10b981;
        }

        .notification-icon {
          font-size: 20px;
          margin-top: 2px;
        }

        .notification-content {
          flex: 1;
          min-width: 0;
        }

        .notification-title-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }

        .notification-title {
          font-weight: 600;
          color: #1f2937;
          font-size: 14px;
        }

        .action-required-badge {
          background: #fef3c7;
          color: #92400e;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 10px;
          font-weight: 600;
        }

        .notification-message {
          color: #4b5563;
          font-size: 13px;
          line-height: 1.4;
          margin-bottom: 8px;
        }

        .notification-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .notification-time {
          font-size: 11px;
          color: #9ca3af;
        }

        .unread-indicator {
          color: #3b82f6;
          font-size: 8px;
        }

        .notification-actions {
          display: flex;
          align-items: flex-start;
        }

        .delete-btn {
          background: none;
          border: none;
          cursor: pointer;
          opacity: 0;
          transition: opacity 0.2s ease;
          padding: 4px;
        }

        .notification-item:hover .delete-btn {
          opacity: 1;
        }

        @media (max-width: 768px) {
          .notification-panel {
            width: 100%;
            max-width: 100%;
            border-radius: 0;
            height: 100%;
            max-height: 100%;
          }

          .notification-system {
            padding-top: 0;
          }
        }
      `}</style>
    </div>
  );
};

export default NotificationSystem;