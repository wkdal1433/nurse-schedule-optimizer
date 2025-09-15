/**
 * Constraint Management Component
 * Single Responsibility: Constraint UI and interaction handling
 * Open/Closed: Easy to extend with new constraint UI features
 * Interface Segregation: Clean props interface for constraint management
 * Dependency Inversion: Depends on useConstraints hook abstraction
 */

import React from 'react';
import { useConstraints, UseConstraintsReturn } from '../hooks/useConstraints';

interface ConstraintManagementProps {
  wardId: number;
  isVisible: boolean;
}

const ConstraintManagement: React.FC<ConstraintManagementProps> = ({ wardId, isVisible }) => {
  const constraints = useConstraints(wardId);

  if (!isVisible) return null;

  return (
    <div className="constraints-section">
      <ConstraintHeader constraints={constraints} />
      
      {constraints.state.showForm && (
        <ConstraintForm constraints={constraints} />
      )}
      
      <ConstraintGrid constraints={constraints} />
    </div>
  );
};

interface ConstraintComponentProps {
  constraints: UseConstraintsReturn;
}

const ConstraintHeader: React.FC<ConstraintComponentProps> = ({ constraints }) => {
  const { state, actions } = constraints;
  const { setShowForm } = actions;
  const { showForm, constraints: constraintList } = state;

  return (
    <div className="section-header">
      <h3>역할별 제약조건 ({constraintList.length}개)</h3>
      <button 
        onClick={() => setShowForm(!showForm)}
        className="btn-primary"
      >
        {showForm ? '취소' : '새 제약조건'}
      </button>
    </div>
  );
};

const ConstraintForm: React.FC<ConstraintComponentProps> = ({ constraints }) => {
  const { state, actions } = constraints;
  const { formData, loading } = state;
  const { createConstraint, setFormData, resetForm, updateArrayField } = actions;

  return (
    <div className="constraint-form">
      <h3>새 역할 제약조건</h3>
      
      <div className="form-grid">
        <div className="form-group">
          <label>역할</label>
          <select
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          >
            <option value="head_nurse">수간호사</option>
            <option value="charge_nurse">책임간호사</option>
            <option value="staff_nurse">일반간호사</option>
            <option value="new_nurse">신입간호사</option>
            <option value="education_coordinator">교육담당자</option>
          </select>
        </div>

        <div className="form-group">
          <label>최소 인원</label>
          <input
            type="number"
            min="0"
            value={formData.min_per_shift}
            onChange={(e) => setFormData({ 
              ...formData, 
              min_per_shift: parseInt(e.target.value) 
            })}
          />
        </div>

        <div className="form-group">
          <label>최대 인원</label>
          <input
            type="number"
            min="1"
            value={formData.max_per_shift}
            onChange={(e) => setFormData({ 
              ...formData, 
              max_per_shift: parseInt(e.target.value) 
            })}
          />
        </div>

        <div className="form-group">
          <label>허용 근무시간 (콤마로 구분)</label>
          <input
            type="text"
            value={formData.allowed_shifts.join(', ')}
            onChange={(e) => updateArrayField('allowed_shifts', e.target.value)}
            placeholder="day, evening, night"
          />
        </div>

        <div className="form-group">
          <label>금지 근무시간</label>
          <input
            type="text"
            value={formData.forbidden_shifts.join(', ')}
            onChange={(e) => updateArrayField('forbidden_shifts', e.target.value)}
            placeholder="night"
          />
        </div>

        <div className="form-group">
          <label>필요한 역할 (함께 근무)</label>
          <input
            type="text"
            value={formData.requires_pairing_with_roles.join(', ')}
            onChange={(e) => updateArrayField('requires_pairing_with_roles', e.target.value)}
            placeholder="staff_nurse, head_nurse"
          />
        </div>
      </div>

      <div className="checkbox-section">
        <label>
          <input
            type="checkbox"
            checked={formData.must_have_supervisor}
            onChange={(e) => setFormData({ 
              ...formData, 
              must_have_supervisor: e.target.checked 
            })}
          />
          감독자 필수
        </label>
        <label>
          <input
            type="checkbox"
            checked={formData.can_be_sole_charge}
            onChange={(e) => setFormData({ 
              ...formData, 
              can_be_sole_charge: e.target.checked 
            })}
          />
          단독 책임자 가능
        </label>
      </div>

      <div className="form-actions">
        <button onClick={createConstraint} className="btn-primary" disabled={loading}>
          {loading ? '생성 중...' : '생성'}
        </button>
        <button onClick={resetForm} className="btn-secondary">
          취소
        </button>
      </div>
    </div>
  );
};

const ConstraintGrid: React.FC<ConstraintComponentProps> = ({ constraints }) => {
  const { state, utils } = constraints;
  const { constraints: constraintList } = state;
  const { getRoleDisplayName } = utils;

  return (
    <div className="constraints-grid">
      {constraintList.map((constraint) => (
        <div key={constraint.id} className="constraint-card">
          <div className="constraint-header">
            <h4>{getRoleDisplayName(constraint.role)}</h4>
            <div className="constraint-badge">
              {constraint.min_per_shift}-{constraint.max_per_shift}명
            </div>
          </div>

          <div className="constraint-details">
            <div className="detail-row">
              <span>허용 근무:</span>
              <strong>{constraint.allowed_shifts.join(', ')}</strong>
            </div>
            {constraint.forbidden_shifts.length > 0 && (
              <div className="detail-row">
                <span>금지 근무:</span>
                <strong>{constraint.forbidden_shifts.join(', ')}</strong>
              </div>
            )}
            {constraint.requires_pairing_with_roles.length > 0 && (
              <div className="detail-row">
                <span>필요 역할:</span>
                <strong>{constraint.requires_pairing_with_roles.join(', ')}</strong>
              </div>
            )}
          </div>

          <div className="constraint-flags">
            {constraint.must_have_supervisor && (
              <span className="flag supervisor">👨‍🏫 감독자 필수</span>
            )}
            {constraint.can_be_sole_charge && (
              <span className="flag charge">⭐ 단독책임자</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ConstraintManagement;