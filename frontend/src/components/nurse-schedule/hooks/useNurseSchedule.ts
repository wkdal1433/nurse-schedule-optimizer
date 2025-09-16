/**
 * 간호사 스케줄링 비즈니스 로직 훅
 * Single Responsibility: 스케줄링 상태 관리 및 비즈니스 로직만 담당
 */

import { useState, useCallback, useMemo } from 'react';
import {
  Nurse,
  Ward,
  ScheduleData,
  AppState,
  ViewType,
  PreCheckResult,
  ScheduleGenerationRequest,
  ScheduleGenerationResponse
} from '../types';

export const useNurseSchedule = () => {
  // State 관리
  const [state, setState] = useState<AppState>({
    currentView: 'setup',
    nurses: [],
    selectedWard: null,
    scheduleData: [],
    selectedDate: new Date(),
    isLoading: false,
    showPreCheckDialog: false,
    pendingScheduleGeneration: false,
    showPersonalSchedule: false,
    selectedNurse: null,
    nurseFilter: null,
    showNotifications: false,
  });

  // 병동 데이터 (실제로는 백엔드에서 가져올 것)
  const wards: Ward[] = useMemo(() => [
    { id: 1, name: '내과 병동', min_nurses_per_shift: 3, shift_types: ['DAY', 'EVENING', 'NIGHT'] },
    { id: 2, name: '외과 병동', min_nurses_per_shift: 4, shift_types: ['DAY', 'EVENING', 'NIGHT'] },
    { id: 3, name: '중환자실', min_nurses_per_shift: 2, shift_types: ['DAY', 'NIGHT'] },
    { id: 4, name: '응급실', min_nurses_per_shift: 5, shift_types: ['DAY', 'EVENING', 'NIGHT'] }
  ], []);

  // 상태 업데이트 헬퍼 함수
  const updateState = useCallback((updates: Partial<AppState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // View 변경
  const setCurrentView = useCallback((view: ViewType) => {
    updateState({ currentView: view });
  }, [updateState]);

  // 간호사 관리
  const addNurse = useCallback((
    name: string,
    role: Nurse['role'],
    employment_type: Nurse['employment_type'],
    experience: number
  ) => {
    const newNurse: Nurse = {
      id: Date.now(),
      name,
      role,
      employment_type,
      experience_level: experience
    };

    setState(prev => ({
      ...prev,
      nurses: [...prev.nurses, newNurse]
    }));
  }, []);

  const removeNurse = useCallback((nurseId: number) => {
    setState(prev => ({
      ...prev,
      nurses: prev.nurses.filter(nurse => nurse.id !== nurseId)
    }));
  }, []);

  // 병동 선택
  const selectWard = useCallback((ward: Ward) => {
    updateState({ selectedWard: ward });
  }, [updateState]);

  // 최저 인원 충족 여부 확인
  const checkMinStaffRequirement = useCallback((): boolean => {
    if (!state.selectedWard) return false;

    const requiredNurses = state.selectedWard.min_nurses_per_shift * state.selectedWard.shift_types.length;
    const result = state.nurses.length >= requiredNurses;

    console.log(`최저 인원 체크: 필요=${requiredNurses}, 현재=${state.nurses.length}, 충족=${result}`);
    return result;
  }, [state.selectedWard, state.nurses.length]);

  // 근무표 생성 가능 여부 확인
  const canGenerateSchedule = useCallback((): boolean => {
    const hasWard = !!state.selectedWard;
    const hasNurses = state.nurses.length > 0;
    const hasMinStaff = checkMinStaffRequirement();
    const notLoading = !state.isLoading;
    const result = hasWard && hasNurses && hasMinStaff && notLoading;

    console.log(`생성 가능 체크: 병동=${hasWard}, 간호사=${hasNurses}, 최소인원=${hasMinStaff}, 로딩중아님=${notLoading}, 결과=${result}`);
    return result;
  }, [state.selectedWard, state.nurses.length, state.isLoading, checkMinStaffRequirement]);

  // Pre-check 실행
  const performPreCheck = useCallback((): PreCheckResult => {
    const missingRequirements: string[] = [];
    const recommendations: string[] = [];

    if (!state.selectedWard) {
      missingRequirements.push('병동 선택이 필요합니다');
    }

    if (state.nurses.length === 0) {
      missingRequirements.push('간호사 등록이 필요합니다');
    }

    if (state.selectedWard && !checkMinStaffRequirement()) {
      const requiredNurses = state.selectedWard.min_nurses_per_shift * state.selectedWard.shift_types.length;
      missingRequirements.push(`최소 ${requiredNurses}명의 간호사가 필요합니다 (현재: ${state.nurses.length}명)`);
    }

    // 추천사항 생성
    if (state.selectedWard) {
      const headNurses = state.nurses.filter(n => n.role === 'head_nurse').length;
      const staffNurses = state.nurses.filter(n => n.role === 'staff_nurse').length;
      const newNurses = state.nurses.filter(n => n.role === 'new_nurse').length;

      if (headNurses === 0 && state.nurses.length > 5) {
        recommendations.push('수간호사 1명 이상 등록을 권장합니다');
      }

      if (newNurses > staffNurses && staffNurses < 2) {
        recommendations.push('신입간호사 대비 경력간호사 비율을 조정하는 것을 권장합니다');
      }

      const fullTimeNurses = state.nurses.filter(n => n.employment_type === 'full_time').length;
      if (fullTimeNurses < state.selectedWard.min_nurses_per_shift * 2) {
        recommendations.push('안정적인 스케줄링을 위해 정규직 간호사 비율을 늘리는 것을 권장합니다');
      }
    }

    return {
      canGenerate: missingRequirements.length === 0,
      missingRequirements,
      recommendations
    };
  }, [state.selectedWard, state.nurses, checkMinStaffRequirement]);

  // 스케줄 생성
  const generateSchedule = useCallback(async (): Promise<ScheduleGenerationResponse> => {
    if (!state.selectedWard) {
      return { success: false, message: '병동을 선택해주세요' };
    }

    updateState({ isLoading: true });

    try {
      const startDate = new Date();
      const endDate = new Date();
      endDate.setMonth(endDate.getMonth() + 1);

      const request: ScheduleGenerationRequest = {
        ward_id: state.selectedWard.id,
        nurses: state.nurses,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        constraints: {
          min_rest_days: 2,
          max_consecutive_shifts: 5,
          preferred_patterns: []
        }
      };

      const response = await fetch('/api/generate-schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      });

      const result: ScheduleGenerationResponse = await response.json();

      if (result.success && result.schedule) {
        updateState({
          scheduleData: result.schedule,
          currentView: 'calendar'
        });
      }

      return result;

    } catch (error) {
      console.error('스케줄 생성 중 오류:', error);
      return {
        success: false,
        message: '스케줄 생성 중 오류가 발생했습니다'
      };
    } finally {
      updateState({ isLoading: false });
    }
  }, [state.selectedWard, state.nurses, updateState]);

  // 스케줄 데이터 필터링
  const filterScheduleDataByNurse = useCallback((
    scheduleData: ScheduleData[],
    nurseId: number
  ): ScheduleData[] => {
    return scheduleData.map(dayData => ({
      ...dayData,
      nurses: Object.keys(dayData.nurses).reduce((acc, key) => {
        const nurseKey = parseInt(key);
        if (nurseKey === nurseId) {
          acc[nurseKey] = dayData.nurses[nurseKey];
        }
        return acc;
      }, {} as typeof dayData.nurses)
    }));
  }, []);

  // 날짜 관리
  const setSelectedDate = useCallback((date: Date) => {
    updateState({ selectedDate: date });
  }, [updateState]);

  // 날짜 네비게이션
  const navigateDate = useCallback((direction: 'prev' | 'next') => {
    setState(prev => {
      const newDate = new Date(prev.selectedDate);
      if (direction === 'prev') {
        newDate.setMonth(newDate.getMonth() - 1);
      } else {
        newDate.setMonth(newDate.getMonth() + 1);
      }
      return { ...prev, selectedDate: newDate };
    });
  }, []);

  // Pre-check 다이얼로그 열기
  const openPreCheckDialog = useCallback(() => {
    if (!state.selectedWard) {
      alert('병동을 먼저 선택해주세요.');
      return;
    }
    if (state.nurses.length === 0) {
      alert('간호사를 먼저 등록해주세요.');
      return;
    }
    if (!checkMinStaffRequirement()) {
      const requiredNurses = state.selectedWard!.min_nurses_per_shift * state.selectedWard!.shift_types.length;
      alert(`최소 ${requiredNurses}명의 간호사가 필요합니다. (현재: ${state.nurses.length}명)`);
      return;
    }

    updateState({ showPreCheckDialog: true });
  }, [state.selectedWard, state.nurses.length, checkMinStaffRequirement, updateState]);

  // Pre-check 다이얼로그 닫기
  const closePreCheckDialog = useCallback(() => {
    updateState({ showPreCheckDialog: false });
  }, [updateState]);

  // 개인 스케줄 보기
  const showPersonalScheduleAction = useCallback((nurse: Nurse) => {
    updateState({
      selectedNurse: nurse,
      showPersonalSchedule: true
    });
  }, [updateState]);

  // 개인 스케줄 닫기
  const closePersonalSchedule = useCallback(() => {
    updateState({
      showPersonalSchedule: false,
      selectedNurse: null
    });
  }, [updateState]);

  // 간호사 필터 설정
  const setNurseFilter = useCallback((nurseId: number | null) => {
    updateState({ nurseFilter: nurseId });
  }, [updateState]);

  // 알림 토글
  const toggleNotifications = useCallback(() => {
    updateState({ showNotifications: !state.showNotifications });
  }, [state.showNotifications, updateState]);

  return {
    // State
    ...state,
    wards,

    // Actions
    setCurrentView,
    addNurse,
    removeNurse,
    selectWard,
    checkMinStaffRequirement,
    canGenerateSchedule,
    performPreCheck,
    generateSchedule,
    filterScheduleDataByNurse,
    navigateDate,
    openPreCheckDialog,
    closePreCheckDialog,
    showPersonalScheduleAction,
    closePersonalSchedule,
    setNurseFilter,
    setSelectedDate,
    toggleNotifications
  };
};