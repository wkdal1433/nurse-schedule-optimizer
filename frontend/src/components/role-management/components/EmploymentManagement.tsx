/**
 * Employment Management Component
 * Single Responsibility: Employment rule UI and interaction handling
 * Open/Closed: Easy to extend with new employment UI features
 * Interface Segregation: Clean props interface for employment management
 * Dependency Inversion: Depends on useEmployment hook abstraction
 */

import React from 'react';
import { useEmployment, UseEmploymentReturn } from '../hooks/useEmployment';

interface EmploymentManagementProps {
  wardId: number;
  isVisible: boolean;
}

const EmploymentManagement: React.FC<EmploymentManagementProps> = ({ wardId, isVisible }) => {
  const employment = useEmployment(wardId);

  if (!isVisible) return null;

  return (
    <div className="employment-section">
      <EmploymentHeader employment={employment} />
      
      {employment.state.showForm && (
        <EmploymentForm employment={employment} />
      )}
      
      <EmploymentGrid employment={employment} />
    </div>
  );
};

interface EmploymentComponentProps {
  employment: UseEmploymentReturn;
}

const EmploymentHeader: React.FC<EmploymentComponentProps> = ({ employment }) => {
  const { state, actions } = employment;
  const { setShowForm } = actions;
  const { showForm, rules } = state;

  return (
    <div className="section-header">
      <h3>고용형태별 규칙 ({rules.length}개)</h3>
      <button 
        onClick={() => setShowForm(!showForm)}
        className="btn-primary"
      >
        {showForm ? '취소' : '새 규칙'}
      </button>
    </div>
  );
};

const EmploymentForm: React.FC<EmploymentComponentProps> = ({ employment }) => {
  const { state, actions } = employment;
  const { formData, loading } = state;
  const { createRule, setFormData, resetForm, updateArrayField } = actions;

  return (
    <div className="employment-form">
      <h3>새 고용형태 규칙</h3>
      
      <div className="form-grid">
        <div className="form-group">
          <label>고용형태</label>
          <select
            value={formData.employment_type}
            onChange={(e) => setFormData({ 
              ...formData, 
              employment_type: e.target.value 
            })}
          >
            <option value="full_time">정규직</option>
            <option value="part_time">시간제</option>
          </select>
        </div>

        <div className="form-group">
          <label>일일 최대 시간</label>
          <input
            type="number"
            min="1"
            max="12"
            value={formData.max_hours_per_day}
            onChange={(e) => setFormData({ 
              ...formData, 
              max_hours_per_day: parseInt(e.target.value) 
            })}
          />
        </div>

        <div className="form-group">
          <label>주간 최대 시간</label>
          <input
            type="number"
            min="1"
            max="60"
            value={formData.max_hours_per_week}
            onChange={(e) => setFormData({ 
              ...formData, 
              max_hours_per_week: parseInt(e.target.value) 
            })}
          />
        </div>

        <div className="form-group">
          <label>주간 최대 근무일</label>
          <input
            type="number"
            min="1"
            max="7"
            value={formData.max_days_per_week}
            onChange={(e) => setFormData({ 
              ...formData, 
              max_days_per_week: parseInt(e.target.value) 
            })}
          />
        </div>

        <div className="form-group">
          <label>최대 연속 근무일</label>
          <input
            type="number"
            min="1"
            max="10"
            value={formData.max_consecutive_days}
            onChange={(e) => setFormData({ 
              ...formData, 
              max_consecutive_days: parseInt(e.target.value) 
            })}
          />
        </div>

        <div className="form-group">
          <label>허용 근무시간</label>
          <input
            type="text"
            value={formData.allowed_shift_types.join(', ')}
            onChange={(e) => updateArrayField('allowed_shift_types', e.target.value)}
            placeholder="day, evening, night"
          />
        </div>

        <div className="form-group">
          <label>스케줄링 우선순위</label>
          <input
            type="number"
            min="1"
            max="10"
            value={formData.scheduling_priority}
            onChange={(e) => setFormData({ 
              ...formData, 
              scheduling_priority: parseInt(e.target.value) 
            })}
          />
          <small>1=최우선, 10=최후순</small>
        </div>
      </div>

      <div className="checkbox-section">
        <label>
          <input
            type="checkbox"
            checked={formData.weekend_work_allowed}
            onChange={(e) => setFormData({ 
              ...formData, 
              weekend_work_allowed: e.target.checked 
            })}
          />
          주말 근무 허용
        </label>
        <label>
          <input
            type="checkbox"
            checked={formData.night_shift_allowed}
            onChange={(e) => setFormData({ 
              ...formData, 
              night_shift_allowed: e.target.checked 
            })}
          />
          야간 근무 허용
        </label>
        <label>
          <input
            type="checkbox"
            checked={formData.holiday_work_allowed}
            onChange={(e) => setFormData({ 
              ...formData, 
              holiday_work_allowed: e.target.checked 
            })}
          />
          휴일 근무 허용
        </label>
      </div>

      <div className="form-actions">
        <button onClick={createRule} className="btn-primary" disabled={loading}>
          {loading ? '생성 중...' : '생성'}
        </button>
        <button onClick={resetForm} className="btn-secondary">
          취소
        </button>
      </div>
    </div>
  );
};

const EmploymentGrid: React.FC<EmploymentComponentProps> = ({ employment }) => {
  const { state, utils } = employment;
  const { rules } = state;
  const { getEmploymentTypeDisplayName } = utils;

  return (
    <div className="employment-grid">
      {rules.map((rule) => (
        <div key={rule.id} className="employment-card">
          <div className="employment-header">
            <h4>{getEmploymentTypeDisplayName(rule.employment_type)}</h4>
            <div className="priority-badge">우선순위 {rule.scheduling_priority}</div>
          </div>

          <div className="employment-limits">
            <div className="limit-item">
              <span>일일:</span> <strong>{rule.max_hours_per_day}시간</strong>
            </div>
            <div className="limit-item">
              <span>주간:</span> <strong>{rule.max_hours_per_week}시간</strong>
            </div>
            <div className="limit-item">
              <span>주간 근무일:</span> <strong>{rule.max_days_per_week}일</strong>
            </div>
            <div className="limit-item">
              <span>연속 근무:</span> <strong>{rule.max_consecutive_days}일</strong>
            </div>
          </div>

          <div className="employment-permissions">
            <div className="permission-item">
              <span>허용 시간:</span>
              <strong>{rule.allowed_shift_types.join(', ')}</strong>
            </div>
            <div className="permission-flags">
              {rule.weekend_work_allowed && (
                <span className="flag allowed">🌅 주말</span>
              )}
              {rule.night_shift_allowed && (
                <span className="flag allowed">🌙 야간</span>
              )}
              {rule.holiday_work_allowed && (
                <span className="flag allowed">🎉 휴일</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default EmploymentManagement;