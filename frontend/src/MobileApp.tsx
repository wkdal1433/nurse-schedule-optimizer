import React, { useState } from 'react';
import { complianceAPI } from './services/api';

const MobileApp: React.FC = () => {
  const [currentScreen, setCurrentScreen] = useState('home');
  const [isLoading, setIsLoading] = useState(false);
  const [notification, setNotification] = useState<string>('');
  const [scheduleData, setScheduleData] = useState<any[]>([]);

  // 알림 표시 함수
  const showNotification = (message: string) => {
    setNotification(message);
    setTimeout(() => setNotification(''), 3000);
  };

  // 기본 규칙 생성 테스트
  const handleCreateDefaultRules = async () => {
    setIsLoading(true);
    try {
      await complianceAPI.createDefaultRules(1);
      showNotification('✅ 기본 규칙이 생성되었습니다');
    } catch (error) {
      showNotification('❌ 규칙 생성에 실패했습니다');
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 근무표 생성 (임시)
  const handleGenerateSchedule = async () => {
    setIsLoading(true);
    try {
      // 임시 스케줄 데이터 생성
      const mockSchedule = [
        { id: 1, nurse: '김간호사', date: '2024-01-15', shift: 'DAY' },
        { id: 2, nurse: '이간호사', date: '2024-01-15', shift: 'EVENING' },
        { id: 3, nurse: '박간호사', date: '2024-01-15', shift: 'NIGHT' },
        { id: 4, nurse: '최간호사', date: '2024-01-15', shift: 'OFF' }
      ];
      setScheduleData(mockSchedule);
      showNotification('✅ 근무표가 생성되었습니다');
    } catch (error) {
      showNotification('❌ 근무표 생성에 실패했습니다');
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Apple iOS 스타일 로딩 인디케이터
  const LoadingSpinner = () => (
    <div className="loading-spinner">
      <div className="spinner"></div>
    </div>
  );

  // 알림 컴포넌트
  const NotificationBanner = () => (
    notification ? (
      <div className="notification-banner">
        {notification}
      </div>
    ) : null
  );

  // 홈 화면 컴포넌트
  const HomeScreen = () => (
    <div className="screen">
      <div className="header">
        <h1>🏥 간호사 근무표</h1>
        <p>자동 근무표 최적화 시스템</p>
      </div>

      <div className="main-actions">
        <button
          className="primary-button"
          onClick={handleGenerateSchedule}
          disabled={isLoading}
        >
          {isLoading ? <LoadingSpinner /> : '📅 근무표 생성'}
        </button>

        <button
          className="secondary-button"
          onClick={() => setCurrentScreen('schedule')}
        >
          📋 근무표 보기
        </button>

        <button
          className="secondary-button"
          onClick={() => setCurrentScreen('settings')}
        >
          ⚙️ 설정
        </button>
      </div>

      <div className="quick-actions">
        <div className="quick-action-card" onClick={handleCreateDefaultRules}>
          <div className="card-icon">🔧</div>
          <div className="card-title">기본 설정</div>
          <div className="card-subtitle">기본 규칙 생성</div>
        </div>

        <div className="quick-action-card" onClick={() => setCurrentScreen('rules')}>
          <div className="card-icon">📜</div>
          <div className="card-title">근무 규칙</div>
          <div className="card-subtitle">규칙 관리</div>
        </div>

        <div className="quick-action-card" onClick={() => setCurrentScreen('staff')}>
          <div className="card-icon">👥</div>
          <div className="card-title">직원 관리</div>
          <div className="card-subtitle">간호사 등록</div>
        </div>
      </div>
    </div>
  );

  // 스케줄 화면
  const ScheduleScreen = () => (
    <div className="screen">
      <div className="header">
        <button className="back-button" onClick={() => setCurrentScreen('home')}>
          ← 뒤로
        </button>
        <h1>📋 현재 근무표</h1>
      </div>

      <div className="schedule-content">
        {scheduleData.length > 0 ? (
          <div className="schedule-list">
            {scheduleData.map((item) => (
              <div key={item.id} className="schedule-item">
                <div className="schedule-nurse">{item.nurse}</div>
                <div className="schedule-date">{item.date}</div>
                <div className={`schedule-shift ${item.shift.toLowerCase()}`}>
                  {item.shift}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>근무표가 없습니다</h3>
            <p>홈 화면에서 근무표를 생성해주세요</p>
            <button
              className="primary-button"
              onClick={() => setCurrentScreen('home')}
            >
              홈으로 돌아가기
            </button>
          </div>
        )}
      </div>
    </div>
  );

  // 설정 화면
  const SettingsScreen = () => (
    <div className="screen">
      <div className="header">
        <button className="back-button" onClick={() => setCurrentScreen('home')}>
          ← 뒤로
        </button>
        <h1>⚙️ 설정</h1>
      </div>

      <div className="settings-content">
        <div className="settings-section">
          <h2>근무 관리</h2>
          <div className="settings-item" onClick={() => setCurrentScreen('rules')}>
            <div className="settings-icon">📜</div>
            <div className="settings-text">
              <div className="settings-title">근무 규칙</div>
              <div className="settings-subtitle">법적 준수, 연속 근무 제한</div>
            </div>
            <div className="settings-arrow">›</div>
          </div>

          <div className="settings-item" onClick={() => setCurrentScreen('staff')}>
            <div className="settings-icon">👥</div>
            <div className="settings-text">
              <div className="settings-title">직원 관리</div>
              <div className="settings-subtitle">간호사 등록 및 역할 설정</div>
            </div>
            <div className="settings-arrow">›</div>
          </div>
        </div>

        <div className="settings-section">
          <h2>시스템</h2>
          <div className="settings-item">
            <div className="settings-icon">🔒</div>
            <div className="settings-text">
              <div className="settings-title">보안 설정</div>
              <div className="settings-subtitle">계정 및 접근 권한</div>
            </div>
            <div className="settings-arrow">›</div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="mobile-app">
      <NotificationBanner />

      {currentScreen === 'home' && <HomeScreen />}
      {currentScreen === 'schedule' && <ScheduleScreen />}
      {currentScreen === 'settings' && <SettingsScreen />}

      {/* 기타 화면들은 임시로 홈으로 리다이렉트 */}
      {['rules', 'staff'].includes(currentScreen) && (
        <div className="screen">
          <div className="header">
            <button className="back-button" onClick={() => setCurrentScreen('home')}>
              ← 뒤로
            </button>
            <h1>🚧 개발 중</h1>
          </div>
          <div className="empty-state">
            <div className="empty-icon">🚧</div>
            <h3>이 기능은 개발 중입니다</h3>
            <p>곧 사용하실 수 있습니다</p>
            <button
              className="primary-button"
              onClick={() => setCurrentScreen('home')}
            >
              홈으로 돌아가기
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        .mobile-app {
          min-height: 100vh;
          background: #f2f2f7;
          font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
          color: #1c1c1e;
          overflow-x: hidden;
        }

        .notification-banner {
          position: fixed;
          top: 20px;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(0, 0, 0, 0.9);
          color: white;
          padding: 12px 20px;
          border-radius: 20px;
          font-size: 14px;
          font-weight: 500;
          z-index: 1000;
          backdrop-filter: blur(20px);
          animation: slideDown 0.3s ease-out;
        }

        @keyframes slideDown {
          from { opacity: 0; transform: translate(-50%, -100%); }
          to { opacity: 1; transform: translate(-50%, 0); }
        }

        .screen {
          padding: 20px;
          max-width: 400px;
          margin: 0 auto;
          min-height: 100vh;
        }

        .header {
          text-align: center;
          margin-bottom: 30px;
          padding-top: 20px;
        }

        .header h1 {
          font-size: 28px;
          font-weight: 700;
          margin: 0 0 8px 0;
          color: #1c1c1e;
        }

        .header p {
          font-size: 16px;
          color: #8e8e93;
          margin: 0;
          font-weight: 400;
        }

        .back-button {
          position: absolute;
          left: 0;
          top: 25px;
          background: none;
          border: none;
          font-size: 17px;
          color: #007aff;
          font-weight: 400;
          cursor: pointer;
          padding: 8px;
        }

        .back-button:active {
          opacity: 0.3;
        }

        .main-actions {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 40px;
        }

        .primary-button {
          background: #007aff;
          color: white;
          border: none;
          border-radius: 12px;
          padding: 16px 24px;
          font-size: 17px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          transition: all 0.2s ease;
          min-height: 56px;
        }

        .primary-button:hover {
          background: #0056cc;
          transform: translateY(-1px);
          box-shadow: 0 8px 25px rgba(0, 122, 255, 0.3);
        }

        .primary-button:active {
          transform: translateY(0);
          background: #004299;
        }

        .primary-button:disabled {
          background: #8e8e93;
          cursor: not-allowed;
          transform: none;
          box-shadow: none;
        }

        .secondary-button {
          background: white;
          color: #007aff;
          border: 1px solid #e5e5ea;
          border-radius: 12px;
          padding: 16px 24px;
          font-size: 17px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          min-height: 56px;
        }

        .secondary-button:hover {
          background: #f9f9f9;
          border-color: #007aff;
          transform: translateY(-1px);
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }

        .secondary-button:active {
          background: #f0f0f0;
          transform: translateY(0);
        }

        .quick-actions {
          display: grid;
          grid-template-columns: 1fr;
          gap: 12px;
        }

        .quick-action-card {
          background: white;
          border-radius: 16px;
          padding: 20px;
          cursor: pointer;
          border: 1px solid #e5e5ea;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .quick-action-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
          border-color: #007aff;
        }

        .quick-action-card:active {
          transform: translateY(0);
        }

        .card-icon {
          font-size: 24px;
          width: 48px;
          height: 48px;
          background: #f2f2f7;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .card-title {
          font-size: 17px;
          font-weight: 600;
          color: #1c1c1e;
          margin: 0;
        }

        .card-subtitle {
          font-size: 15px;
          color: #8e8e93;
          margin: 4px 0 0 0;
        }

        .loading-spinner {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .spinner {
          width: 20px;
          height: 20px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-radius: 50%;
          border-top: 2px solid white;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .schedule-content {
          margin-top: 20px;
        }

        .schedule-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .schedule-item {
          background: white;
          border-radius: 12px;
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border: 1px solid #e5e5ea;
        }

        .schedule-nurse {
          font-weight: 600;
          font-size: 16px;
          color: #1c1c1e;
        }

        .schedule-date {
          font-size: 14px;
          color: #8e8e93;
        }

        .schedule-shift {
          padding: 6px 12px;
          border-radius: 8px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .schedule-shift.day {
          background: #fff3cd;
          color: #856404;
        }

        .schedule-shift.evening {
          background: #d1ecf1;
          color: #0c5460;
        }

        .schedule-shift.night {
          background: #d4edda;
          color: #155724;
        }

        .schedule-shift.off {
          background: #f8d7da;
          color: #721c24;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
        }

        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .empty-state h3 {
          font-size: 20px;
          font-weight: 600;
          color: #1c1c1e;
          margin: 0 0 8px 0;
        }

        .empty-state p {
          font-size: 16px;
          color: #8e8e93;
          margin: 0 0 24px 0;
        }

        .settings-content {
          margin-top: 20px;
        }

        .settings-section {
          margin-bottom: 32px;
        }

        .settings-section h2 {
          font-size: 20px;
          font-weight: 600;
          color: #1c1c1e;
          margin: 0 0 16px 0;
        }

        .settings-item {
          background: white;
          border-radius: 12px;
          padding: 16px;
          display: flex;
          align-items: center;
          gap: 16px;
          cursor: pointer;
          margin-bottom: 8px;
          border: 1px solid #e5e5ea;
          transition: all 0.2s ease;
        }

        .settings-item:hover {
          background: #f9f9f9;
          transform: translateY(-1px);
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }

        .settings-item:active {
          background: #f0f0f0;
          transform: translateY(0);
        }

        .settings-icon {
          font-size: 20px;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .settings-text {
          flex: 1;
        }

        .settings-title {
          font-size: 16px;
          font-weight: 500;
          color: #1c1c1e;
          margin: 0;
        }

        .settings-subtitle {
          font-size: 14px;
          color: #8e8e93;
          margin: 2px 0 0 0;
        }

        .settings-arrow {
          color: #8e8e93;
          font-size: 18px;
          font-weight: 300;
        }

        @media (max-width: 480px) {
          .screen {
            padding: 16px;
          }

          .header h1 {
            font-size: 24px;
          }

          .primary-button, .secondary-button {
            font-size: 16px;
            padding: 14px 20px;
            min-height: 52px;
          }
        }
      `}</style>
    </div>
  );
};

export default MobileApp;