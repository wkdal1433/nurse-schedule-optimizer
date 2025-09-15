import React, { useState, useEffect } from 'react';

interface Nurse {
  id: number;
  name: string;
  role: 'head_nurse' | 'staff_nurse' | 'new_nurse';
  employment_type: 'full_time' | 'part_time';
  experience_level: number;
}

interface PersonalSchedule {
  date: string;
  shift: 'DAY' | 'EVENING' | 'NIGHT' | 'OFF';
  location?: string;
  notes?: string;
}

interface PersonalScheduleViewProps {
  nurse: Nurse;
  scheduleData: any[];
  selectedDate: Date;
  onClose: () => void;
}

const PersonalScheduleView: React.FC<PersonalScheduleViewProps> = ({
  nurse,
  scheduleData,
  selectedDate,
  onClose
}) => {
  const [personalSchedule, setPersonalSchedule] = useState<PersonalSchedule[]>([]);
  const [viewMode, setViewMode] = useState<'month' | 'week'>('month');
  const [showNotifications, setShowNotifications] = useState(true);

  useEffect(() => {
    // scheduleData에서 해당 간호사의 개인 스케줄 추출
    const extractPersonalSchedule = () => {
      const personal: PersonalSchedule[] = [];

      scheduleData.forEach(dayData => {
        const nurseAssignment = dayData.nurses[nurse.id];
        if (nurseAssignment) {
          personal.push({
            date: dayData.date,
            shift: nurseAssignment.shift,
            location: '병동 A', // 기본값
            notes: ''
          });
        }
      });

      setPersonalSchedule(personal);
    };

    extractPersonalSchedule();
  }, [scheduleData, nurse.id]);

  const getShiftColor = (shift: string) => {
    switch (shift) {
      case 'DAY': return '#3b82f6';
      case 'EVENING': return '#f59e0b';
      case 'NIGHT': return '#6366f1';
      case 'OFF': return '#6b7280';
      default: return '#9ca3af';
    }
  };

  const getShiftIcon = (shift: string) => {
    switch (shift) {
      case 'DAY': return '🌅';
      case 'EVENING': return '🌆';
      case 'NIGHT': return '🌙';
      case 'OFF': return '😴';
      default: return '❓';
    }
  };

  const getShiftName = (shift: string) => {
    switch (shift) {
      case 'DAY': return '주간';
      case 'EVENING': return '오후';
      case 'NIGHT': return '야간';
      case 'OFF': return '휴무';
      default: return '미정';
    }
  };

  const getWorkingHours = (shift: string) => {
    switch (shift) {
      case 'DAY': return '08:00 - 16:00';
      case 'EVENING': return '16:00 - 24:00';
      case 'NIGHT': return '00:00 - 08:00';
      case 'OFF': return '휴무';
      default: return '';
    }
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();

    const days: Date[] = [];
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }
    return days;
  };

  const getDaysInWeek = (date: Date) => {
    const startOfWeek = new Date(date);
    const day = startOfWeek.getDay();
    const diff = startOfWeek.getDate() - day;
    startOfWeek.setDate(diff);

    const days: Date[] = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      days.push(day);
    }
    return days;
  };

  const days = viewMode === 'month' ? getDaysInMonth(selectedDate) : getDaysInWeek(selectedDate);

  const getScheduleForDate = (date: Date): PersonalSchedule | null => {
    const dateKey = date.toISOString().split('T')[0];
    return personalSchedule.find(s => s.date === dateKey) || null;
  };

  const calculateWorkStats = () => {
    const thisMonth = personalSchedule.filter(s => {
      const scheduleDate = new Date(s.date);
      return scheduleDate.getMonth() === selectedDate.getMonth() &&
             scheduleDate.getFullYear() === selectedDate.getFullYear();
    });

    const dayShifts = thisMonth.filter(s => s.shift === 'DAY').length;
    const eveningShifts = thisMonth.filter(s => s.shift === 'EVENING').length;
    const nightShifts = thisMonth.filter(s => s.shift === 'NIGHT').length;
    const offDays = thisMonth.filter(s => s.shift === 'OFF').length;

    return { dayShifts, eveningShifts, nightShifts, offDays, total: thisMonth.length };
  };

  const workStats = calculateWorkStats();

  const handleExportPersonalSchedule = () => {
    // PDF 내보내기 로직 (향후 구현)
    alert('개인 스케줄 PDF 내보내기 기능은 향후 구현 예정입니다.');
  };

  const handleShareKakaoTalk = () => {
    // 카카오톡 공유 로직 (향후 구현)
    alert('카카오톡 공유 기능은 향후 구현 예정입니다.');
  };

  return (
    <div className="personal-schedule-modal">
      <div className="modal-backdrop" onClick={onClose}></div>
      <div className="modal-content">
        <div className="modal-header">
          <div className="nurse-info">
            <div className="nurse-avatar">
              {nurse.name.charAt(0)}
            </div>
            <div className="nurse-details">
              <h2>{nurse.name}님의 개인 스케줄</h2>
              <p>{nurse.role} • {nurse.employment_type} • 경력 {nurse.experience_level}년</p>
            </div>
          </div>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="schedule-controls">
          <div className="view-mode-toggle">
            <button
              className={viewMode === 'month' ? 'active' : ''}
              onClick={() => setViewMode('month')}
            >
              월간뷰
            </button>
            <button
              className={viewMode === 'week' ? 'active' : ''}
              onClick={() => setViewMode('week')}
            >
              주간뷰
            </button>
          </div>

          <div className="action-buttons">
            <button className="export-btn" onClick={handleExportPersonalSchedule}>
              📄 PDF 내보내기
            </button>
            <button className="share-btn" onClick={handleShareKakaoTalk}>
              💬 카톡 공유
            </button>
          </div>
        </div>

        <div className="work-stats">
          <div className="stat-item">
            <span className="stat-label">이번 달 근무일</span>
            <span className="stat-value">{workStats.total}일</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">주간 {workStats.dayShifts}일</span>
            <span className="stat-label">오후 {workStats.eveningShifts}일</span>
            <span className="stat-label">야간 {workStats.nightShifts}일</span>
            <span className="stat-label">휴무 {workStats.offDays}일</span>
          </div>
        </div>

        <div className={`schedule-calendar ${viewMode}`}>
          {days.map(date => {
            const schedule = getScheduleForDate(date);
            const isToday = date.toDateString() === new Date().toDateString();
            const isCurrentMonth = date.getMonth() === selectedDate.getMonth();

            return (
              <div
                key={date.toISOString()}
                className={`calendar-day ${isToday ? 'today' : ''} ${!isCurrentMonth ? 'other-month' : ''}`}
              >
                <div className="day-header">
                  <span className="day-number">{date.getDate()}</span>
                  <span className="day-name">
                    {['일', '월', '화', '수', '목', '금', '토'][date.getDay()]}
                  </span>
                </div>

                {schedule ? (
                  <div
                    className="schedule-item"
                    style={{ backgroundColor: getShiftColor(schedule.shift) }}
                  >
                    <div className="shift-info">
                      <span className="shift-icon">{getShiftIcon(schedule.shift)}</span>
                      <span className="shift-name">{getShiftName(schedule.shift)}</span>
                    </div>
                    <div className="shift-time">{getWorkingHours(schedule.shift)}</div>
                    {schedule.location && (
                      <div className="shift-location">{schedule.location}</div>
                    )}
                  </div>
                ) : (
                  <div className="no-schedule">
                    <span>미배정</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {showNotifications && (
          <div className="notifications-section">
            <div className="section-header">
              <h3>📢 알림</h3>
              <button
                className="toggle-notifications"
                onClick={() => setShowNotifications(!showNotifications)}
              >
                {showNotifications ? '숨기기' : '보기'}
              </button>
            </div>
            <div className="notifications-list">
              <div className="notification-item important">
                <span className="notification-icon">⚠️</span>
                <div className="notification-content">
                  <div className="notification-title">다음 주 야간근무 예정</div>
                  <div className="notification-desc">12월 15일(금) 야간근무가 배정되었습니다.</div>
                </div>
              </div>
              <div className="notification-item">
                <span className="notification-icon">📅</span>
                <div className="notification-content">
                  <div className="notification-title">휴가 신청 알림</div>
                  <div className="notification-desc">12월 연차 휴가 신청 기간이 곧 마감됩니다.</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .personal-schedule-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
          display: flex;
          justify-content: center;
          align-items: center;
        }

        .modal-backdrop {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
        }

        .modal-content {
          background: white;
          border-radius: 16px;
          width: 90%;
          max-width: 900px;
          max-height: 90vh;
          overflow-y: auto;
          position: relative;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 24px;
          border-bottom: 1px solid #e5e7eb;
        }

        .nurse-info {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .nurse-avatar {
          width: 50px;
          height: 50px;
          border-radius: 50%;
          background: linear-gradient(135deg, #3b82f6, #6366f1);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          font-weight: 600;
        }

        .nurse-details h2 {
          margin: 0 0 4px 0;
          color: #1f2937;
          font-size: 20px;
        }

        .nurse-details p {
          margin: 0;
          color: #6b7280;
          font-size: 14px;
        }

        .close-button {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #6b7280;
          padding: 8px;
        }

        .schedule-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          background: #f8fafc;
          border-bottom: 1px solid #e5e7eb;
        }

        .view-mode-toggle {
          display: flex;
          background: white;
          border-radius: 8px;
          padding: 4px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .view-mode-toggle button {
          padding: 8px 16px;
          border: none;
          background: transparent;
          cursor: pointer;
          border-radius: 6px;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .view-mode-toggle button.active {
          background: #3b82f6;
          color: white;
        }

        .action-buttons {
          display: flex;
          gap: 8px;
        }

        .export-btn, .share-btn {
          padding: 8px 16px;
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .export-btn:hover, .share-btn:hover {
          background: #f3f4f6;
          border-color: #9ca3af;
        }

        .work-stats {
          padding: 16px 24px;
          background: #f0f9ff;
          border-bottom: 1px solid #e0f2fe;
        }

        .stat-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .stat-item:last-child {
          margin-bottom: 0;
          gap: 16px;
        }

        .stat-label {
          font-size: 14px;
          color: #374151;
        }

        .stat-value {
          font-size: 18px;
          font-weight: 600;
          color: #1f2937;
        }

        .schedule-calendar {
          padding: 24px;
        }

        .schedule-calendar.month {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 12px;
        }

        .schedule-calendar.week {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 16px;
        }

        .calendar-day {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 12px;
          min-height: 100px;
          transition: all 0.2s ease;
        }

        .calendar-day.today {
          border-color: #3b82f6;
          box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
        }

        .calendar-day.other-month {
          opacity: 0.4;
        }

        .day-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .day-number {
          font-weight: 600;
          color: #1f2937;
        }

        .day-name {
          font-size: 12px;
          color: #6b7280;
        }

        .schedule-item {
          padding: 8px;
          border-radius: 6px;
          color: white;
          font-size: 12px;
        }

        .shift-info {
          display: flex;
          align-items: center;
          gap: 4px;
          margin-bottom: 4px;
        }

        .shift-icon {
          font-size: 14px;
        }

        .shift-name {
          font-weight: 600;
        }

        .shift-time {
          font-size: 11px;
          opacity: 0.9;
          margin-bottom: 2px;
        }

        .shift-location {
          font-size: 10px;
          opacity: 0.8;
        }

        .no-schedule {
          text-align: center;
          color: #9ca3af;
          font-size: 12px;
          padding: 20px 8px;
        }

        .notifications-section {
          padding: 24px;
          border-top: 1px solid #e5e7eb;
          background: #fefefe;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .section-header h3 {
          margin: 0;
          color: #374151;
          font-size: 16px;
        }

        .toggle-notifications {
          background: none;
          border: none;
          color: #6b7280;
          cursor: pointer;
          font-size: 14px;
        }

        .notifications-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .notification-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 12px;
          background: white;
          border-radius: 8px;
          border: 1px solid #e5e7eb;
        }

        .notification-item.important {
          border-color: #f59e0b;
          background: #fffbeb;
        }

        .notification-icon {
          font-size: 16px;
          margin-top: 2px;
        }

        .notification-content {
          flex: 1;
        }

        .notification-title {
          font-weight: 600;
          color: #374151;
          margin-bottom: 4px;
        }

        .notification-desc {
          font-size: 14px;
          color: #6b7280;
        }

        @media (max-width: 768px) {
          .schedule-calendar.month {
            grid-template-columns: 1fr;
            gap: 8px;
          }

          .schedule-calendar.week {
            grid-template-columns: 1fr;
            gap: 8px;
          }

          .calendar-day {
            min-height: 80px;
          }

          .work-stats .stat-item:last-child {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }
        }
      `}</style>
    </div>
  );
};

export default PersonalScheduleView;