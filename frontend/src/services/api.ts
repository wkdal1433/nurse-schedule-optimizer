import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 근무 규칙 관련 API
export interface ShiftRule {
  id?: number;
  ward_id?: number;
  rule_name: string;
  rule_type: 'hard' | 'soft';
  category: 'consecutive' | 'weekly' | 'legal' | 'pattern';
  max_consecutive_nights: number;
  max_consecutive_days: number;
  min_rest_days_per_week: number;
  max_hours_per_week: number;
  forbidden_patterns: string[];
  penalty_weight: number;
  is_active?: boolean;
}

export interface ComplianceReport {
  is_compliant: boolean;
  compliance_score: number;
  total_violations: number;
  violations_by_severity: Record<string, number>;
  violations: any[];
}

export const complianceAPI = {
  // 규칙 생성
  createRule: (rule: Omit<ShiftRule, 'id'>) =>
    api.post('/compliance/rules/', rule),
  
  // 규칙 목록 조회
  getRules: (wardId?: number, isActive: boolean = true) =>
    api.get<ShiftRule[]>('/compliance/rules/', { 
      params: { ward_id: wardId, is_active: isActive } 
    }),
  
  // 규칙 수정
  updateRule: (ruleId: number, rule: Partial<ShiftRule>) =>
    api.put(`/compliance/rules/${ruleId}`, rule),
  
  // 규칙 삭제
  deleteRule: (ruleId: number) =>
    api.delete(`/compliance/rules/${ruleId}`),
  
  // 스케줄 검증
  validateSchedule: (scheduleId: number) =>
    api.post<ComplianceReport>('/compliance/validate/', { schedule_id: scheduleId }),
  
  // 기본 규칙 생성
  createDefaultRules: (wardId: number) =>
    api.post(`/compliance/rules/default/${wardId}`),
  
  // 준수 리포트
  getComplianceReport: (wardId: number) =>
    api.get(`/compliance/report/${wardId}`),
  
  // 위반 사항 조회
  getViolations: (scheduleId: number) =>
    api.get(`/compliance/violations/${scheduleId}`),
};

// 선호도 관리 관련 API
export interface PreferenceTemplate {
  id?: number;
  employee_id: number;
  preferred_shifts: string[];
  avoided_shifts: string[];
  max_night_shifts_per_month: number;
  max_weekend_shifts_per_month: number;
  preferred_patterns: string[];
  avoided_patterns: string[];
  max_consecutive_days: number;
  min_days_off_after_nights: number;
  cannot_work_alone: boolean;
  needs_senior_support: boolean;
}

export interface ShiftRequest {
  id?: number;
  employee_id: number;
  employee_name?: string;
  start_date: string;
  end_date: string;
  request_type: 'vacation' | 'shift_preference' | 'avoid' | 'pattern_request';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  shift_type?: string;
  reason: string;
  medical_reason: boolean;
  is_recurring: boolean;
  recurrence_pattern?: any;
  flexibility_level: number;
  alternative_acceptable: boolean;
  status?: string;
  admin_notes?: string;
  created_at?: string;
  reviewed_at?: string;
}

export const preferencesAPI = {
  // 선호도 템플릿 관리
  createPreferences: (employeeId: number, preferences: Omit<PreferenceTemplate, 'id' | 'employee_id'>) =>
    api.post(`/preferences/preferences/${employeeId}`, preferences),
  
  getPreferences: (employeeId: number) =>
    api.get<PreferenceTemplate>(`/preferences/preferences/${employeeId}`),
  
  // 요청 관리
  submitRequest: (employeeId: number, request: Omit<ShiftRequest, 'id' | 'employee_id'>) =>
    api.post(`/preferences/requests/${employeeId}`, request),
  
  getPendingRequests: (wardId?: number) =>
    api.get<ShiftRequest[]>('/preferences/requests/pending', { 
      params: wardId ? { ward_id: wardId } : {} 
    }),
  
  getEmployeeRequests: (employeeId: number, status?: string) =>
    api.get<ShiftRequest[]>(`/preferences/requests/employee/${employeeId}`, {
      params: status ? { status } : {}
    }),
  
  reviewRequest: (requestId: number, reviewerId: number, status: string, adminNotes: string = '') =>
    api.put(`/preferences/requests/${requestId}/review`, {
      status,
      admin_notes: adminNotes
    }, {
      params: { reviewer_id: reviewerId }
    }),
  
  // 대시보드 및 통계
  getDashboard: (wardId: number) =>
    api.get(`/preferences/dashboard/${wardId}`),
  
  getFairnessAnalysis: (scheduleId: number) =>
    api.get(`/preferences/fairness/${scheduleId}`),
  
  getRequestStatistics: (wardId?: number, startDate?: string, endDate?: string) =>
    api.get('/preferences/statistics/requests', {
      params: { ward_id: wardId, start_date: startDate, end_date: endDate }
    }),
  
  // 기본 템플릿
  getDefaultTemplate: () =>
    api.get<PreferenceTemplate>('/preferences/templates/defaults'),
  
  // 일괄 처리
  createBulkPreferences: (preferencesData: any[]) =>
    api.post('/preferences/preferences/bulk', preferencesData),
};

// 역할 관리 관련 API
export interface EmployeeRoleInfo {
  employee_id: number;
  employee_name: string;
  role: string;
  employment_type: string;
  allowed_shifts?: string[];
  max_hours_per_week: number;
  max_days_per_week: number;
  can_work_alone: boolean;
  requires_supervision: boolean;
  can_supervise: boolean;
  specialization?: string;
  years_experience: number;
  skill_level: number;
}

export interface RoleConstraint {
  id?: number;
  role: string;
  ward_id?: number;
  allowed_shifts: string[];
  forbidden_shifts: string[];
  min_per_shift: number;
  max_per_shift: number;
  requires_pairing_with_roles: string[];
  cannot_work_with_roles: string[];
  must_have_supervisor: boolean;
  can_be_sole_charge: boolean;
}

export interface SupervisionPair {
  id?: number;
  supervisor: {
    id: number;
    name: string;
    role: string;
  };
  supervisee: {
    id: number;
    name: string;
    role: string;
  };
  pairing_type: string;
  is_mandatory: boolean;
  start_date: string;
  end_date?: string;
  is_active: boolean;
}

export interface EmploymentTypeRule {
  id?: number;
  employment_type: string;
  ward_id?: number;
  max_hours_per_day: number;
  max_hours_per_week: number;
  max_days_per_week: number;
  max_consecutive_days: number;
  allowed_shift_types: string[];
  forbidden_shift_types: string[];
  weekend_work_allowed: boolean;
  night_shift_allowed: boolean;
  holiday_work_allowed: boolean;
  scheduling_priority: number;
}

export const rolesAPI = {
  // 직원 역할 관리
  updateEmployeeRole: (employeeId: number, roleData: Partial<EmployeeRoleInfo>) =>
    api.put(`/roles/employees/${employeeId}/role`, roleData),
  
  getEmployeeRoleInfo: (employeeId: number) =>
    api.get<EmployeeRoleInfo>(`/roles/employees/${employeeId}/role`),
  
  getEmployeesByWard: (wardId: number, role?: string, employmentType?: string) =>
    api.get<EmployeeRoleInfo[]>(`/roles/employees/by-ward/${wardId}`, {
      params: { role, employment_type: employmentType }
    }),
  
  // 역할별 제약조건 관리
  createRoleConstraint: (constraint: Omit<RoleConstraint, 'id'>) =>
    api.post('/roles/constraints/', constraint),
  
  getRoleConstraints: (wardId?: number, role?: string) =>
    api.get<RoleConstraint[]>('/roles/constraints/', {
      params: { ward_id: wardId, role }
    }),
  
  // 감독 페어 관리
  createSupervisionPair: (pairData: {
    supervisor_id: number;
    supervisee_id: number;
    pairing_type?: string;
    end_date?: string;
  }) =>
    api.post('/roles/supervision-pairs/', pairData),
  
  getSupervisionPairs: (wardId?: number, activeOnly: boolean = true) =>
    api.get<SupervisionPair[]>('/roles/supervision-pairs/', {
      params: { ward_id: wardId, active_only: activeOnly }
    }),
  
  deactivateSupervisionPair: (pairId: number) =>
    api.delete(`/roles/supervision-pairs/${pairId}`),
  
  // 고용형태별 규칙 관리
  createEmploymentTypeRule: (rule: Omit<EmploymentTypeRule, 'id'>) =>
    api.post('/roles/employment-rules/', rule),
  
  getEmploymentTypeRules: (employmentType?: string, wardId?: number) =>
    api.get<EmploymentTypeRule[]>('/roles/employment-rules/', {
      params: { employment_type: employmentType, ward_id: wardId }
    }),
  
  // 역할 배치 검증
  validateRoleAssignments: (scheduleId: number) =>
    api.post('/roles/validate/', { schedule_id: scheduleId }),
  
  getRoleAssignmentSummary: (scheduleId: number) =>
    api.get(`/roles/summary/${scheduleId}`),
  
  // 기본 설정 생성
  createDefaultRoleSettings: (wardId: number) =>
    api.post(`/roles/defaults/${wardId}`)
};

// 패턴 검증 관련 API
export interface ShiftPattern {
  id?: number;
  pattern_name: string;
  pattern_type: 'forbidden' | 'discouraged' | 'preferred';
  description?: string;
  sequence_length: number;
  pattern_definition: any;
  penalty_score: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  ward_id?: number;
  role_specific?: string[];
  is_active?: boolean;
}

export interface PatternViolation {
  id: number;
  employee_id: number;
  pattern_name: string;
  violation_date_start: string;
  violation_date_end: string;
  violation_sequence: string[];
  description: string;
  severity: string;
  penalty_score: number;
  is_resolved: boolean;
  resolution_method?: string;
}

export interface PatternValidationResult {
  employee_id: number;
  is_valid: boolean;
  total_penalty: number;
  violations: any[];
  pattern_score: number;
  recommendations: string[];
  overall_score: number;
  total_violations: number;
  summary: string;
}

export interface FatigueAnalysis {
  employee_id: number;
  total_fatigue_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  recommendations: string[];
  rest_days_needed: number;
}

export const patternsAPI = {
  // 패턴 규칙 관리
  createPattern: (pattern: Omit<ShiftPattern, 'id'>) =>
    api.post('/patterns/', pattern),
  
  getPatterns: (wardId?: number, patternType?: string, isActive: boolean = true) =>
    api.get<ShiftPattern[]>('/patterns/', { 
      params: { ward_id: wardId, pattern_type: patternType, is_active: isActive } 
    }),
  
  updatePattern: (patternId: number, pattern: Partial<ShiftPattern>) =>
    api.put(`/patterns/${patternId}`, pattern),
  
  deletePattern: (patternId: number) =>
    api.delete(`/patterns/${patternId}`),
  
  // 패턴 검증
  validateEmployeePattern: (employeeId: number, assignments: any[], periodStart: string, periodEnd: string) =>
    api.post<PatternValidationResult>('/patterns/validate/employee', {
      employee_id: employeeId,
      assignments,
      period_start: periodStart,
      period_end: periodEnd
    }),
  
  validateSchedulePatterns: (scheduleId: number) =>
    api.post('/patterns/validate/schedule/' + scheduleId),
  
  // 위반사항 관리
  getPatternViolations: (scheduleId: number, resolved?: boolean, severity?: string) =>
    api.get(`/patterns/violations/schedule/${scheduleId}`, {
      params: { resolved, severity }
    }),
  
  resolveViolation: (violationId: number, resolutionMethod: string, notes?: string, resolverId?: number) =>
    api.post(`/patterns/violations/${violationId}/resolve`, {
      resolution_method: resolutionMethod,
      resolution_notes: notes,
      resolver_id: resolverId
    }),
  
  // 피로도 분석
  analyzeFatigue: (employeeId: number, periodStart: string, periodEnd: string) =>
    api.post<FatigueAnalysis>('/patterns/fatigue/analyze', {
      employee_id: employeeId,
      period_start: periodStart,
      period_end: periodEnd
    }),
  
  // 통계
  getPatternStatistics: (wardId: number, periodStart: string, periodEnd: string) =>
    api.get(`/patterns/statistics/ward/${wardId}`, {
      params: { period_start: periodStart, period_end: periodEnd }
    }),
  
  // 권장사항
  getPatternRecommendations: (scheduleId: number, priority?: string, status?: string) =>
    api.get(`/patterns/recommendations/schedule/${scheduleId}`, {
      params: { priority, status }
    }),
  
  // 기본 패턴 생성
  createDefaultPatterns: (wardId: number) =>
    api.post(`/patterns/defaults/ward/${wardId}`)
};

// 수동 편집 및 응급 오버라이드 관련 API
export interface Schedule {
  id: number;
  ward_id: number;
  schedule_name: string;
  period_start: string;
  period_end: string;
  status: 'draft' | 'active' | 'archived';
  optimization_score: number;
  compliance_score?: number;
  pattern_score?: number;
  preference_score?: number;
}

export interface ShiftAssignment {
  id: number;
  schedule_id: number;
  employee_id: number;
  employee_name?: string;
  shift_date: string;
  shift_type: string;
  is_manual_assignment: boolean;
  is_override: boolean;
  override_reason?: string;
}

export interface ValidationResult {
  valid: boolean;
  warnings: any[];
  errors: any[];
  pattern_score: number;
  recommendations: string[];
}

export interface ReplacementSuggestion {
  employee_id: number;
  employee_name: string;
  role: string;
  employment_type: string;
  skill_level: number;
  years_experience: number;
  suitability_score: number;
  suitability_reasons: string[];
  warnings: string[];
  availability_status: string;
}

export interface EmergencyLog {
  id: number;
  assignment_id: number;
  emergency_type: string;
  urgency_level: string;
  original_employee_id: number;
  replacement_employee_id?: number;
  reason: string;
  admin_id: number;
  status: string;
  created_at: string;
  resolution_time?: string;
}

export const manualEditingAPI = {
  // 근무 변경 검증 및 적용
  validateChange: (data: {
    assignment_id: number;
    new_employee_id?: number;
    new_shift_type?: string;
    new_shift_date?: string;
  }) =>
    api.post<ValidationResult>('/manual-editing/validate-change', data),

  applyChange: (data: {
    assignment_id: number;
    new_employee_id?: number;
    new_shift_type?: string;
    new_shift_date?: string;
    override?: boolean;
    override_reason?: string;
    admin_id?: number;
  }) =>
    api.post('/manual-editing/apply-change', data),

  // 대체자 추천
  getReplacementSuggestions: (assignmentId: number, emergency: boolean = false, maxSuggestions: number = 5) =>
    api.get<ReplacementSuggestion[]>(`/manual-editing/suggestions/${assignmentId}`, {
      params: { emergency, max_suggestions: maxSuggestions }
    }),

  // 응급 재배치
  emergencyReassignment: (data: {
    assignment_id: number;
    replacement_employee_id: number;
    emergency_reason: string;
    admin_id: number;
    notify_affected?: boolean;
  }) =>
    api.post('/manual-editing/emergency-reassignment', data),

  // 일괄 근무 교환
  bulkSwap: (data: {
    swap_pairs: Array<[number, number]>;
    admin_id: number;
    validation_level?: 'strict' | 'standard' | 'minimal';
  }) =>
    api.post('/manual-editing/bulk-swap', data),

  // 스케줄 관리
  getSchedules: (wardId?: number, status?: string, limit: number = 10) =>
    api.get<Schedule[]>('/manual-editing/schedules/', {
      params: { ward_id: wardId, status, limit }
    }),

  createSchedule: (data: {
    ward_id: number;
    schedule_name: string;
    period_start: string;
    period_end: string;
    admin_id: number;
  }) =>
    api.post<Schedule>('/manual-editing/schedules/', null, { params: data }),

  updateSchedule: (scheduleId: number, data: {
    schedule_name?: string;
    status?: string;
    admin_id?: number;
  }) =>
    api.put(`/manual-editing/schedules/${scheduleId}`, null, { params: data }),

  // 근무 배정 관리
  getScheduleAssignments: (scheduleId: number, filters?: {
    employee_id?: number;
    shift_type?: string;
    date_from?: string;
    date_to?: string;
  }) =>
    api.get<ShiftAssignment[]>(`/manual-editing/schedules/${scheduleId}/assignments`, {
      params: filters
    }),

  createAssignment: (data: {
    schedule_id: number;
    employee_id: number;
    shift_date: string;
    shift_type: string;
    admin_id: number;
    override?: boolean;
    override_reason?: string;
    notes?: string;
  }) =>
    api.post('/manual-editing/assignments/create', data),

  deleteAssignment: (assignmentId: number, adminId: number, reason?: string) =>
    api.delete(`/manual-editing/assignments/${assignmentId}`, {
      params: { admin_id: adminId, reason }
    }),

  // 스케줄 점수
  getScheduleScore: (scheduleId: number, recalculate: boolean = false) =>
    api.get(`/manual-editing/schedules/${scheduleId}/score`, {
      params: { recalculate }
    }),

  // 응급 로그
  getEmergencyLogs: (filters?: {
    assignment_id?: number;
    admin_id?: number;
    status?: string;
    limit?: number;
  }) =>
    api.get('/manual-editing/emergency-logs/', { params: filters })
};

export default api;