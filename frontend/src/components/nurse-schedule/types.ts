/**
 * 간호사 스케줄링 관련 타입 정의
 * Single Responsibility: 타입 정의만 담당
 */

export interface Nurse {
  id: number;
  name: string;
  role: 'head_nurse' | 'staff_nurse' | 'new_nurse';
  employment_type: 'full_time' | 'part_time';
  experience_level: number;
}

export interface Ward {
  id: number;
  name: string;
  min_nurses_per_shift: number;
  shift_types: string[];
}

export interface ScheduleData {
  date: string;
  nurses: {
    [nurseId: number]: {
      shift: 'DAY' | 'EVENING' | 'NIGHT' | 'OFF';
      nurse: Nurse;
    };
  };
}

export type ViewType = 'setup' | 'calendar' | 'settings';

export interface AppState {
  currentView: ViewType;
  nurses: Nurse[];
  selectedWard: Ward | null;
  scheduleData: ScheduleData[];
  selectedDate: Date;
  isLoading: boolean;
  showPreCheckDialog: boolean;
  pendingScheduleGeneration: boolean;
  showPersonalSchedule: boolean;
  selectedNurse: Nurse | null;
  nurseFilter: number | null;
  showNotifications: boolean;
}

export interface NurseFormData {
  name: string;
  role: Nurse['role'];
  employment_type: Nurse['employment_type'];
  experience: number;
}

export interface PreCheckResult {
  canGenerate: boolean;
  missingRequirements: string[];
  recommendations: string[];
}

export interface ScheduleGenerationRequest {
  ward_id: number;
  nurses: Nurse[];
  start_date: string;
  end_date: string;
  constraints?: {
    min_rest_days?: number;
    max_consecutive_shifts?: number;
    preferred_patterns?: any[];
  };
}

export interface ScheduleGenerationResponse {
  success: boolean;
  schedule?: ScheduleData[];
  message?: string;
  optimization_score?: number;
}