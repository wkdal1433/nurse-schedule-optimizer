import React, { useState, useEffect } from 'react';
import { rolesAPI, EmployeeRoleInfo, RoleConstraint, SupervisionPair, EmploymentTypeRule } from '../services/api';

interface RoleManagementProps {
  wardId?: number;
}

const RoleManagement: React.FC<RoleManagementProps> = ({ wardId = 1 }) => {
  const [activeTab, setActiveTab] = useState<'employees' | 'constraints' | 'supervision' | 'employment'>('employees');
  const [loading, setLoading] = useState(false);

  // 직원 관련 상태
  const [employees, setEmployees] = useState<EmployeeRoleInfo[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeRoleInfo | null>(null);
  const [showEmployeeForm, setShowEmployeeForm] = useState(false);

  // 제약조건 관련 상태
  const [roleConstraints, setRoleConstraints] = useState<RoleConstraint[]>([]);
  const [showConstraintForm, setShowConstraintForm] = useState(false);

  // 감독 페어 관련 상태
  const [supervisionPairs, setSupervisionPairs] = useState<SupervisionPair[]>([]);
  const [showPairForm, setShowPairForm] = useState(false);

  // 고용형태 규칙 관련 상태
  const [employmentRules, setEmploymentRules] = useState<EmploymentTypeRule[]>([]);
  const [showEmploymentForm, setShowEmploymentForm] = useState(false);

  // 폼 데이터
  const [employeeForm, setEmployeeForm] = useState<Partial<EmployeeRoleInfo>>({});
  
  const defaultConstraint: Omit<RoleConstraint, 'id'> = {
    role: 'staff_nurse',
    ward_id: wardId,
    allowed_shifts: ['day', 'evening', 'night'],
    forbidden_shifts: [],
    min_per_shift: 1,
    max_per_shift: 10,
    requires_pairing_with_roles: [],
    cannot_work_with_roles: [],
    must_have_supervisor: false,
    can_be_sole_charge: true
  };

  const [constraintForm, setConstraintForm] = useState(defaultConstraint);

  const [pairForm, setPairForm] = useState({
    supervisor_id: 0,
    supervisee_id: 0,
    pairing_type: 'mentor',
    end_date: ''
  });

  const defaultEmploymentRule: Omit<EmploymentTypeRule, 'id'> = {
    employment_type: 'full_time',
    ward_id: wardId,
    max_hours_per_day: 8,
    max_hours_per_week: 40,
    max_days_per_week: 5,
    max_consecutive_days: 5,
    allowed_shift_types: ['day', 'evening', 'night'],
    forbidden_shift_types: [],
    weekend_work_allowed: true,
    night_shift_allowed: true,
    holiday_work_allowed: true,
    scheduling_priority: 5
  };

  const [employmentForm, setEmploymentForm] = useState(defaultEmploymentRule);

  useEffect(() => {
    if (activeTab === 'employees') {
      loadEmployees();
    } else if (activeTab === 'constraints') {
      loadRoleConstraints();
    } else if (activeTab === 'supervision') {
      loadSupervisionPairs();
    } else if (activeTab === 'employment') {
      loadEmploymentRules();
    }
  }, [activeTab, wardId]);

  const loadEmployees = async () => {
    setLoading(true);
    try {
      const response = await rolesAPI.getEmployeesByWard(wardId);
      setEmployees(response.data);
    } catch (error) {
      console.error('직원 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRoleConstraints = async () => {
    setLoading(true);
    try {
      const response = await rolesAPI.getRoleConstraints(wardId);
      setRoleConstraints(response.data);
    } catch (error) {
      console.error('역할 제약조건 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSupervisionPairs = async () => {
    setLoading(true);
    try {
      const response = await rolesAPI.getSupervisionPairs(wardId);
      setSupervisionPairs(response.data);
    } catch (error) {
      console.error('감독 페어 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadEmploymentRules = async () => {
    setLoading(true);
    try {
      const response = await rolesAPI.getEmploymentTypeRules(undefined, wardId);
      setEmploymentRules(response.data);
    } catch (error) {
      console.error('고용형태 규칙 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateEmployee = async () => {
    if (!selectedEmployee || !employeeForm) return;
    
    setLoading(true);
    try {
      await rolesAPI.updateEmployeeRole(selectedEmployee.employee_id, employeeForm);
      await loadEmployees();
      setShowEmployeeForm(false);
      setSelectedEmployee(null);
      alert('직원 역할 정보가 업데이트되었습니다.');
    } catch (error) {
      console.error('직원 업데이트 실패:', error);
      alert('직원 정보 업데이트에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConstraint = async () => {
    setLoading(true);
    try {
      await rolesAPI.createRoleConstraint(constraintForm);
      await loadRoleConstraints();
      setShowConstraintForm(false);
      setConstraintForm(defaultConstraint);
      alert('역할 제약조건이 생성되었습니다.');
    } catch (error) {
      console.error('제약조건 생성 실패:', error);
      alert('제약조건 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePair = async () => {
    if (pairForm.supervisor_id === 0 || pairForm.supervisee_id === 0) {
      alert('감독자와 피감독자를 모두 선택해주세요.');
      return;
    }

    setLoading(true);
    try {
      await rolesAPI.createSupervisionPair(pairForm);
      await loadSupervisionPairs();
      setShowPairForm(false);
      setPairForm({ supervisor_id: 0, supervisee_id: 0, pairing_type: 'mentor', end_date: '' });
      alert('감독 페어가 생성되었습니다.');
    } catch (error) {
      console.error('감독 페어 생성 실패:', error);
      alert('감독 페어 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEmploymentRule = async () => {
    setLoading(true);
    try {
      await rolesAPI.createEmploymentTypeRule(employmentForm);
      await loadEmploymentRules();
      setShowEmploymentForm(false);
      setEmploymentForm(defaultEmploymentRule);
      alert('고용형태 규칙이 생성되었습니다.');
    } catch (error) {
      console.error('고용형태 규칙 생성 실패:', error);
      alert('고용형태 규칙 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleEditEmployee = (employee: EmployeeRoleInfo) => {
    setSelectedEmployee(employee);
    setEmployeeForm({
      role: employee.role,
      employment_type: employee.employment_type,
      allowed_shifts: employee.allowed_shifts,
      max_hours_per_week: employee.max_hours_per_week,
      max_days_per_week: employee.max_days_per_week,
      can_work_alone: employee.can_work_alone,
      requires_supervision: employee.requires_supervision,
      can_supervise: employee.can_supervise,
      specialization: employee.specialization
    });
    setShowEmployeeForm(true);
  };

  const handleDeactivatePair = async (pairId: number) => {
    if (!confirm('이 감독 페어를 비활성화하시겠습니까?')) return;

    setLoading(true);
    try {
      await rolesAPI.deactivateSupervisionPair(pairId);
      await loadSupervisionPairs();
      alert('감독 페어가 비활성화되었습니다.');
    } catch (error) {
      console.error('감독 페어 비활성화 실패:', error);
      alert('감독 페어 비활성화에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const createDefaultSettings = async () => {
    if (!confirm('기본 역할 설정을 생성하시겠습니까?')) return;

    setLoading(true);
    try {
      await rolesAPI.createDefaultRoleSettings(wardId);
      // 모든 데이터 새로고침
      await Promise.all([
        loadRoleConstraints(),
        loadEmploymentRules()
      ]);
      alert('기본 역할 설정이 생성되었습니다.');
    } catch (error) {
      console.error('기본 설정 생성 실패:', error);
      alert('기본 설정 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const updateArrayField = (field: keyof typeof constraintForm, value: string) => {
    const array = value.split(',').map(s => s.trim()).filter(s => s);
    setConstraintForm({ ...constraintForm, [field]: array });
  };

  const updateEmploymentArrayField = (field: keyof typeof employmentForm, value: string) => {
    const array = value.split(',').map(s => s.trim()).filter(s => s);
    setEmploymentForm({ ...employmentForm, [field]: array });
  };

  const getRoleDisplayName = (role: string) => {
    const roleNames: Record<string, string> = {
      'head_nurse': '수간호사',
      'charge_nurse': '책임간호사',
      'staff_nurse': '일반간호사',
      'new_nurse': '신입간호사',
      'education_coordinator': '교육담당자'
    };
    return roleNames[role] || role;
  };

  const getEmploymentTypeDisplayName = (type: string) => {
    return type === 'full_time' ? '정규직' : '시간제';
  };

  return (
    <div className="role-management">
      <div className="header">
        <h2>👥 역할 & 고용형태 관리</h2>
        <button onClick={createDefaultSettings} className="btn-secondary">
          기본 설정 생성
        </button>
      </div>

      <div className="tabs">
        <button
          className={activeTab === 'employees' ? 'active' : ''}
          onClick={() => setActiveTab('employees')}
        >
          👤 직원 관리
        </button>
        <button
          className={activeTab === 'constraints' ? 'active' : ''}
          onClick={() => setActiveTab('constraints')}
        >
          📋 역할 제약조건
        </button>
        <button
          className={activeTab === 'supervision' ? 'active' : ''}
          onClick={() => setActiveTab('supervision')}
        >
          👥 감독 페어
        </button>
        <button
          className={activeTab === 'employment' ? 'active' : ''}
          onClick={() => setActiveTab('employment')}
        >
          🏢 고용형태 규칙
        </button>
      </div>

      {loading && <div className="loading">로딩 중...</div>}

      {/* 직원 관리 탭 */}
      {activeTab === 'employees' && (
        <div className="employees-section">
          <div className="section-header">
            <h3>직원 목록 ({employees.length}명)</h3>
          </div>

          {showEmployeeForm && selectedEmployee && (
            <div className="employee-form">
              <h3>직원 역할 정보 수정: {selectedEmployee.employee_name}</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label>역할</label>
                  <select
                    value={employeeForm.role || ''}
                    onChange={(e) => setEmployeeForm({ ...employeeForm, role: e.target.value })}
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
                    value={employeeForm.employment_type || ''}
                    onChange={(e) => setEmployeeForm({ ...employeeForm, employment_type: e.target.value })}
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
                    value={employeeForm.max_hours_per_week || 40}
                    onChange={(e) => setEmployeeForm({ 
                      ...employeeForm, 
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
                    value={employeeForm.max_days_per_week || 5}
                    onChange={(e) => setEmployeeForm({ 
                      ...employeeForm, 
                      max_days_per_week: parseInt(e.target.value) 
                    })}
                  />
                </div>

                <div className="form-group full-width">
                  <label>전문 분야</label>
                  <input
                    type="text"
                    value={employeeForm.specialization || ''}
                    onChange={(e) => setEmployeeForm({ ...employeeForm, specialization: e.target.value })}
                    placeholder="ICU, ER, 소아과 등"
                  />
                </div>
              </div>

              <div className="checkbox-section">
                <label>
                  <input
                    type="checkbox"
                    checked={employeeForm.can_work_alone || false}
                    onChange={(e) => setEmployeeForm({ 
                      ...employeeForm, 
                      can_work_alone: e.target.checked 
                    })}
                  />
                  단독 근무 가능
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={employeeForm.requires_supervision || false}
                    onChange={(e) => setEmployeeForm({ 
                      ...employeeForm, 
                      requires_supervision: e.target.checked 
                    })}
                  />
                  감독 필요
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={employeeForm.can_supervise || false}
                    onChange={(e) => setEmployeeForm({ 
                      ...employeeForm, 
                      can_supervise: e.target.checked 
                    })}
                  />
                  감독 가능
                </label>
              </div>

              <div className="form-actions">
                <button onClick={handleUpdateEmployee} className="btn-primary" disabled={loading}>
                  {loading ? '저장 중...' : '저장'}
                </button>
                <button onClick={() => setShowEmployeeForm(false)} className="btn-secondary">
                  취소
                </button>
              </div>
            </div>
          )}

          <div className="employees-grid">
            {employees.map((employee) => (
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
                    onClick={() => handleEditEmployee(employee)}
                    className="btn-edit"
                  >
                    수정
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 역할 제약조건 탭 */}
      {activeTab === 'constraints' && (
        <div className="constraints-section">
          <div className="section-header">
            <h3>역할별 제약조건 ({roleConstraints.length}개)</h3>
            <button 
              onClick={() => setShowConstraintForm(!showConstraintForm)}
              className="btn-primary"
            >
              {showConstraintForm ? '취소' : '새 제약조건'}
            </button>
          </div>

          {showConstraintForm && (
            <div className="constraint-form">
              <h3>새 역할 제약조건</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label>역할</label>
                  <select
                    value={constraintForm.role}
                    onChange={(e) => setConstraintForm({ ...constraintForm, role: e.target.value })}
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
                    value={constraintForm.min_per_shift}
                    onChange={(e) => setConstraintForm({ 
                      ...constraintForm, 
                      min_per_shift: parseInt(e.target.value) 
                    })}
                  />
                </div>

                <div className="form-group">
                  <label>최대 인원</label>
                  <input
                    type="number"
                    min="1"
                    value={constraintForm.max_per_shift}
                    onChange={(e) => setConstraintForm({ 
                      ...constraintForm, 
                      max_per_shift: parseInt(e.target.value) 
                    })}
                  />
                </div>

                <div className="form-group">
                  <label>허용 근무시간 (콤마로 구분)</label>
                  <input
                    type="text"
                    value={constraintForm.allowed_shifts.join(', ')}
                    onChange={(e) => updateArrayField('allowed_shifts', e.target.value)}
                    placeholder="day, evening, night"
                  />
                </div>

                <div className="form-group">
                  <label>금지 근무시간</label>
                  <input
                    type="text"
                    value={constraintForm.forbidden_shifts.join(', ')}
                    onChange={(e) => updateArrayField('forbidden_shifts', e.target.value)}
                    placeholder="night"
                  />
                </div>

                <div className="form-group">
                  <label>필요한 역할 (함께 근무)</label>
                  <input
                    type="text"
                    value={constraintForm.requires_pairing_with_roles.join(', ')}
                    onChange={(e) => updateArrayField('requires_pairing_with_roles', e.target.value)}
                    placeholder="staff_nurse, head_nurse"
                  />
                </div>
              </div>

              <div className="checkbox-section">
                <label>
                  <input
                    type="checkbox"
                    checked={constraintForm.must_have_supervisor}
                    onChange={(e) => setConstraintForm({ 
                      ...constraintForm, 
                      must_have_supervisor: e.target.checked 
                    })}
                  />
                  감독자 필수
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={constraintForm.can_be_sole_charge}
                    onChange={(e) => setConstraintForm({ 
                      ...constraintForm, 
                      can_be_sole_charge: e.target.checked 
                    })}
                  />
                  단독 책임자 가능
                </label>
              </div>

              <div className="form-actions">
                <button onClick={handleCreateConstraint} className="btn-primary" disabled={loading}>
                  {loading ? '생성 중...' : '생성'}
                </button>
                <button 
                  onClick={() => setShowConstraintForm(false)} 
                  className="btn-secondary"
                >
                  취소
                </button>
              </div>
            </div>
          )}

          <div className="constraints-grid">
            {roleConstraints.map((constraint) => (
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
        </div>
      )}

      {/* 감독 페어 탭 */}
      {activeTab === 'supervision' && (
        <div className="supervision-section">
          <div className="section-header">
            <h3>감독 페어 ({supervisionPairs.length}개)</h3>
            <button 
              onClick={() => setShowPairForm(!showPairForm)}
              className="btn-primary"
            >
              {showPairForm ? '취소' : '새 페어 생성'}
            </button>
          </div>

          {showPairForm && (
            <div className="pair-form">
              <h3>새 감독 페어</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label>감독자</label>
                  <select
                    value={pairForm.supervisor_id}
                    onChange={(e) => setPairForm({ 
                      ...pairForm, 
                      supervisor_id: parseInt(e.target.value) 
                    })}
                  >
                    <option value={0}>감독자 선택</option>
                    {employees
                      .filter(emp => emp.can_supervise)
                      .map(emp => (
                        <option key={emp.employee_id} value={emp.employee_id}>
                          {emp.employee_name} ({getRoleDisplayName(emp.role)})
                        </option>
                      ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>피감독자</label>
                  <select
                    value={pairForm.supervisee_id}
                    onChange={(e) => setPairForm({ 
                      ...pairForm, 
                      supervisee_id: parseInt(e.target.value) 
                    })}
                  >
                    <option value={0}>피감독자 선택</option>
                    {employees
                      .filter(emp => emp.requires_supervision || emp.role === 'new_nurse')
                      .map(emp => (
                        <option key={emp.employee_id} value={emp.employee_id}>
                          {emp.employee_name} ({getRoleDisplayName(emp.role)})
                        </option>
                      ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>페어링 유형</label>
                  <select
                    value={pairForm.pairing_type}
                    onChange={(e) => setPairForm({ ...pairForm, pairing_type: e.target.value })}
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
                    value={pairForm.end_date}
                    onChange={(e) => setPairForm({ ...pairForm, end_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-actions">
                <button onClick={handleCreatePair} className="btn-primary" disabled={loading}>
                  {loading ? '생성 중...' : '생성'}
                </button>
                <button onClick={() => setShowPairForm(false)} className="btn-secondary">
                  취소
                </button>
              </div>
            </div>
          )}

          <div className="pairs-grid">
            {supervisionPairs.map((pair) => (
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
                      onClick={() => handleDeactivatePair(pair.id!)}
                      className="btn-danger"
                    >
                      비활성화
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 고용형태 규칙 탭 */}
      {activeTab === 'employment' && (
        <div className="employment-section">
          <div className="section-header">
            <h3>고용형태별 규칙 ({employmentRules.length}개)</h3>
            <button 
              onClick={() => setShowEmploymentForm(!showEmploymentForm)}
              className="btn-primary"
            >
              {showEmploymentForm ? '취소' : '새 규칙'}
            </button>
          </div>

          {showEmploymentForm && (
            <div className="employment-form">
              <h3>새 고용형태 규칙</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label>고용형태</label>
                  <select
                    value={employmentForm.employment_type}
                    onChange={(e) => setEmploymentForm({ 
                      ...employmentForm, 
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
                    value={employmentForm.max_hours_per_day}
                    onChange={(e) => setEmploymentForm({ 
                      ...employmentForm, 
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
                    value={employmentForm.max_hours_per_week}
                    onChange={(e) => setEmploymentForm({ 
                      ...employmentForm, 
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
                    value={employmentForm.max_days_per_week}
                    onChange={(e) => setEmploymentForm({ 
                      ...employmentForm, 
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
                    value={employmentForm.max_consecutive_days}
                    onChange={(e) => setEmploymentForm({ 
                      ...employmentForm, 
                      max_consecutive_days: parseInt(e.target.value) 
                    })}
                  />
                </div>

                <div className="form-group">
                  <label>허용 근무시간</label>
                  <input
                    type="text"
                    value={employmentForm.allowed_shift_types.join(', ')}
                    onChange={(e) => updateEmploymentArrayField('allowed_shift_types', e.target.value)}
                    placeholder="day, evening, night"
                  />
                </div>

                <div className="form-group">
                  <label>스케줄링 우선순위</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={employmentForm.scheduling_priority}
                    onChange={(e) => setEmploymentForm({ 
                      ...employmentForm, 
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
                    checked={employmentForm.weekend_work_allowed}
                    onChange={(e) => setEmploymentForm({ 
                      ...employmentForm, 
                      weekend_work_allowed: e.target.checked 
                    })}
                  />
                  주말 근무 허용
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={employmentForm.night_shift_allowed}
                    onChange={(e) => setEmploymentForm({ 
                      ...employmentForm, 
                      night_shift_allowed: e.target.checked 
                    })}
                  />
                  야간 근무 허용
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={employmentForm.holiday_work_allowed}
                    onChange={(e) => setEmploymentForm({ 
                      ...employmentForm, 
                      holiday_work_allowed: e.target.checked 
                    })}
                  />
                  휴일 근무 허용
                </label>
              </div>

              <div className="form-actions">
                <button onClick={handleCreateEmploymentRule} className="btn-primary" disabled={loading}>
                  {loading ? '생성 중...' : '생성'}
                </button>
                <button onClick={() => setShowEmploymentForm(false)} className="btn-secondary">
                  취소
                </button>
              </div>
            </div>
          )}

          <div className="employment-grid">
            {employmentRules.map((rule) => (
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
        </div>
      )}

      <style jsx>{`
        .role-management {
          padding: 20px;
          max-width: 1600px;
          margin: 0 auto;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .tabs {
          display: flex;
          gap: 10px;
          margin-bottom: 30px;
          border-bottom: 2px solid #e0e0e0;
        }

        .tabs button {
          padding: 12px 20px;
          border: none;
          background: transparent;
          border-bottom: 3px solid transparent;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.3s;
        }

        .tabs button.active {
          border-bottom-color: #3498db;
          color: #3498db;
          font-weight: 600;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .employees-grid,
        .constraints-grid,
        .pairs-grid,
        .employment-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 20px;
        }

        .employee-card,
        .constraint-card,
        .pair-card,
        .employment-card {
          background: white;
          border: 1px solid #e0e0e0;
          border-radius: 10px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .employee-header,
        .constraint-header,
        .pair-header,
        .employment-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 15px;
        }

        .employee-badges,
        .constraint-badge,
        .priority-badge {
          display: flex;
          gap: 5px;
        }

        .badge {
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .badge.role-head_nurse { background: #e74c3c; color: white; }
        .badge.role-charge_nurse { background: #e67e22; color: white; }
        .badge.role-staff_nurse { background: #3498db; color: white; }
        .badge.role-new_nurse { background: #2ecc71; color: white; }
        .badge.role-education_coordinator { background: #9b59b6; color: white; }

        .badge.employment-full_time { background: #34495e; color: white; }
        .badge.employment-part_time { background: #95a5a6; color: white; }

        .detail-row,
        .limit-item,
        .permission-item {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          padding-bottom: 4px;
          border-bottom: 1px solid #f0f0f0;
        }

        .employee-capabilities,
        .constraint-flags,
        .permission-flags {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin: 10px 0;
        }

        .capability,
        .flag {
          padding: 4px 8px;
          border-radius: 8px;
          font-size: 12px;
        }

        .capability { background: #d5f4e6; color: #27ae60; }
        .capability.warning { background: #ffeaa7; color: #e17055; }

        .flag.supervisor { background: #74b9ff; color: white; }
        .flag.charge { background: #fdcb6e; color: #2d3436; }
        .flag.allowed { background: #00cec9; color: white; }

        .employee-form,
        .constraint-form,
        .pair-form,
        .employment-form {
          background: #f8f9fa;
          padding: 25px;
          border-radius: 10px;
          margin-bottom: 30px;
        }

        .form-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .form-group.full-width {
          grid-column: 1 / -1;
        }

        .form-group label {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
          color: #555;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 5px;
          font-size: 14px;
        }

        .form-group small {
          color: #666;
          font-size: 12px;
        }

        .checkbox-section {
          display: flex;
          gap: 20px;
          margin: 15px 0;
        }

        .checkbox-section label {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
        }

        .form-actions {
          display: flex;
          gap: 10px;
          justify-content: flex-end;
        }

        .employee-actions,
        .pair-actions {
          margin-top: 15px;
        }

        .btn-primary,
        .btn-secondary,
        .btn-edit,
        .btn-danger {
          padding: 8px 16px;
          border: none;
          border-radius: 5px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.3s;
        }

        .btn-primary { background: #3498db; color: white; }
        .btn-secondary { background: #95a5a6; color: white; }
        .btn-edit { background: #f39c12; color: white; }
        .btn-danger { background: #e74c3c; color: white; }

        .btn-primary:hover { background: #2980b9; }
        .btn-secondary:hover { background: #7f8c8d; }
        .btn-edit:hover { background: #e67e22; }
        .btn-danger:hover { background: #c0392b; }

        .loading {
          text-align: center;
          padding: 20px;
          color: #666;
        }

        .status.active { color: #27ae60; font-weight: bold; }
        .status.inactive { color: #e74c3c; font-weight: bold; }

        .pair-members {
          margin: 15px 0;
        }

        .member {
          margin-bottom: 8px;
        }

        .member .role {
          color: #666;
          font-size: 12px;
        }

        .pair-dates {
          font-size: 12px;
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default RoleManagement;