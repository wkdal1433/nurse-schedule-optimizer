/**
 * 리팩토링된 NurseScheduleApp 메인 컴포넌트
 * Single Responsibility: UI 조합 및 라우팅만 담당
 * SOLID 원칙 적용: 각 View와 Hook으로 책임 분리
 */

import React from 'react';
import { SetupView } from './views/SetupView';
import { CalendarView } from './views/CalendarView';
import { SettingsView } from './views/SettingsView';
import PreCheckDialog from '../PreCheckDialog';
import PersonalScheduleView from '../PersonalScheduleView';
import NotificationSystem from '../NotificationSystem';
import { useNurseSchedule } from './hooks/useNurseSchedule';
import styles from './NurseScheduleApp.module.css';

const NurseScheduleApp: React.FC = () => {
  const {
    // State
    currentView,
    nurses,
    wards,
    selectedWard,
    scheduleData,
    selectedDate,
    isLoading,
    showPreCheckDialog,
    showPersonalSchedule,
    selectedNurse,
    nurseFilter,
    showNotifications,

    // Actions
    setCurrentView,
    addNurse,
    removeNurse,
    selectWard,
    canGenerateSchedule,
    performPreCheck,
    generateSchedule,
    filterScheduleDataByNurse,
    navigateDate,
    openPreCheckDialog,
    closePreCheckDialog,
    showPersonalScheduleAction,
    closePersonalSchedule,
    setNurseFilter,
    setSelectedDate,
    toggleNotifications
  } = useNurseSchedule();

  // Pre-check 승인 처리
  const handlePreCheckApproval = async (forceGenerate?: boolean) => {
    try {
      const result = await generateSchedule();

      if (result.success) {
        closePreCheckDialog();
        alert(`✅ 스케줄이 성공적으로 생성되었습니다!${result.optimization_score ? ` (최적화 점수: ${result.optimization_score.toFixed(1)})` : ''}`);
      } else {
        alert(`❌ 스케줄 생성 실패: ${result.message}`);
      }
    } catch (error) {
      console.error('스케줄 생성 중 오류:', error);
      alert('❌ 스케줄 생성 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className={styles.nurseScheduleApp}>
      {/* iOS 스타일 헤더 */}
      <div className={styles.iosHeader}>
        <h1>🏥 간호사 근무표</h1>
        <p>최적화된 근무 스케줄링 시스템</p>
      </div>

      {/* 네비게이션 */}
      <div className={styles.navContainer}>
        <button
          className={`${styles.navButton} ${currentView === 'setup' ? styles.navButtonActive : ''}`}
          onClick={() => setCurrentView('setup')}
        >
          📝 설정
        </button>
        <button
          className={`${styles.navButton} ${currentView === 'calendar' ? styles.navButtonActive : ''}`}
          onClick={() => setCurrentView('calendar')}
        >
          📅 달력
        </button>
        <button
          className={`${styles.navButton} ${currentView === 'settings' ? styles.navButtonActive : ''}`}
          onClick={() => setCurrentView('settings')}
        >
          ⚙️ 환경설정
        </button>
        <button
          className={styles.navButton}
          onClick={toggleNotifications}
        >
          🔔 {showNotifications ? '알림 끄기' : '알림 켜기'}
        </button>
      </div>

      {/* 메인 콘텐츠 - View별 분기 */}
      {currentView === 'setup' && (
        <SetupView
          nurses={nurses}
          wards={wards}
          selectedWard={selectedWard}
          onAddNurse={addNurse}
          onRemoveNurse={removeNurse}
          onSelectWard={selectWard}
          onNavigateToCalendar={() => setCurrentView('calendar')}
          onOpenPreCheck={openPreCheckDialog}
          canGenerateSchedule={canGenerateSchedule()}
          isLoading={isLoading}
        />
      )}

      {currentView === 'calendar' && (
        <CalendarView
          scheduleData={scheduleData}
          nurses={nurses}
          selectedDate={selectedDate}
          nurseFilter={nurseFilter}
          onDateChange={setSelectedDate}
          onNavigateDate={navigateDate}
          onNurseFilterChange={setNurseFilter}
          onShowPersonalSchedule={showPersonalScheduleAction}
          filterScheduleDataByNurse={filterScheduleDataByNurse}
        />
      )}

      {currentView === 'settings' && (
        <SettingsView
          nurses={nurses}
          selectedWard={selectedWard}
          onNavigateToCalendar={() => setCurrentView('calendar')}
          onNavigateToSetup={() => setCurrentView('setup')}
          onToggleNotifications={toggleNotifications}
          showNotifications={showNotifications}
        />
      )}

      {/* Pre-Check 다이얼로그 */}
      {showPreCheckDialog && selectedWard && (
        <PreCheckDialog
          isOpen={showPreCheckDialog}
          onClose={closePreCheckDialog}
          wardId={selectedWard.id}
          year={new Date().getFullYear()}
          month={new Date().getMonth() + 1}
          onProceed={handlePreCheckApproval}
        />
      )}

      {/* 개인 스케줄 뷰 */}
      {showPersonalSchedule && selectedNurse && (
        <PersonalScheduleView
          nurse={selectedNurse}
          scheduleData={scheduleData}
          selectedDate={selectedDate}
          onClose={closePersonalSchedule}
        />
      )}

      {/* 알림 시스템 */}
      {showNotifications && (
        <NotificationSystem
          isOpen={showNotifications}
          onClose={() => toggleNotifications()}
        />
      )}
    </div>
  );
};

export default NurseScheduleApp;