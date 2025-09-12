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

export default api;