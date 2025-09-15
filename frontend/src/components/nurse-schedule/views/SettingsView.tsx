/**
 * 설정 뷰 컴포넌트
 * Single Responsibility: 설정 화면 UI만 담당
 */

import React from 'react';
import { Nurse, Ward } from '../types';
import styles from '../NurseScheduleApp.module.css';

interface SettingsViewProps {
  nurses: Nurse[];
  selectedWard: Ward | null;
  onNavigateToCalendar: () => void;
  onNavigateToSetup: () => void;
  onToggleNotifications: () => void;
  showNotifications: boolean;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  nurses,
  selectedWard,
  onNavigateToCalendar,
  onNavigateToSetup,
  onToggleNotifications,
  showNotifications
}) => {
  const getRoleDisplayName = (role: Nurse['role']): string => {
    switch (role) {
      case 'head_nurse': return '수간호사';
      case 'staff_nurse': return '간호사';
      case 'new_nurse': return '신입간호사';
      default: return role;
    }
  };

  const getEmploymentTypeDisplayName = (type: Nurse['employment_type']): string => {
    switch (type) {
      case 'full_time': return '정규직';
      case 'part_time': return '비정규직';
      default: return type;
    }
  };

  const getRoleStats = () => {
    const stats = {
      head_nurse: 0,
      staff_nurse: 0,
      new_nurse: 0,
      full_time: 0,
      part_time: 0
    };

    nurses.forEach(nurse => {
      stats[nurse.role]++;
      stats[nurse.employment_type]++;
    });

    return stats;
  };

  const stats = getRoleStats();

  return (
    <div className={styles.settingsContainer}>
      {/* 헤더 */}
      <div className={styles.calendarHeader}>
        <button
          className={styles.navButton}
          onClick={onNavigateToCalendar}
        >
          ← 달력
        </button>
        <h1>⚙️ 설정</h1>
      </div>

      {/* 병동 정보 섹션 */}
      <div className={styles.settingsSection}>
        <h2>🏥 병동 정보</h2>
        {selectedWard ? (
          <div className={styles.currentWardInfo}>
            <h3>{selectedWard.name}</h3>
            <p>최소 인력: {selectedWard.min_nurses_per_shift}명/교대</p>
            <p>근무 형태: {selectedWard.shift_types.join(', ')}</p>
            <p>총 필요 인력: {selectedWard.min_nurses_per_shift * selectedWard.shift_types.length}명 이상</p>
          </div>
        ) : (
          <div style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '16px',
            color: '#991b1b'
          }}>
            <strong>⚠️ 병동이 선택되지 않았습니다</strong>
            <p>설정 페이지에서 병동을 먼저 선택해주세요.</p>
          </div>
        )}
      </div>

      {/* 간호사 통계 섹션 */}
      <div className={styles.settingsSection}>
        <h2>👥 간호사 현황 ({nurses.length}명)</h2>

        {nurses.length > 0 ? (
          <>
            {/* 통계 카드들 */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
              marginBottom: '24px'
            }}>
              <div style={{
                background: '#f0f9ff',
                border: '1px solid #0ea5e9',
                borderRadius: '8px',
                padding: '16px'
              }}>
                <h4 style={{ margin: '0 0 8px 0', color: '#0c4a6e' }}>역할별 현황</h4>
                <p>수간호사: {stats.head_nurse}명</p>
                <p>간호사: {stats.staff_nurse}명</p>
                <p>신입간호사: {stats.new_nurse}명</p>
              </div>

              <div style={{
                background: '#f0fdf4',
                border: '1px solid #22c55e',
                borderRadius: '8px',
                padding: '16px'
              }}>
                <h4 style={{ margin: '0 0 8px 0', color: '#15803d' }}>고용 형태별 현황</h4>
                <p>정규직: {stats.full_time}명</p>
                <p>비정규직: {stats.part_time}명</p>
              </div>
            </div>

            {/* 간호사 목록 */}
            <h3>등록된 간호사 목록</h3>
            <div className={styles.nurseSummary}>
              {nurses.map(nurse => (
                <div key={nurse.id} className={styles.nurseSummaryItem}>
                  <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                    {nurse.name}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {getRoleDisplayName(nurse.role)} •
                    {getEmploymentTypeDisplayName(nurse.employment_type)} •
                    경력 {nurse.experience_level}년
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{
            background: '#fefce8',
            border: '1px solid #eab308',
            borderRadius: '8px',
            padding: '16px',
            textAlign: 'center',
            color: '#92400e'
          }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>👩‍⚕️</div>
            <div style={{ fontWeight: '600', marginBottom: '8px' }}>
              등록된 간호사가 없습니다
            </div>
            <div style={{ fontSize: '14px' }}>
              설정 페이지에서 간호사를 등록해주세요.
            </div>
          </div>
        )}
      </div>

      {/* 알림 설정 섹션 */}
      <div className={styles.settingsSection}>
        <h2>🔔 알림 설정</h2>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px',
          background: 'white',
          borderRadius: '8px',
          border: '1px solid #e5e5e7'
        }}>
          <div>
            <h4 style={{ margin: '0 0 4px 0' }}>푸시 알림</h4>
            <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
              스케줄 변경 및 중요 공지사항 알림
            </p>
          </div>
          <button
            onClick={onToggleNotifications}
            style={{
              background: showNotifications ? '#22c55e' : '#e5e5e7',
              border: 'none',
              borderRadius: '20px',
              width: '50px',
              height: '28px',
              cursor: 'pointer',
              position: 'relative',
              transition: 'background-color 0.2s'
            }}
          >
            <div
              style={{
                position: 'absolute',
                top: '2px',
                left: showNotifications ? '24px' : '2px',
                width: '24px',
                height: '24px',
                background: 'white',
                borderRadius: '50%',
                transition: 'left 0.2s',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            />
          </button>
        </div>
      </div>

      {/* 시스템 정보 섹션 */}
      <div className={styles.settingsSection}>
        <h2>ℹ️ 시스템 정보</h2>
        <div style={{
          background: 'white',
          border: '1px solid #e5e5e7',
          borderRadius: '8px',
          padding: '16px'
        }}>
          <p><strong>버전:</strong> 1.0.0</p>
          <p><strong>마지막 업데이트:</strong> 2024년 12월</p>
          <p><strong>개발팀:</strong> 간호사 스케줄링 최적화팀</p>
        </div>
      </div>

      {/* 액션 버튼들 */}
      <div className={styles.settingsActions}>
        <button
          className={styles.primaryButton}
          onClick={onNavigateToSetup}
        >
          📝 병동 및 간호사 관리
        </button>

        <button
          className={styles.secondaryButton}
          onClick={onNavigateToCalendar}
        >
          📅 스케줄 보기
        </button>
      </div>

      {/* 권장사항 섹션 */}
      {selectedWard && nurses.length > 0 && (
        <div className={styles.settingsSection}>
          <h2>💡 권장사항</h2>
          <div style={{
            background: '#f0f9ff',
            border: '1px solid #0ea5e9',
            borderRadius: '8px',
            padding: '16px',
            fontSize: '14px',
            color: '#0c4a6e'
          }}>
            {selectedWard.min_nurses_per_shift * selectedWard.shift_types.length > nurses.length && (
              <p>• 최적의 스케줄링을 위해 {selectedWard.min_nurses_per_shift * selectedWard.shift_types.length - nurses.length}명의 간호사를 추가로 등록하는 것을 권장합니다.</p>
            )}

            {stats.head_nurse === 0 && nurses.length > 5 && (
              <p>• 효율적인 병동 관리를 위해 수간호사 1명 이상 등록을 권장합니다.</p>
            )}

            {stats.new_nurse > stats.staff_nurse && stats.staff_nurse < 2 && (
              <p>• 신입간호사 대비 경력간호사 비율을 조정하여 안정적인 근무 환경을 조성하는 것을 권장합니다.</p>
            )}

            {stats.full_time < selectedWard.min_nurses_per_shift * 2 && (
              <p>• 안정적인 스케줄링을 위해 정규직 간호사 비율을 늘리는 것을 권장합니다.</p>
            )}

            {selectedWard.min_nurses_per_shift * selectedWard.shift_types.length <= nurses.length &&
             stats.head_nurse > 0 &&
             stats.full_time >= selectedWard.min_nurses_per_shift * 2 && (
              <p>✅ 현재 설정이 최적화되어 있습니다! 스케줄을 생성해보세요.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};