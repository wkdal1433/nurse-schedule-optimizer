/**
 * Supervision Management Component
 * Single Responsibility: Supervision UI and interaction handling
 * Open/Closed: Easy to extend with new supervision UI features
 * Interface Segregation: Clean props interface for supervision management
 * Dependency Inversion: Depends on useSupervision hook abstraction
 */

import React from 'react';
import { useSupervision, UseSupervisionReturn } from '../hooks/useSupervision';
import { useEmployees } from '../hooks/useEmployees';

interface SupervisionManagementProps {
  wardId: number;
  isVisible: boolean;
}

const SupervisionManagement: React.FC<SupervisionManagementProps> = ({ wardId, isVisible }) => {
  const supervision = useSupervision(wardId);
  const employees = useEmployees(wardId);

  if (!isVisible) return null;

  return (
    <div className="supervision-section">
      <SupervisionHeader supervision={supervision} />
      
      {supervision.state.showForm && (
        <SupervisionForm supervision={supervision} employees={employees} />
      )}
      
      <SupervisionGrid supervision={supervision} />
    </div>
  );
};

interface SupervisionComponentProps {
  supervision: UseSupervisionReturn;
  employees?: any; // Using any for now to avoid circular dependency
}

const SupervisionHeader: React.FC<Pick<SupervisionComponentProps, 'supervision'>> = ({ supervision }) => {
  const { state, actions } = supervision;
  const { setShowForm } = actions;
  const { showForm, pairs } = state;

  return (
    <div className="section-header">
      <h3>감독 페어 ({pairs.length}개)</h3>
      <button 
        onClick={() => setShowForm(!showForm)}
        className="btn-primary"
      >
        {showForm ? '취소' : '새 페어 생성'}
      </button>
    </div>
  );
};

const SupervisionForm: React.FC<SupervisionComponentProps> = ({ supervision, employees }) => {
  const { state, actions, utils } = supervision;
  const { formData, loading } = state;
  const { createPair, setFormData, resetForm } = actions;
  const { getRoleDisplayName, getSupervisors, getSupervisees } = utils;

  const supervisors = getSupervisors(employees?.state.employees || []);
  const supervisees = getSupervisees(employees?.state.employees || []);

  return (
    <div className="pair-form">
      <h3>새 감독 페어</h3>
      
      <div className="form-grid">
        <div className="form-group">
          <label>감독자</label>
          <select
            value={formData.supervisor_id}
            onChange={(e) => setFormData({ 
              ...formData, 
              supervisor_id: parseInt(e.target.value) 
            })}
          >
            <option value={0}>감독자 선택</option>
            {supervisors.map(emp => (
              <option key={emp.employee_id} value={emp.employee_id}>
                {emp.employee_name} ({getRoleDisplayName(emp.role)})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>피감독자</label>
          <select
            value={formData.supervisee_id}
            onChange={(e) => setFormData({ 
              ...formData, 
              supervisee_id: parseInt(e.target.value) 
            })}
          >
            <option value={0}>피감독자 선택</option>
            {supervisees.map(emp => (
              <option key={emp.employee_id} value={emp.employee_id}>
                {emp.employee_name} ({getRoleDisplayName(emp.role)})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>페어링 유형</label>
          <select
            value={formData.pairing_type}
            onChange={(e) => setFormData({ ...formData, pairing_type: e.target.value })}
          >
            <option value="mentor">멘토</option>
            <option value="buddy">버디</option>
            <option value="preceptor">프리셉터</option>
          </select>
        </div>

        <div className="form-group">
          <label>종료 날짜 (선택사항)</label>
          <input
            type="date"
            value={formData.end_date}
            onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
          />
        </div>
      </div>

      <div className="form-actions">
        <button onClick={createPair} className="btn-primary" disabled={loading}>
          {loading ? '생성 중...' : '생성'}
        </button>
        <button onClick={resetForm} className="btn-secondary">
          취소
        </button>
      </div>
    </div>
  );
};

const SupervisionGrid: React.FC<Pick<SupervisionComponentProps, 'supervision'>> = ({ supervision }) => {
  const { state, actions, utils } = supervision;
  const { pairs } = state;
  const { deactivatePair } = actions;
  const { getRoleDisplayName } = utils;

  return (
    <div className="pairs-grid">
      {pairs.map((pair) => (
        <div key={pair.id} className="pair-card">
          <div className="pair-header">
            <h4>👨‍🏫 {pair.pairing_type}</h4>
            <span className={`status ${pair.is_active ? 'active' : 'inactive'}`}>
              {pair.is_active ? '활성' : '비활성'}
            </span>
          </div>

          <div className="pair-members">
            <div className="member supervisor">
              <strong>감독자:</strong> {pair.supervisor.name}
              <span className="role">({getRoleDisplayName(pair.supervisor.role)})</span>
            </div>
            <div className="member supervisee">
              <strong>피감독자:</strong> {pair.supervisee.name}
              <span className="role">({getRoleDisplayName(pair.supervisee.role)})</span>
            </div>
          </div>

          <div className="pair-dates">
            <div>시작: {new Date(pair.start_date).toLocaleDateString('ko-KR')}</div>
            {pair.end_date && (
              <div>종료: {new Date(pair.end_date).toLocaleDateString('ko-KR')}</div>
            )}
          </div>

          {pair.is_active && (
            <div className="pair-actions">
              <button 
                onClick={() => deactivatePair(pair.id!)}
                className="btn-danger"
              >
                비활성화
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default SupervisionManagement;