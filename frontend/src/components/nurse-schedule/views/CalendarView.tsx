/**
 * 캘린더 뷰 컴포넌트
 * Single Responsibility: 캘린더 UI 표시만 담당
 */

import React from 'react';
import { Nurse, ScheduleData } from '../types';
import DraggableCalendar from '../../DraggableCalendar';
import styles from '../NurseScheduleApp.module.css';

interface CalendarViewProps {
  scheduleData: ScheduleData[];
  nurses: Nurse[];
  selectedDate: Date;
  nurseFilter: number | null;
  onDateChange: (date: Date) => void;
  onNavigateDate: (direction: 'prev' | 'next') => void;
  onNurseFilterChange: (nurseId: number | null) => void;
  onShowPersonalSchedule: (nurse: Nurse) => void;
  filterScheduleDataByNurse: (scheduleData: ScheduleData[], nurseId: number) => ScheduleData[];
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  scheduleData,
  nurses,
  selectedDate,
  nurseFilter,
  onDateChange,
  onNavigateDate,
  onNurseFilterChange,
  onShowPersonalSchedule,
  filterScheduleDataByNurse
}) => {
  const formatMonthYear = (date: Date): string => {
    return new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: 'long'
    }).format(date);
  };

  const getFilteredScheduleData = () => {
    if (nurseFilter) {
      return filterScheduleDataByNurse(scheduleData, nurseFilter);
    }
    return scheduleData;
  };

  const handlePersonalViewClick = () => {
    if (nurseFilter) {
      const nurse = nurses.find(n => n.id === nurseFilter);
      if (nurse) {
        onShowPersonalSchedule(nurse);
      }
    }
  };

  return (
    <div className={styles.calendarContainer}>
      {/* 캘린더 헤더 */}
      <div className={styles.calendarHeader}>
        {/* 날짜 네비게이션 */}
        <div className={styles.dateNavigation}>
          <button
            className={styles.dateNavButton}
            onClick={() => onNavigateDate('prev')}
          >
            ‹
          </button>
          <span className={styles.currentMonth}>
            {formatMonthYear(selectedDate)}
          </span>
          <button
            className={styles.dateNavButton}
            onClick={() => onNavigateDate('next')}
          >
            ›
          </button>
        </div>

        {/* 필터 컨트롤 */}
        <div className={styles.filterControls}>
          <select
            className={styles.nurseFilter}
            value={nurseFilter || ''}
            onChange={(e) => onNurseFilterChange(e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">전체 간호사</option>
            {nurses.map(nurse => (
              <option key={nurse.id} value={nurse.id}>
                {nurse.name} ({
                  nurse.role === 'head_nurse' ? '수간호사' :
                  nurse.role === 'staff_nurse' ? '간호사' : '신입간호사'
                })
              </option>
            ))}
          </select>

          {nurseFilter && (
            <button
              className={styles.personalViewBtn}
              onClick={handlePersonalViewClick}
            >
              👤 개인 스케줄 보기
            </button>
          )}
        </div>
      </div>

      {/* 드래그 앤 드롭 캘린더 */}
      <DraggableCalendar
        scheduleId={1} // 임시 ID, 실제로는 생성된 스케줄 ID 사용
        scheduleData={getFilteredScheduleData()}
        nurses={nurses}
        selectedDate={selectedDate}
        onDateChange={onDateChange}
      />

      {/* 스케줄 범례 */}
      <div className={styles.scheduleLegend}>
        <div className={styles.legendItem}>
          <span className={`${styles.legendColor} ${styles.day}`}></span>
          주간 (D)
        </div>
        <div className={styles.legendItem}>
          <span className={`${styles.legendColor} ${styles.evening}`}></span>
          저녁 (E)
        </div>
        <div className={styles.legendItem}>
          <span className={`${styles.legendColor} ${styles.night}`}></span>
          야간 (N)
        </div>
        <div className={styles.legendItem}>
          <span className={`${styles.legendColor} ${styles.off}`}></span>
          휴무 (-)
        </div>
      </div>

      {/* 정보 카드 */}
      {nurseFilter && (
        <div style={{
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          padding: '16px',
          marginTop: '20px',
          fontSize: '14px',
          color: '#475569'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '8px' }}>
            🔍 필터 적용됨
          </div>
          <div>
            {nurses.find(n => n.id === nurseFilter)?.name}님의 스케줄만 표시 중입니다.
            전체 스케줄을 보려면 위의 필터를 "전체 간호사"로 변경하세요.
          </div>
        </div>
      )}

      {scheduleData.length === 0 && (
        <div style={{
          background: '#fef3c7',
          border: '1px solid #f59e0b',
          borderRadius: '12px',
          padding: '24px',
          marginTop: '20px',
          textAlign: 'center',
          color: '#92400e'
        }}>
          <div style={{ fontSize: '24px', marginBottom: '12px' }}>📅</div>
          <div style={{ fontWeight: '600', marginBottom: '8px' }}>
            생성된 스케줄이 없습니다
          </div>
          <div style={{ fontSize: '14px' }}>
            설정 페이지에서 병동과 간호사를 등록한 후 스케줄을 생성해주세요.
          </div>
        </div>
      )}
    </div>
  );
};