/**
 * 설정 뷰 컴포넌트
 * Single Responsibility: 초기 설정 UI만 담당
 */

import React, { useState } from 'react';
import { Nurse, Ward } from '../types';
import styles from '../NurseScheduleApp.module.css';

interface SetupViewProps {
  nurses: Nurse[];
  wards: Ward[];
  selectedWard: Ward | null;
  onAddNurse: (name: string, role: Nurse['role'], employment_type: Nurse['employment_type'], experience: number) => void;
  onRemoveNurse: (nurseId: number) => void;
  onSelectWard: (ward: Ward) => void;
  onNavigateToCalendar: () => void;
  onOpenPreCheck: () => void;
  canGenerateSchedule: boolean;
  isLoading: boolean;
}

export const SetupView: React.FC<SetupViewProps> = ({
  nurses,
  wards,
  selectedWard,
  onAddNurse,
  onRemoveNurse,
  onSelectWard,
  onNavigateToCalendar,
  onOpenPreCheck,
  canGenerateSchedule,
  isLoading
}) => {
  const [nurseForm, setNurseForm] = useState({
    name: '',
    role: 'staff_nurse' as Nurse['role'],
    employment_type: 'full_time' as Nurse['employment_type'],
    experience: 1
  });

  const handleAddNurse = (e: React.FormEvent) => {
    e.preventDefault();

    if (!nurseForm.name.trim()) {
      alert('간호사 이름을 입력해주세요.');
      return;
    }

    onAddNurse(
      nurseForm.name.trim(),
      nurseForm.role,
      nurseForm.employment_type,
      nurseForm.experience
    );

    // 폼 초기화
    setNurseForm({
      name: '',
      role: 'staff_nurse',
      employment_type: 'full_time',
      experience: 1
    });
  };

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

  return (
    <div className={styles.setupContainer}>
      {/* 병동 선택 섹션 */}
      <div className={styles.formSection}>
        <h2>🏥 병동 선택</h2>
        <div className={styles.wardList}>
          {wards.map(ward => (
            <div
              key={ward.id}
              className={`${styles.wardItem} ${
                selectedWard?.id === ward.id ? styles.wardItemSelected : ''
              }`}
              onClick={() => onSelectWard(ward)}
            >
              <h3>{ward.name}</h3>
              <p>최소 인력: {ward.min_nurses_per_shift}명/교대</p>
              <p>근무 형태: {ward.shift_types.join(', ')}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 간호사 등록 섹션 */}
      <div className={styles.formSection}>
        <h2>👩‍⚕️ 간호사 등록</h2>

        <form onSubmit={handleAddNurse}>
          <div className={styles.formGroup}>
            <label>이름</label>
            <input
              type="text"
              value={nurseForm.name}
              onChange={(e) => setNurseForm({ ...nurseForm, name: e.target.value })}
              className={styles.formInput}
              placeholder="간호사 이름을 입력하세요"
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label>역할</label>
            <select
              value={nurseForm.role}
              onChange={(e) => setNurseForm({ ...nurseForm, role: e.target.value as Nurse['role'] })}
              className={styles.formSelect}
            >
              <option value="head_nurse">수간호사</option>
              <option value="staff_nurse">간호사</option>
              <option value="new_nurse">신입간호사</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label>고용 형태</label>
            <select
              value={nurseForm.employment_type}
              onChange={(e) => setNurseForm({ ...nurseForm, employment_type: e.target.value as Nurse['employment_type'] })}
              className={styles.formSelect}
            >
              <option value="full_time">정규직</option>
              <option value="part_time">비정규직</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label>경력 (년)</label>
            <input
              type="number"
              min="0"
              max="40"
              value={nurseForm.experience}
              onChange={(e) => setNurseForm({ ...nurseForm, experience: parseInt(e.target.value) || 1 })}
              className={styles.formInput}
            />
          </div>

          <button type="submit" className={styles.secondaryButton}>
            간호사 추가
          </button>
        </form>
      </div>

      {/* 등록된 간호사 목록 */}
      {nurses.length > 0 && (
        <div className={styles.formSection}>
          <h2>등록된 간호사 ({nurses.length}명)</h2>
          <div className={styles.nurseList}>
            {nurses.map(nurse => (
              <div key={nurse.id} className={styles.nurseItem}>
                <div className={styles.nurseInfo}>
                  <h4>{nurse.name}</h4>
                  <p>
                    {getRoleDisplayName(nurse.role)} •
                    {getEmploymentTypeDisplayName(nurse.employment_type)} •
                    경력 {nurse.experience_level}년
                  </p>
                </div>
                <button
                  className={styles.deleteButton}
                  onClick={() => onRemoveNurse(nurse.id)}
                >
                  삭제
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 액션 버튼들 */}
      <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
        {nurses.length > 0 && (
          <button
            className={styles.secondaryButton}
            onClick={onNavigateToCalendar}
          >
            📅 스케줄 보기
          </button>
        )}

        <button
          className={styles.primaryButton}
          onClick={onOpenPreCheck}
          disabled={!canGenerateSchedule || isLoading}
        >
          {isLoading ? (
            <>
              <div className={styles.loadingSpinner}></div>
              생성 중...
            </>
          ) : (
            '🎯 스케줄 생성'
          )}
        </button>
      </div>

      {/* 안내 메시지 */}
      {selectedWard && (
        <div style={{
          background: '#f0f9ff',
          border: '1px solid #0ea5e9',
          borderRadius: '8px',
          padding: '16px',
          marginTop: '20px',
          fontSize: '14px',
          color: '#0c4a6e'
        }}>
          <strong>💡 안내:</strong><br />
          • {selectedWard.name} 선택됨<br />
          • 최소 {selectedWard.min_nurses_per_shift * selectedWard.shift_types.length}명의 간호사가 필요합니다<br />
          • 현재 등록된 간호사: {nurses.length}명<br />
          • 근무 형태: {selectedWard.shift_types.join(', ')}
        </div>
      )}
    </div>
  );
};