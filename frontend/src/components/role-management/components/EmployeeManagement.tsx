/**
 * Employee Management Component
 * Single Responsibility: Employee UI and interaction handling
 * Open/Closed: Easy to extend with new employee UI features
 * Interface Segregation: Clean props interface for employee management
 * Dependency Inversion: Depends on useEmployees hook abstraction
 */

import React from 'react';
import { useEmployees, UseEmployeesReturn } from '../hooks/useEmployees';

interface EmployeeManagementProps {
  wardId: number;
  isVisible: boolean;
}

const EmployeeManagement: React.FC<EmployeeManagementProps> = ({ wardId, isVisible }) => {
  const employees = useEmployees(wardId);

  if (!isVisible) return null;

  return (
    <div className="employees-section">
      <EmployeeHeader employees={employees} />
      
      {employees.state.showForm && employees.state.selectedEmployee && (
        <EmployeeForm employees={employees} />
      )}
      
      <EmployeeGrid employees={employees} />
    </div>
  );
};

interface EmployeeComponentProps {
  employees: UseEmployeesReturn;
}

const EmployeeHeader: React.FC<EmployeeComponentProps> = ({ employees }) => (
  <div className="section-header">
    <h3>직원 목록 ({employees.state.employees.length}명)</h3>
  </div>
);

const EmployeeForm: React.FC<EmployeeComponentProps> = ({ employees }) => {
  const { state, actions } = employees;
  const { selectedEmployee, formData, loading } = state;
  const { updateEmployee, setFormData, resetForm } = actions;

  if (!selectedEmployee) return null;

  return (
    <div className="employee-form">
      <h3>직원 역할 정보 수정: {selectedEmployee.employee_name}</h3>
      
      <div className="form-grid">
        <div className="form-group">
          <label>역할</label>
          <select
            value={formData.role || ''}
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
          <label>고용형태</label>
          <select
            value={formData.employment_type || ''}
            onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
          >
            <option value="full_time">정규직</option>
            <option value="part_time">시간제</option>
          </select>
        </div>

        <div className="form-group">
          <label>주간 최대 근무시간</label>
          <input
            type="number"
            min="0"
            max="60"
            value={formData.max_hours_per_week || 40}
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
            value={formData.max_days_per_week || 5}
            onChange={(e) => setFormData({ 
              ...formData, 
              max_days_per_week: parseInt(e.target.value) 
            })}
          />
        </div>

        <div className="form-group full-width">
          <label>전문 분야</label>
          <input
            type="text"
            value={formData.specialization || ''}
            onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
            placeholder="ICU, ER, 소아과 등"
          />
        </div>
      </div>

      <div className="checkbox-section">
        <label>
          <input
            type="checkbox"
            checked={formData.can_work_alone || false}
            onChange={(e) => setFormData({ 
              ...formData, 
              can_work_alone: e.target.checked 
            })}
          />
          단독 근무 가능
        </label>
        <label>
          <input
            type="checkbox"
            checked={formData.requires_supervision || false}
            onChange={(e) => setFormData({ 
              ...formData, 
              requires_supervision: e.target.checked 
            })}
          />
          감독 필요
        </label>
        <label>
          <input
            type="checkbox"
            checked={formData.can_supervise || false}
            onChange={(e) => setFormData({ 
              ...formData, 
              can_supervise: e.target.checked 
            })}
          />
          감독 가능
        </label>
      </div>

      <div className="form-actions">
        <button onClick={updateEmployee} className="btn-primary" disabled={loading}>
          {loading ? '저장 중...' : '저장'}
        </button>
        <button onClick={resetForm} className="btn-secondary">
          취소
        </button>
      </div>
    </div>
  );
};

const EmployeeGrid: React.FC<EmployeeComponentProps> = ({ employees }) => {
  const { state, actions, utils } = employees;
  const { employees: employeeList } = state;
  const { selectEmployee } = actions;
  const { getRoleDisplayName, getEmploymentTypeDisplayName } = utils;

  return (
    <div className="employees-grid">
      {employeeList.map((employee) => (
        <div key={employee.employee_id} className="employee-card">
          <div className="employee-header">
            <h4>{employee.employee_name}</h4>
            <div className="employee-badges">
              <span className={`badge role-${employee.role}`}>
                {getRoleDisplayName(employee.role)}
              </span>
              <span className={`badge employment-${employee.employment_type}`}>
                {getEmploymentTypeDisplayName(employee.employment_type)}
              </span>
            </div>
          </div>

          <div className="employee-details">
            <div className="detail-row">
              <span>경력:</span> <strong>{employee.years_experience}년</strong>
            </div>
            <div className="detail-row">
              <span>숙련도:</span> <strong>{employee.skill_level}/5</strong>
            </div>
            <div className="detail-row">
              <span>주간 최대:</span> <strong>{employee.max_hours_per_week}시간</strong>
            </div>
            {employee.specialization && (
              <div className="detail-row">
                <span>전문분야:</span> <strong>{employee.specialization}</strong>
              </div>
            )}
          </div>

          <div className="employee-capabilities">
            {employee.can_work_alone && (
              <span className="capability">🏠 단독근무</span>
            )}
            {employee.can_supervise && (
              <span className="capability">👨‍🏫 감독가능</span>
            )}
            {employee.requires_supervision && (
              <span className="capability warning">⚠️ 감독필요</span>
            )}
          </div>

          <div className="employee-actions">
            <button 
              onClick={() => selectEmployee(employee)}
              className="btn-edit"
            >
              수정
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default EmployeeManagement;