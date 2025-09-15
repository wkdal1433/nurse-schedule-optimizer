// 공통 타입 정의
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
export type ShiftType = 'DAY' | 'EVENING' | 'NIGHT' | 'OFF';