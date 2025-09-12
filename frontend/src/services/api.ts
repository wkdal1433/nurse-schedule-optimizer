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

export default api;