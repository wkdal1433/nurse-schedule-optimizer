import React, { useState } from 'react';

interface Nurse {
  id: number;
  name: string;
  role: 'head_nurse' | 'staff_nurse' | 'new_nurse';
  employment_type: 'full_time' | 'part_time';
  experience_level: number;
}

interface Ward {
  id: number;
  name: string;
  min_nurses_per_shift: number;
  shift_types: string[];
}

interface ScheduleData {
  date: string;
  nurses: {
    [nurseId: number]: {
      shift: 'DAY' | 'EVENING' | 'NIGHT' | 'OFF';
      nurse: Nurse;
    };
  };
}

const NurseScheduleApp: React.FC = () => {
  const [currentView, setCurrentView] = useState<'setup' | 'calendar' | 'settings'>('setup');
  const [nurses, setNurses] = useState<Nurse[]>([]);
  const [selectedWard, setSelectedWard] = useState<Ward | null>(null);
  const [scheduleData, setScheduleData] = useState<ScheduleData[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isLoading, setIsLoading] = useState(false);

  // 병동 데이터 (실제로는 백엔드에서 가져올 것)
  const wards: Ward[] = [
    { id: 1, name: '내과 병동', min_nurses_per_shift: 3, shift_types: ['DAY', 'EVENING', 'NIGHT'] },
    { id: 2, name: '외과 병동', min_nurses_per_shift: 4, shift_types: ['DAY', 'EVENING', 'NIGHT'] },
    { id: 3, name: '중환자실', min_nurses_per_shift: 2, shift_types: ['DAY', 'NIGHT'] },
    { id: 4, name: '응급실', min_nurses_per_shift: 5, shift_types: ['DAY', 'EVENING', 'NIGHT'] }
  ];

  // 간호사 추가
  const addNurse = (name: string, role: Nurse['role'], employment_type: Nurse['employment_type'], experience: number) => {
    const newNurse: Nurse = {
      id: Date.now(),
      name,
      role,
      employment_type,
      experience_level: experience
    };
    setNurses([...nurses, newNurse]);
  };

  // 근무표 생성
  const generateSchedule = async () => {
    if (!selectedWard || nurses.length === 0) {
      alert('병동과 간호사를 먼저 설정해주세요.');
      return;
    }

    setIsLoading(true);
    try {
      // 임시 근무표 데이터 생성 (실제로는 백엔드 알고리즘 호출)
      const schedule: ScheduleData[] = [];
      const startDate = new Date(selectedDate);

      for (let i = 0; i < 30; i++) {
        const currentDate = new Date(startDate);
        currentDate.setDate(startDate.getDate() + i);

        const daySchedule: ScheduleData = {
          date: currentDate.toISOString().split('T')[0],
          nurses: {}
        };

        // 각 간호사에게 근무 배정 (단순 로직)
        nurses.forEach((nurse, index) => {
          const shifts = ['DAY', 'EVENING', 'NIGHT', 'OFF'] as const;
          const shift = shifts[(index + i) % 4];
          daySchedule.nurses[nurse.id] = { shift, nurse };
        });

        schedule.push(daySchedule);
      }

      setScheduleData(schedule);
      setCurrentView('calendar');
    } catch (error) {
      console.error('근무표 생성 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 달력 렌더링을 위한 함수들
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startDayOfWeek = firstDay.getDay();

    const days: any[] = [];

    // 이전 달의 빈 칸들
    for (let i = 0; i < startDayOfWeek; i++) {
      days.push(null);
    }

    // 현재 달의 날짜들
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }

    return days;
  };

  const getScheduleForDate = (date: Date): ScheduleData | undefined => {
    const dateStr = date.toISOString().split('T')[0];
    return scheduleData.find(s => s.date === dateStr);
  };

  // 컴포넌트들
  const SetupView = () => (
    <div className="setup-container">
      <div className="ios-header">
        <h1>🏥 근무표 설정</h1>
        <p>병동과 간호사 정보를 입력해주세요</p>
      </div>

      <div className="setup-section">
        <h2>병동 선택</h2>
        <div className="ward-grid">
          {wards.map(ward => (
            <div
              key={ward.id}
              className={`ward-card ${selectedWard?.id === ward.id ? 'selected' : ''}`}
              onClick={() => setSelectedWard(ward)}
            >
              <div className="ward-name">{ward.name}</div>
              <div className="ward-info">최소 {ward.min_nurses_per_shift}명/교대</div>
            </div>
          ))}
        </div>
      </div>

      <div className="setup-section">
        <h2>간호사 등록 ({nurses.length}명)</h2>
        <NurseRegistrationForm onAdd={addNurse} />

        {nurses.length > 0 && (
          <div className="nurse-list">
            {nurses.map(nurse => (
              <div key={nurse.id} className="nurse-item">
                <div className="nurse-info">
                  <div className="nurse-name">{nurse.name}</div>
                  <div className="nurse-details">
                    {nurse.role === 'head_nurse' ? '수간호사' :
                     nurse.role === 'staff_nurse' ? '간호사' : '신입간호사'} •{' '}
                    {nurse.employment_type === 'full_time' ? '정규직' : '시간제'} •{' '}
                    {nurse.experience_level}년차
                  </div>
                </div>
                <button
                  className="delete-nurse-btn"
                  onClick={() => setNurses(nurses.filter(n => n.id !== nurse.id))}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="setup-actions">
        <button
          className="ios-primary-button"
          onClick={generateSchedule}
          disabled={!selectedWard || nurses.length === 0 || isLoading}
        >
          {isLoading ? (
            <>
              <span className="loading-spinner"></span>
              근무표 생성 중...
            </>
          ) : (
            '📅 근무표 생성'
          )}
        </button>
      </div>
    </div>
  );

  const NurseRegistrationForm = ({ onAdd }: { onAdd: (name: string, role: Nurse['role'], employment: Nurse['employment_type'], experience: number) => void }) => {
    const [name, setName] = useState('');
    const [role, setRole] = useState<Nurse['role']>('staff_nurse');
    const [employment, setEmployment] = useState<Nurse['employment_type']>('full_time');
    const [experience, setExperience] = useState(1);
    const [showForm, setShowForm] = useState(false);

    const handleSubmit = () => {
      if (!name.trim()) return;
      onAdd(name, role, employment, experience);
      setName('');
      setRole('staff_nurse');
      setEmployment('full_time');
      setExperience(1);
      setShowForm(false);
    };

    if (!showForm) {
      return (
        <button className="ios-secondary-button" onClick={() => setShowForm(true)}>
          + 간호사 추가
        </button>
      );
    }

    return (
      <div className="nurse-form">
        <div className="form-row">
          <input
            type="text"
            placeholder="간호사 이름"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="ios-input"
          />
        </div>

        <div className="form-row">
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as Nurse['role'])}
            className="ios-select"
          >
            <option value="head_nurse">수간호사</option>
            <option value="staff_nurse">간호사</option>
            <option value="new_nurse">신입간호사</option>
          </select>

          <select
            value={employment}
            onChange={(e) => setEmployment(e.target.value as Nurse['employment_type'])}
            className="ios-select"
          >
            <option value="full_time">정규직</option>
            <option value="part_time">시간제</option>
          </select>
        </div>

        <div className="form-row">
          <label className="experience-label">
            경력: {experience}년차
            <input
              type="range"
              min="0"
              max="30"
              value={experience}
              onChange={(e) => setExperience(parseInt(e.target.value))}
              className="ios-slider"
            />
          </label>
        </div>

        <div className="form-actions">
          <button className="ios-primary-button" onClick={handleSubmit}>
            추가
          </button>
          <button className="ios-cancel-button" onClick={() => setShowForm(false)}>
            취소
          </button>
        </div>
      </div>
    );
  };

  const CalendarView = () => {
    const days = getDaysInMonth(selectedDate);
    const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];

    return (
      <div className="calendar-container">
        <div className="calendar-header">
          <button
            className="nav-button"
            onClick={() => setCurrentView('setup')}
          >
            ← 설정
          </button>
          <h1>📅 {selectedDate.getFullYear()}년 {monthNames[selectedDate.getMonth()]}</h1>
          <button className="settings-button" onClick={() => setCurrentView('settings')}>
            ⚙️
          </button>
        </div>

        <div className="calendar-navigation">
          <button
            className="month-nav-btn"
            onClick={() => {
              const prev = new Date(selectedDate);
              prev.setMonth(prev.getMonth() - 1);
              setSelectedDate(prev);
            }}
          >
            ‹
          </button>
          <button
            className="month-nav-btn"
            onClick={() => {
              const next = new Date(selectedDate);
              next.setMonth(next.getMonth() + 1);
              setSelectedDate(next);
            }}
          >
            ›
          </button>
        </div>

        <div className="calendar-grid">
          <div className="calendar-weekdays">
            {dayNames.map(day => (
              <div key={day} className="weekday">{day}</div>
            ))}
          </div>

          <div className="calendar-days">
            {days.map((date, index) => {
              if (!date) {
                return <div key={index} className="empty-day"></div>;
              }

              const currentDate = date as Date;
              const daySchedule = getScheduleForDate(currentDate);
              const isToday = currentDate.toDateString() === new Date().toDateString();

              return (
                <div key={currentDate.toISOString()} className={`calendar-day ${isToday ? 'today' : ''}`}>
                  <div className="day-number">{currentDate.getDate()}</div>
                  {daySchedule && (
                    <div className="day-schedule">
                      {Object.values(daySchedule.nurses).map((assignment, i) => (
                        <div
                          key={i}
                          className={`schedule-item ${assignment.shift.toLowerCase()}`}
                        >
                          <div className="nurse-initial">
                            {assignment.nurse.name.charAt(0)}
                          </div>
                          <div className="shift-type">
                            {assignment.shift === 'DAY' ? 'D' :
                             assignment.shift === 'EVENING' ? 'E' :
                             assignment.shift === 'NIGHT' ? 'N' : '-'}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="schedule-legend">
          <div className="legend-item">
            <span className="legend-color day"></span> 주간 (D)
          </div>
          <div className="legend-item">
            <span className="legend-color evening"></span> 저녁 (E)
          </div>
          <div className="legend-item">
            <span className="legend-color night"></span> 야간 (N)
          </div>
          <div className="legend-item">
            <span className="legend-color off"></span> 휴무 (-)
          </div>
        </div>
      </div>
    );
  };

  const SettingsView = () => (
    <div className="settings-container">
      <div className="settings-header">
        <button
          className="nav-button"
          onClick={() => setCurrentView('calendar')}
        >
          ← 달력
        </button>
        <h1>⚙️ 설정</h1>
      </div>

      <div className="settings-section">
        <h2>병동 정보</h2>
        {selectedWard ? (
          <div className="current-ward-info">
            <h3>{selectedWard.name}</h3>
            <p>최소 인력: {selectedWard.min_nurses_per_shift}명/교대</p>
            <p>근무 형태: {selectedWard.shift_types.join(', ')}</p>
          </div>
        ) : (
          <p>병동이 선택되지 않았습니다.</p>
        )}
      </div>

      <div className="settings-section">
        <h2>등록된 간호사 ({nurses.length}명)</h2>
        <div className="nurse-summary">
          {nurses.map(nurse => (
            <div key={nurse.id} className="nurse-summary-item">
              {nurse.name} ({nurse.role === 'head_nurse' ? '수간호사' :
                           nurse.role === 'staff_nurse' ? '간호사' : '신입간호사'})
            </div>
          ))}
        </div>
      </div>

      <div className="settings-actions">
        <button
          className="ios-primary-button"
          onClick={() => setCurrentView('setup')}
        >
          설정 수정
        </button>
        <button
          className="ios-secondary-button"
          onClick={generateSchedule}
          disabled={isLoading}
        >
          근무표 재생성
        </button>
      </div>
    </div>
  );

  return (
    <div className="nurse-schedule-app">
      {currentView === 'setup' && <SetupView />}
      {currentView === 'calendar' && <CalendarView />}
      {currentView === 'settings' && <SettingsView />}

      <style jsx>{`
        .nurse-schedule-app {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', sans-serif;
          color: #1d1d1f;
          padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
        }

        /* iOS 헤더 스타일 */
        .ios-header {
          text-align: center;
          padding: 20px;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          margin: 20px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        .ios-header h1 {
          font-size: 32px;
          font-weight: 700;
          margin: 0 0 8px 0;
          background: linear-gradient(135deg, #667eea, #764ba2);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .ios-header p {
          font-size: 17px;
          color: #6d6d70;
          margin: 0;
          font-weight: 400;
        }

        /* 설정 섹션 */
        .setup-container {
          max-width: 400px;
          margin: 0 auto;
          padding: 20px;
        }

        .setup-section {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          padding: 24px;
          margin-bottom: 20px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        .setup-section h2 {
          font-size: 22px;
          font-weight: 600;
          margin: 0 0 16px 0;
          color: #1d1d1f;
        }

        /* 병동 카드 */
        .ward-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 12px;
        }

        .ward-card {
          background: white;
          border: 2px solid #e5e5ea;
          border-radius: 16px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
          position: relative;
        }

        .ward-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 20px 40px rgba(102, 126, 234, 0.15);
        }

        .ward-card.selected {
          border-color: #667eea;
          background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        }

        .ward-card.selected::after {
          content: '✓';
          position: absolute;
          top: 12px;
          right: 16px;
          color: #667eea;
          font-weight: 600;
          font-size: 18px;
        }

        .ward-name {
          font-size: 18px;
          font-weight: 600;
          color: #1d1d1f;
          margin-bottom: 4px;
        }

        .ward-info {
          font-size: 15px;
          color: #6d6d70;
        }

        /* iOS 버튼 스타일 */
        .ios-primary-button {
          background: linear-gradient(135deg, #667eea, #764ba2);
          color: white;
          border: none;
          border-radius: 16px;
          padding: 16px 32px;
          font-size: 17px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          width: 100%;
          transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
          box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }

        .ios-primary-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 20px 40px rgba(102, 126, 234, 0.4);
        }

        .ios-primary-button:active {
          transform: translateY(0);
        }

        .ios-primary-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .ios-secondary-button {
          background: rgba(255, 255, 255, 0.9);
          color: #667eea;
          border: 2px solid rgba(102, 126, 234, 0.2);
          border-radius: 16px;
          padding: 12px 24px;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
          backdrop-filter: blur(20px);
        }

        .ios-secondary-button:hover {
          background: rgba(102, 126, 234, 0.1);
          border-color: #667eea;
        }

        .ios-cancel-button {
          background: transparent;
          color: #ff3b30;
          border: 2px solid rgba(255, 59, 48, 0.2);
          border-radius: 12px;
          padding: 12px 24px;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
        }

        /* 간호사 폼 */
        .nurse-form {
          background: rgba(248, 248, 248, 0.8);
          border-radius: 16px;
          padding: 20px;
          margin-bottom: 16px;
        }

        .form-row {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
        }

        .form-row:last-child {
          margin-bottom: 0;
        }

        .ios-input, .ios-select {
          background: white;
          border: 1px solid #e5e5ea;
          border-radius: 12px;
          padding: 12px 16px;
          font-size: 16px;
          font-weight: 400;
          flex: 1;
          transition: border-color 0.2s ease;
        }

        .ios-input:focus, .ios-select:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .experience-label {
          font-size: 16px;
          color: #1d1d1f;
          display: block;
          width: 100%;
        }

        .ios-slider {
          width: 100%;
          margin-top: 8px;
          -webkit-appearance: none;
          appearance: none;
          height: 6px;
          border-radius: 3px;
          background: #e5e5ea;
          outline: none;
        }

        .ios-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: #667eea;
          cursor: pointer;
          box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }

        .form-actions {
          display: flex;
          gap: 12px;
        }

        .form-actions .ios-primary-button,
        .form-actions .ios-cancel-button {
          flex: 1;
        }

        /* 간호사 목록 */
        .nurse-list {
          margin-top: 16px;
        }

        .nurse-item {
          background: white;
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 8px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border: 1px solid #f0f0f5;
        }

        .nurse-info {
          flex: 1;
        }

        .nurse-name {
          font-size: 17px;
          font-weight: 600;
          color: #1d1d1f;
          margin-bottom: 4px;
        }

        .nurse-details {
          font-size: 14px;
          color: #6d6d70;
        }

        .delete-nurse-btn {
          background: #ff3b30;
          color: white;
          border: none;
          border-radius: 50%;
          width: 28px;
          height: 28px;
          cursor: pointer;
          font-size: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        /* 달력 뷰 */
        .calendar-container {
          max-width: 400px;
          margin: 0 auto;
          padding: 20px;
        }

        .calendar-header {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          padding: 20px;
          margin-bottom: 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        .calendar-header h1 {
          font-size: 24px;
          font-weight: 600;
          margin: 0;
          flex: 1;
          text-align: center;
        }

        .nav-button, .settings-button {
          background: rgba(102, 126, 234, 0.1);
          color: #667eea;
          border: none;
          border-radius: 12px;
          padding: 8px 12px;
          font-size: 16px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .nav-button:hover, .settings-button:hover {
          background: rgba(102, 126, 234, 0.2);
        }

        .calendar-navigation {
          display: flex;
          justify-content: space-between;
          margin-bottom: 20px;
          padding: 0 20px;
        }

        .month-nav-btn {
          background: rgba(255, 255, 255, 0.9);
          border: none;
          border-radius: 50%;
          width: 44px;
          height: 44px;
          font-size: 20px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
          transition: all 0.2s ease;
        }

        .month-nav-btn:hover {
          transform: scale(1.05);
          box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        }

        .calendar-grid {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          padding: 20px;
          margin-bottom: 20px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        .calendar-weekdays {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 4px;
          margin-bottom: 16px;
        }

        .weekday {
          text-align: center;
          font-size: 14px;
          font-weight: 600;
          color: #6d6d70;
          padding: 8px 0;
        }

        .calendar-days {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 4px;
        }

        .calendar-day {
          min-height: 80px;
          border-radius: 12px;
          padding: 8px;
          position: relative;
          transition: all 0.2s ease;
        }

        .calendar-day:hover {
          background: rgba(102, 126, 234, 0.05);
        }

        .calendar-day.today {
          background: rgba(102, 126, 234, 0.1);
          border: 2px solid #667eea;
        }

        .empty-day {
          min-height: 80px;
        }

        .day-number {
          font-size: 16px;
          font-weight: 600;
          color: #1d1d1f;
          margin-bottom: 4px;
        }

        .day-schedule {
          display: flex;
          flex-wrap: wrap;
          gap: 2px;
        }

        .schedule-item {
          width: 20px;
          height: 20px;
          border-radius: 6px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-size: 8px;
          font-weight: 600;
          color: white;
          position: relative;
        }

        .schedule-item.day {
          background: #34c759;
        }

        .schedule-item.evening {
          background: #ff9500;
        }

        .schedule-item.night {
          background: #5856d6;
        }

        .schedule-item.off {
          background: #8e8e93;
        }

        .nurse-initial {
          font-size: 6px;
          line-height: 1;
        }

        .shift-type {
          font-size: 6px;
          line-height: 1;
          margin-top: 1px;
        }

        .schedule-legend {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 16px;
          padding: 16px;
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
          justify-content: center;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 14px;
          font-weight: 500;
        }

        .legend-color {
          width: 12px;
          height: 12px;
          border-radius: 3px;
        }

        .legend-color.day {
          background: #34c759;
        }

        .legend-color.evening {
          background: #ff9500;
        }

        .legend-color.night {
          background: #5856d6;
        }

        .legend-color.off {
          background: #8e8e93;
        }

        /* 설정 뷰 */
        .settings-container {
          max-width: 400px;
          margin: 0 auto;
          padding: 20px;
        }

        .settings-header {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          padding: 20px;
          margin-bottom: 20px;
          display: flex;
          align-items: center;
          gap: 16px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        .settings-header h1 {
          font-size: 24px;
          font-weight: 600;
          margin: 0;
          flex: 1;
        }

        .settings-section {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          padding: 24px;
          margin-bottom: 20px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        .settings-section h2 {
          font-size: 20px;
          font-weight: 600;
          margin: 0 0 16px 0;
          color: #1d1d1f;
        }

        .current-ward-info h3 {
          font-size: 18px;
          font-weight: 600;
          color: #667eea;
          margin: 0 0 8px 0;
        }

        .current-ward-info p {
          font-size: 15px;
          color: #6d6d70;
          margin: 4px 0;
        }

        .nurse-summary {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .nurse-summary-item {
          background: rgba(102, 126, 234, 0.1);
          border-radius: 8px;
          padding: 12px 16px;
          font-size: 15px;
          font-weight: 500;
          color: #1d1d1f;
        }

        .settings-actions {
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding: 0 20px;
        }

        .loading-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-radius: 50%;
          border-top: 2px solid white;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        /* 모바일 최적화 */
        @media (max-width: 480px) {
          .nurse-schedule-app {
            padding: 10px;
          }

          .setup-container, .calendar-container, .settings-container {
            padding: 10px;
          }

          .ios-header {
            margin: 10px;
            padding: 16px;
          }

          .ios-header h1 {
            font-size: 24px;
          }

          .calendar-day {
            min-height: 60px;
          }

          .schedule-item {
            width: 16px;
            height: 16px;
          }
        }
      `}</style>
    </div>
  );
};

export default NurseScheduleApp;